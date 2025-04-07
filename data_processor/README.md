# 西安方言处理工具

## 功能特点

- **方言转换**：将普通话文本转换为西安方言的音素表示
- **音频处理**：计算音频文件时长并处理相关元数据
- **BERT特征提取**：可选择性地从文本中提取BERT特征
- **数据格式化**：将处理结果保存为标准化的JSON格式，便于后续使用

## 目录结构

```
xian_dialect_processor/
├── __init__.py
├── converter/              # 方言转换相关模块
│   ├── __init__.py
│   ├── dialect_converter.py  # 主要转换逻辑
│   ├── phonetic_rules.py     # 音系规则定义
│   └── tone_type.py          # 声调类型定义
├── features/               # 特征提取相关模块
│   ├── __init__.py
│   ├── audio_processor.py    # 音频处理
│   └── bert_processor.py     # BERT特征提取
├── utils/                  # 工具函数
│   ├── __init__.py
│   └── io_utils.py           # 输入输出相关工具
└── main.py                 # 主程序入口
```

## 使用方法

### 基本用法

```bash
python main.py <转录文本路径> <输出JSON路径>
```

### 生成BERT特征

```bash
python main.py <转录文本路径> <输出JSON路径> --generate_bert --bert_model <BERT模型路径> --bert_path <BERT特征输出路径>
```

### 完整参数说明

```
参数:
  text_path            转录文本路径，每行格式为"音频文件路径 文本内容"
  output_path          输出JSON文件路径
  --bert_path PATH     BERT特征输出路径
  --bert_model PATH    BERT模型路径
  --device DEVICE      计算设备 (例如 'cuda:0', 'cpu')，默认为'cuda:0'
  --generate_bert      是否生成BERT特征，设置此标志将生成特征
```

## 输入格式

转录文本文件的格式应为每行一个音频文件和对应的文本，用空格分隔：

```
/path/to/audio1.wav 这是第一段文本
/path/to/audio2.wav 这是第二段文本
...
```

## 输出格式

输出的JSON文件中，每行是一个JSON对象，包含以下字段：

```json
{
  "audio_filepath": "/path/to/audio.wav",
  "duration": 5.24,
  "text": "原始文本",
  "speaker": 0,
  "normalized_text": "@ʨ @yo˥˧ @s @ei˥ @t @i @p @ei˨˦ @ʨ @yo˨˦",
  "phoneme_length": [1, 3, 1, 3, 1, 1, 1, 3, 1, 3]
}
```

## BERT特征输出

如果启用BERT特征生成，会在指定的`--bert_path`目录下生成与音频文件对应的`.npy`文件，文件名格式为`{音频目录名}_{音频文件名}.npy`。

## 方言转换规则

西安方言转换基于以下规则：

1. 声母转换：如'b'转为'p'，'p'转为'pʰ'等
2. 韵母转换：如'ao'转为'au'，'an'转为'ã'等
3. 声调转换：普通话四声转为西安方言的阴平、阳平、上声、去声
4. 特殊字词处理：对一些特殊字词使用预定义的方言读音

详细的转换规则可在`converter/phonetic_rules.py`文件中查看和修改。

## 自定义方言字典

可以通过修改`phonetic_rules.py`中的`BASE_DIALECT_DICT`或在实例化`XianDialectConverter`时传入自定义字典来扩展方言词汇表：

```python
custom_dict = {
    "新词": ["自定义读音"],
    # ...
}
converter = XianDialectConverter(custom_dict)
```

## 示例

### 基本处理

```bash
python main.py ./data/transcripts.txt ./output/metadata.json
```

### 生成BERT特征

```bash
python main.py ./data/transcripts.txt ./output/metadata.json --generate_bert --bert_model ./models/chinese-roberta-wwm-ext-large/ --bert_path ./output/bert_features/ --device cuda:0
```

## 注意事项

1. 确保音频文件可访问且格式正确（支持wav、mp3等常见格式）
2. BERT模型需要预先下载，建议使用中文预训练模型如`chinese-roberta-wwm-ext-large`
3. 生成BERT特征需要较大的GPU内存，如内存不足可切换到CPU模式（`--device cpu`）

## 扩展功能

本工具可以根据需要进行扩展：

1. 添加更多方言转换规则
2. 集成语音识别功能
3. 添加更多特征提取方法
4. 支持批处理和多进程处理

