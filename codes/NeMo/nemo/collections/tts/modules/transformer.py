# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from typing import Optional

import torch
import torch.nn as nn
import torch.nn.functional as F

from nemo.collections.tts.modules.submodules import LinearNorm
from nemo.collections.tts.parts.utils.helpers import get_mask_from_lengths
from nemo.core.classes import NeuralModule, typecheck
from nemo.core.neural_types.elements import EncodedRepresentation, LengthsType, MaskType, TokenIndex, VoidType
from nemo.core.neural_types.neural_type import NeuralType


def mask_from_lens(lens, max_len: Optional[int] = None):
    if max_len is None:
        max_len = lens.max()
    ids = torch.arange(0, max_len, device=lens.device, dtype=lens.dtype)
    mask = torch.lt(ids, lens.unsqueeze(1))
    return mask


class PositionalEmbedding(nn.Module):
    def __init__(self, demb):
        super(PositionalEmbedding, self).__init__()
        self.demb = demb
        inv_freq = 1 / (10000 ** (torch.arange(0.0, demb, 2.0) / demb))
        self.register_buffer('inv_freq', inv_freq)

    def forward(self, pos_seq, bsz=None):
        #        sinusoid_inp = torch.ger(pos_seq, self.inv_freq)
        sinusoid_inp = torch.matmul(torch.unsqueeze(pos_seq, -1), torch.unsqueeze(self.inv_freq, 0))

        pos_emb = torch.cat([sinusoid_inp.sin(), sinusoid_inp.cos()], dim=1)
        if bsz is not None:
            return pos_emb[None, :, :].repeat(bsz, 1, 1)
        else:
            return pos_emb[None, :, :]


