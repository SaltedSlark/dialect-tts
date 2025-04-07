import os
import json

def load_transcript_dict(text_path):
    """从文本文件加载转录字典"""
    trans_dict = {}
    with open(text_path) as f:
        for line in f.readlines():
            try:
                filename, text = line.strip().split(' ', 1)  # 只在第一个空格处分割
                trans_dict[filename] = text
            except ValueError:
                continue
    return trans_dict

def save_json(data, output_path):
    """保存结果为 JSON 文件，每行一个JSON对象"""
    with open(output_path, "w", encoding="utf-8") as f:
        for line in data:
            f.writelines(json.dumps(line, ensure_ascii=False)+'\n')

def ensure_dir(dir_path):
    """确保目录存在"""
    os.makedirs(dir_path, exist_ok=True)

