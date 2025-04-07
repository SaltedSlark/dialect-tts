#!/usr/bin/env python3
import os
import argparse
from tqdm import tqdm

from converter.dialect_converter import XianDialectConverter
from features.audio_processor import get_audio_duration
from features.bert_processor import BertFeatureExtractor
from utils.io_utils import load_transcript_dict, save_json, ensure_dir

def process_audio_files(trans_dict, converter, bert_extractor=None, bert_path=None):
    """处理音频文件并生成 JSON 数据"""
    output_data = []
    
    for filepath, text in tqdm(trans_dict.items()):
        try:
            duration = get_audio_duration(filepath)
            
            # 转换为方言音素
            result_initials, result_finals, phoneme_text = converter.convert(text)
            
            # 提取BERT特征（如果需要）
            if bert_extractor and bert_path:
                name = os.path.join(bert_path, f"{filepath.split('/')[-1].replace('.wav', '.npy')}")
                bert_extractor.extract_features(text, result_initials, result_finals, name)
            
            # 计算音素长度
            phoneme_length = []
            for char in phoneme_text.split(" "):
                if '@' in char:
                    phoneme_length.append(len(char)-1)
                elif char in "，。、？!,.?":  # 标点符号
                    phoneme_length.append(len(char)+1)
                else:
                    phoneme_length.append(len(char))
            
            # 构造输出数据
            cur_info = {
                "audio_filepath": filepath,
                "duration": duration,
                "text": text,
                "speaker": 0,
                "normalized_text": phoneme_text,
                "phoneme_length": phoneme_length
            }
            output_data.append(cur_info)
            
        except Exception as e:
            print(f"Error processing {filepath}: {e}")
            continue
            
    return output_data

def main():
    parser = argparse.ArgumentParser(description="西安方言处理工具")
    parser.add_argument("text_path", help="转录文本路径")
    parser.add_argument("output_path", help="输出JSON路径")
    parser.add_argument("--bert_path", help="BERT特征输出路径")
    parser.add_argument("--bert_model", help="BERT模型路径")
    parser.add_argument("--device", default="cuda:0", help="设备 (例如 'cuda:0', 'cpu')")
    parser.add_argument("--generate_bert", action="store_true", help="是否生成BERT特征")
    
    args = parser.parse_args()
    
    # 加载转录字典
    trans_dict = load_transcript_dict(args.text_path)
    
    # 初始化方言转换器
    converter = XianDialectConverter()
    
    # 初始化BERT特征提取器（如果需要）
    bert_extractor = None
    if args.generate_bert:
        if not args.bert_model or not args.bert_path:
            print("Error: --bert_model and --bert_path are required when --generate_bert is set")
            return
        ensure_dir(args.bert_path)
        bert_extractor = BertFeatureExtractor(args.bert_model, args.device)
    
    # 处理音频文件
    data = process_audio_files(trans_dict, converter, bert_extractor, args.bert_path)
    
    # 保存为JSON文件
    save_json(data, args.output_path)
    
    print(f"处理完成。JSON已保存到 {args.output_path}")
    if args.generate_bert:
        print(f"BERT特征已保存到 {args.bert_path}")

if __name__ == "__main__":
    main()

