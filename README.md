# 基于nvidia NeMo框架下fastpitch-tts算法开发的语音合成模型
支持多语言，包括中国方言。本项目以西安方言为案例。
## 环境配置
```
   conda create --name nemo python==3.8
   conda activate nemo
   pip install -r  ./codes/NeMo/requirements.txt
```

## 数据
- 喜马拉雅《白鹿原》陕西方言有声小说 30小时

## 音素设计
- 中文普通话
  - 拼音
- 中英混合
  - 国际音标
- 方言
  - 参考[西安方言](https://humanum.arts.cuhk.edu.hk/Lexis/lexi-mf/dialectIndex.php?point=A)声母、韵母以及声调系统
  - 参考[语保工程](https://zhongguoyuyan.cn/)，dialect-tts方案可推广至大多数方言
  
## 模型
- 总体参考[MassTTS](https://github.com/anyvoiceai/MassTTS/)
  - 新增phoneme_len_regulator，idea来自[论文](https://arxiv.org/abs/2110.07192)
  - 修改aligner中attn计算方式，idea来自[NeMo issue](https://github.com/NVIDIA/NeMo/pull/6806)
  - 加入energy辅助训练

## 模型训练
- 数据处理

  ```
  python main.py /path/to/text_file.txt /path/to/output.json --generate_bert --bert_model ./chinese-roberta-wwm-ext-large/ --bert_path /path/to/bert_features/
  ```

- 配置训练参数

- pitch&energy提取
    ```
    CUDA_VISIBLE_DEVICES=0 python ./codes/NeMo/examples/tts/fastpitch_shaanxi.py \
    train_dataset=train.json \
    validation_datasets=val.json \
    sup_data_path=./sup_data \
    exp_manager.exp_dir=./tmp \
    +bert_path=./bert_feats \
    trainer.strategy=null trainer.precision=32 name=testing pitch_mean=217.7085 pitch_std=58.9581 trainer.max_epochs=1
    ```

- fastpitch模型训练
    ```
    CUDA_VISIBLE_DEVICES=1,3 python ./codes/NeMo/examples/tts/fastpitch_shaanxi.py \
    train_dataset=./train.json \
    validation_datasets=./val.json \
    sup_data_path=./sup_data \
    exp_manager.exp_dir=./results \
    +bert_path=./bert_feats \
    trainer.strategy=ddp name=fs2 pitch_mean={pitch_mean} pitch_std={pitch_std} pitch_fmin={pitch_fmin} pitch_fmax={pitch_fmax}
    ```

- hifigan训练准备

  - pred_mels提取
  
    ```
    CUDA_VISIBLE_DEVICES=3 python ./codes/NeMo/examples/tts/fastpitch_shaanxi.py \
    train_dataset=./train.json \
    validation_datasets=./val.json \
    sup_data_path=./sup_data \
    exp_manager.exp_dir=./results \
    +bert_path=./bert_feats \
    trainer.strategy=ddp name=fs2 pitch_mean={pitch_mean} pitch_std={pitch_std} pitch_fmin={pitch_fmin} pitch_fmax={pitch_fmax}\
    model.train_ds.dataloader_params.batch_size=1 trainer.precision=32 \
    model.get_mel_result=./sup_data/pred_mels \
    trainer.max_epochs=1000000
    ```

   - 数据集构建
   
    ```
    python ./tools/generate_hifigan_meta.py --audio_dir ./audio_files --output_dir ./metas/nemo --mel_dir ./sup_data/pred_mels
    ```


- hifigan模型微调
    ```
    CUDA_VISIBLE_DEVICES=3 python ./codes/NeMo/examples/tts/hifigan_finetune.py \
    train_dataset=./metas/nemo/train_manifest_mel.json \
    validation_datasets=./metas/nemo/val_manifest_mel.json \
    exp_manager.exp_dir=./results \
    model/train_ds=train_ds_finetune model/validation_ds=val_ds_finetune \
    trainer.strategy=null name=hifigan \
    trainer.check_val_every_n_epoch=1 \
    +init_from_pretrained_model='tts_zh_hifigan_sfspeech' \
    --config-name hifigan.yaml
    ```
 
## 实验对比
 - [demopage](https://saltedslark.github.io/)

