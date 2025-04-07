import os
import torch
import numpy as np
from transformers import AutoTokenizer, AutoModelForMaskedLM

class BertFeatureExtractor:
    def __init__(self, model_path, device='cuda:0'):
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForMaskedLM.from_pretrained(model_path)
        self.device = device
        self.model.to(device)
        
    def extract_features(self, text, initials, finals, output_path):
        """提取BERT特征并保存"""
        with torch.no_grad():
            inputs = self.tokenizer(text, return_tensors='pt')
            for i in inputs:
                inputs[i] = inputs[i].to(self.device)
            res = self.model(**inputs, output_hidden_states=True)
            res = torch.cat(res['hidden_states'][-3:-2], -1)[0].cpu().numpy()
            
        _vecs = []
        _text = []
        _chars = []
        for _o in zip(zip(initials, finals), text, res[1:-1]):
            _o, _c, _vec = _o
            if _o[0] != _o[1] and _o[0] != '':
                _text.extend(['@'+i for i in _o])
                _chars.extend([_c]*2)
                _vecs.extend([_vec]*2)
            elif _o[0] != _o[1] and _o[0] == '':
                _text.append('@'+_o[1])
                _chars.append(_c)
                _vecs.append(_vec)
            else:
                _text.extend(list(_o[0]))  
                _chars.extend([_c]*len(_o[0]))
                _vecs.extend([_vec]*len(_o[0]))
        
        try:
            assert len(_text) == len(_chars)
            assert len(_vecs) == len(_text)
        except:
            print(f"Error in {output_path}")
            return False
            
        _vecs = np.stack([res[0]] + _vecs + [res[-1]])
        np.save(output_path, _vecs)
        return True

