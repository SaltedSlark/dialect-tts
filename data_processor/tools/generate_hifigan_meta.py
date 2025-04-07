#!/usr/bin/env python3
"""
生成NeMo训练所需的元数据文件
包含音频路径、持续时间和对应的梅尔频谱图路径
"""

import os
import json
import argparse
import soundfile as sf  # 用于读取音频文件 [[0]](#__0)
from tqdm import tqdm  # 进度条显示 [[1]](#__1)
import numpy as np  # 数组处理 [[2]](#__2)


def generate_metadata(audio_dir, output_dir, mel_dir=None, val_ratio=0.1):
    """
    生成训练和验证集的元数据文件
    
    参数:
        audio_dir: 音频文件目录
        output_dir: 输出元数据文件目录
        mel_dir: 梅尔频谱图目录，默认与音频目录相同，但文件扩展名为.npy
        val_ratio: 验证集比例，默认为0.1
    """
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 如果未指定mel_dir，则默认与audio_dir相同
    if mel_dir is None:
        mel_dir = audio_dir
    
    # 获取所有音频文件
    audio_files = [f for f in os.listdir(audio_dir) if f.endswith((".wav", ".mp3", ".flac"))]
    print(f"找到 {len(audio_files)} 个音频文件")
    
    # 计算训练集和验证集的分割点
    val_count = max(1, int(len(audio_files) * val_ratio))
    train_count = len(audio_files) - val_count
    
    # 准备输出文件路径
    train_manifest_path = os.path.join(output_dir, "train_manifest_mel.json")
    val_manifest_path = os.path.join(output_dir, "val_manifest_mel.json")
    
    # 处理所有音频文件并生成元数据
    metadata = []
    for audio_file in tqdm(audio_files, desc="处理音频文件"):
        audio_path = os.path.join(audio_dir, audio_file)
        try:
            # 读取音频文件并计算持续时间
            audio_data, sample_rate = sf.read(audio_path)  # [[0]](#__0)
            duration = round(len(audio_data) / sample_rate, 3)
            
            # 构建对应的梅尔频谱图路径
            mel_file = os.path.splitext(audio_file)[0] + ".npy"
            mel_path = os.path.join(mel_dir, mel_file)
            
            # 检查梅尔频谱图文件是否存在
            if not os.path.exists(mel_path):
                print(f"警告: 未找到梅尔频谱图文件 {mel_path}")
                # 如果需要，可以在这里添加生成梅尔频谱图的代码
            
            # 创建元数据条目
            entry = {
                "audio_filepath": audio_path,
                "duration": duration,
                "mel_filepath": mel_path,
            }
            metadata.append(entry)
        except Exception as e:
            print(f"处理文件 {audio_path} 时出错: {e}")
    
    # 打乱数据顺序以确保随机分割
    np.random.seed(42)  # 设置随机种子以确保可重复性 [[2]](#__2)
    np.random.shuffle(metadata)
    
    # 分割训练集和验证集
    train_metadata = metadata[:train_count]
    val_metadata = metadata[train_count:]
    
    # 写入训练集元数据
    with open(train_manifest_path, "w", encoding="utf-8") as f:
        for entry in train_metadata:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")  # [[3]](#__3)
    
    # 写入验证集元数据
    with open(val_manifest_path, "w", encoding="utf-8") as f:
        for entry in val_metadata:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    
    print(f"生成完成: 训练集 {len(train_metadata)} 条, 验证集 {len(val_metadata)} 条")
    print(f"训练集元数据保存至: {train_manifest_path}")
    print(f"验证集元数据保存至: {val_manifest_path}")


def main():
    """主函数，处理命令行参数并调用生成函数"""
    parser = argparse.ArgumentParser(description="生成NeMo训练所需的元数据文件")
    parser.add_argument("--audio_dir", required=True, help="音频文件目录")
    parser.add_argument("--output_dir", required=True, help="输出元数据文件目录")
    parser.add_argument("--mel_dir", help="梅尔频谱图目录，默认与音频目录相同")
    parser.add_argument("--val_ratio", type=float, default=0.1, help="验证集比例，默认为0.1")
    
    args = parser.parse_args()
    
    generate_metadata(
        audio_dir=args.audio_dir,
        output_dir=args.output_dir,
        mel_dir=args.mel_dir,
        val_ratio=args.val_ratio
    )


if __name__ == "__main__":
    main()