class PositionwiseConvFF(nn.Module):
    def __init__(self, d_model, d_inner, kernel_size, dropout, pre_lnorm=False):
        super(PositionwiseConvFF, self).__init__()

        self.d_model = d_model
        self.d_inner = d_inner
        self.dropout = dropout

        if type(kernel_size) is not tuple:
            kernel_size = (kernel_size, kernel_size)

        self.CoreNet = nn.Sequential(
            nn.Conv1d(d_model, d_inner, kernel_size[0], 1, (kernel_size[0] // 2)),
            nn.ReLU(),
            # nn.Dropout(dropout),  # worse convergence
            nn.Conv1d(d_inner, d_model, kernel_size[1], 1, (kernel_size[1] // 2)),
            nn.Dropout(dropout),
        )
        self.layer_norm = nn.LayerNorm(d_model)
        self.pre_lnorm = pre_lnorm

    def forward(self, inp):
        return self._forward(inp)

    def _forward(self, inp):
        if self.pre_lnorm:
            # layer normalization + positionwise feed-forward
            core_out = inp.transpose(1, 2)
            core_out = self.CoreNet(self.layer_norm(core_out).to(inp.dtype))
            core_out = core_out.transpose(1, 2)

            # residual connection
            output = core_out + inp
        else:
            # positionwise feed-forward
            core_out = inp.transpose(1, 2)
            core_out = self.CoreNet(core_out)
            core_out = core_out.transpose(1, 2)

            # residual connection + layer normalization
            output = self.layer_norm(inp + core_out).to(inp.dtype)

        return output


class MultiHeadAttn(nn.Module):
    def __init__(self, n_head, d_model, d_head, dropout, dropatt=0.1, pre_lnorm=False):
        super(MultiHeadAttn, self).__init__()

        self.n_head = n_head
        self.d_model = d_model
        self.d_head = d_head
        self.scale = 1 / (d_head ** 0.5)
        self.pre_lnorm = pre_lnorm

        self.qkv_net = nn.Linear(d_model, 3 * n_head * d_head)
        self.drop = nn.Dropout(dropout)
        self.dropatt = nn.Dropout(dropatt)
        self.o_net = nn.Linear(n_head * d_head, d_model, bias=False)
        self.layer_norm = nn.LayerNorm(d_model)

    def forward(self, inp, attn_mask=None):
        return self._forward(inp, attn_mask)

    def _forward(self, inp, attn_mask=None):
        residual = inp

        if self.pre_lnorm:
            # layer normalization
            inp = self.layer_norm(inp)

        n_head, d_head = self.n_head, self.d_head

        head_q, head_k, head_v = torch.chunk(self.qkv_net(inp), 3, dim=2)

        head_q = head_q.view(inp.size(0), inp.size(1), n_head, d_head)
        head_k = head_k.view(inp.size(0), inp.size(1), n_head, d_head)
        head_v = head_v.view(inp.size(0), inp.size(1), n_head, d_head)

        q = head_q.permute(2, 0, 1, 3).reshape(-1, inp.size(1), d_head)
        k = head_k.permute(2, 0, 1, 3).reshape(-1, inp.size(1), d_head)
        v = head_v.permute(2, 0, 1, 3).reshape(-1, inp.size(1), d_head)

        attn_score = torch.bmm(q, k.transpose(1, 2))
        attn_score.mul_(self.scale)

        if attn_mask is not None:
            attn_mask = attn_mask.unsqueeze(1).to(attn_score.dtype)
            attn_mask = attn_mask.repeat(n_head, attn_mask.size(2), 1)
            attn_score.masked_fill_(attn_mask.to(torch.bool), -float('inf'))

        attn_prob = F.softmax(attn_score, dim=2)
        attn_prob = self.dropatt(attn_prob)
        attn_vec = torch.bmm(attn_prob, v)

        attn_vec = attn_vec.view(n_head, inp.size(0), inp.size(1), d_head)
        attn_vec = attn_vec.permute(1, 2, 0, 3).contiguous().view(inp.size(0), inp.size(1), n_head * d_head)

        # linear projection
        attn_out = self.o_net(attn_vec)
        attn_out = self.drop(attn_out)

        if self.pre_lnorm:
            # residual connection
            output = residual + attn_out
        else:
            # residual connection + layer normalization
            output = self.layer_norm(residual + attn_out)

        return output


class TransformerLayer(nn.Module):
    def __init__(self, n_head, d_model, d_head, d_inner, kernel_size, dropout, **kwargs):
        super(TransformerLayer, self).__init__()

        self.dec_attn = MultiHeadAttn(n_head, d_model, d_head, dropout, **kwargs)
        self.pos_ff = PositionwiseConvFF(d_model, d_inner, kernel_size, dropout, pre_lnorm=kwargs.get('pre_lnorm'))

    def forward(self, dec_inp, mask=None):
        output = self.dec_attn(dec_inp, attn_mask=~mask.squeeze(2))
        output *= mask
        output = self.pos_ff(output)
        output *= mask
        return output


class FFTransformerDecoder(NeuralModule):
    def __init__(
        self, n_layer, n_head, d_model, d_head, d_inner, kernel_size, dropout, dropatt, dropemb=0.0, pre_lnorm=False
    ):
        super(FFTransformerDecoder, self).__init__()
        self.d_model = d_model
        self.n_head = n_head
        self.d_head = d_head

        self.pos_emb = PositionalEmbedding(self.d_model)
        self.drop = nn.Dropout(dropemb)
        self.layers = nn.ModuleList()

        for _ in range(n_layer):
            self.layers.append(
                TransformerLayer(
                    n_head, d_model, d_head, d_inner, kernel_size, dropout, dropatt=dropatt, pre_lnorm=pre_lnorm
                )
            )

    @property
    def input_types(self):
        return {
            "input": NeuralType(('B', 'T', 'D'), EncodedRepresentation()),
            "seq_lens": NeuralType(('B'), LengthsType()),
            "conditioning": NeuralType(('B', 'T', 'D'), EncodedRepresentation(), optional=True),
        }

    @property
    def output_types(self):
        return {
            "out": NeuralType(('B', 'T', 'D'), EncodedRepresentation()),
            "mask": NeuralType(('B', 'T', 'D'), MaskType()),
        }

    @typecheck()
    def forward(self, input, seq_lens, conditioning=0):
        return self._forward(input, mask_from_lens(seq_lens).unsqueeze(2), conditioning)

    def _forward(self, inp, mask, conditioning):
        pos_seq = torch.arange(inp.size(1), device=inp.device).to(inp.dtype)
        pos_emb = self.pos_emb(pos_seq) * mask
        out = self.drop(inp + pos_emb + conditioning)

        for layer in self.layers:
            out = layer(out, mask=mask)

        # out = self.drop(out)
        return out, mask


class FFTransformerEncoder(FFTransformerDecoder):
    def __init__(
        self,
        n_layer,
        n_head,
        d_model,
        d_head,
        d_inner,
        kernel_size,
        dropout,
        dropatt,
        dropemb=0.0,
        pre_lnorm=False,
        n_embed=None,
        d_embed=None,
        padding_idx=0,
        bert_feats=0
    ):
        super(FFTransformerEncoder, self).__init__(
            n_layer, n_head, d_model, d_head, d_inner, kernel_size, dropout, dropatt, dropemb, pre_lnorm
        )

        self.padding_idx = padding_idx
        self.word_emb = nn.Embedding(n_embed, d_embed or d_model, padding_idx=self.padding_idx)
        
        self.bert_layer = None
        if bert_feats > 0:
            self.bert_layer = nn.Sequential(
            nn.Conv1d(bert_feats, 512, 3, padding=1), nn.GELU(),
            nn.Conv1d(512, 512, 3, padding=1), nn.GELU(),
            nn.Conv1d(512, d_embed or d_model, 1)
        )

    @property
    def input_types(self):
        return {
            "input": NeuralType(('B', 'T'), TokenIndex()),
            "phoneme_length_sequences": NeuralType(('B', 'T'), VoidType(), optional=True),
            "emotions": NeuralType(('B', 'D'), EncodedRepresentation(), optional=True),
            "bert_feats": NeuralType(('B', 'D', 'T'), EncodedRepresentation(), optional=True),
            "conditioning": NeuralType(('B', 'T', 'D'), EncodedRepresentation(), optional=True),
        }

    def forward(self, input, phoneme_length_sequences=None, emotions=None, bert_feats=None, conditioning=0):
        x = self.word_emb(input)
        device = input.device

        #phoneme-length-regulator
        
        if phoneme_length_sequences is not None:
            # 计算最终的聚合嵌入序列
            assert x.shape[1] == phoneme_length_sequences.shape[1], "X 和 L 的长度必须匹配"
            # 初始化结果列表
            c_tau = torch.cat([torch.zeros((x.shape[0],1)).to(device), torch.cumsum(phoneme_length_sequences, dim=0)],dim=1)
            Y = torch.zeros_like(x).to(device)  # shape: [9, 91, 384]
            # 遍历每个样本
            for i in range(x.shape[0]):  # x.shape[0] == 9
                # 当前样本的特征 (91, 384)
                x_i = x[i]  # shape: (91, 384)
                # 当前样本的 c_tau (N+1,)
                c_tau_i = c_tau[i]  # shape: (N+1,)
                
                # 遍历每个音素段
                for j in range(1, len(c_tau_i)):
                    # 当前音素段的起止索引
                    start_idx = int(c_tau_i[j - 1].item())
                    end_idx = int(c_tau_i[j].item())
                    
                    # 对当前音素段的特征进行累加
                    segment_sum = x_i[start_idx:end_idx].sum(dim=0)  # shape: (384,)
                    
                    # 将累加的结果写回到对应的时间步范围
                    Y[i, start_idx:end_idx] = segment_sum
            x = x + Y
            #x = Y
        if self.bert_layer is not None:
            # assert bert_feats is not None
            if  bert_feats is not None:
                bert_feats = self.bert_layer(bert_feats).transpose(1, 2)
                x = x + bert_feats
            if emotions is not None:
                emotions = emotions.unsqueeze(1).repeat(1,x.shape[1],1)
                x = x + emotions
        return self._forward(x, (input != self.padding_idx).unsqueeze(2), conditioning)  # (B, L, 1)


class FFTransformer(nn.Module):
    def __init__(
        self,
        in_dim,
        out_dim=1,
        n_layers=6,
        n_head=1,
        d_head=64,
        d_inner=1024,
        kernel_size=3,
        dropout=0.1,
        dropatt=0.1,
        dropemb=0.0,
    ):
        super(FFTransformer, self).__init__()
        self.in_dim = in_dim
        self.out_dim = out_dim
        self.n_head = n_head
        self.d_head = d_head

        self.pos_emb = PositionalEmbedding(self.in_dim)
        self.drop = nn.Dropout(dropemb)
        self.layers = nn.ModuleList()

        for _ in range(n_layers):
            self.layers.append(
                TransformerLayer(n_head, in_dim, d_head, d_inner, kernel_size, dropout, dropatt=dropatt)
            )

        self.dense = LinearNorm(in_dim, out_dim)

    def forward(self, dec_inp, in_lens):
        # B, C, T --> B, T, C
        inp = dec_inp.transpose(1, 2)
        mask = get_mask_from_lengths(in_lens)[..., None]

        pos_seq = torch.arange(inp.size(1), device=inp.device).to(inp.dtype)
        pos_emb = self.pos_emb(pos_seq) * mask

        out = self.drop(inp + pos_emb)

        for layer in self.layers:
            out = layer(out, mask=mask)

        out = self.dense(out).transpose(1, 2)
        return out
