from typing import Dict, List, Optional, Tuple
import jieba
from pypinyin import lazy_pinyin, Style

from .phonetic_rules import INITIAL_RULES, FINAL_RULES, TONE_RULES, BASE_DIALECT_DICT

class XianDialectConverter:
    def __init__(self, custom_dict: Optional[Dict[str, List[str]]] = None):
        # 基础读音字典
        self.dialect_dict = BASE_DIALECT_DICT.copy()
        
        # 合并自定义字典
        if custom_dict:
            self.dialect_dict.update(custom_dict)
        
        # 声母、韵母和声调对应规则
        self.initial_rules = INITIAL_RULES
        self.final_rules = FINAL_RULES
        self.tone_rules = TONE_RULES
        
        self.cache = {}

    def _normalize_dict_item(self, item):
        """规范化字典条目为(声母,韵母)格式"""
        if len(item) == 1:
            # 单元素假设为韵母或完整音节
            return "", item[0]
        elif len(item) >= 2:
            # 双元素假设为[声母,韵母]
            return item[0], item[1]
        return "", ""

    def _apply_phonological_rules(self, orig_initials, orig_finals):
        """应用音系规则转换普通话拼音到西安方言拼音"""
        trans_initials = []
        trans_finals = []
        
        for c, v in zip(orig_initials, orig_finals):
            initial, final = "", ""
            
            # 提取声调
            if v and v[-1] in "12345":
                tone = v[-1]
                v_without_tone = v[:-1]
            else:
                tone = "5"  # 默认为轻声
                v_without_tone = v
            
            # 转换声母
            if c in ['y','w',''] and v_without_tone in ['e', 'ai', 'ei', 'ao', 'an', 'en', 'ang', 'ou']:
                initial = 'ŋ'
            elif c in self.initial_rules:
                initial = self.initial_rules[c]
            else:
                initial = c
            
            # 转换韵母(特殊规则优先)
            if c in ['z', 'c', 's'] and v_without_tone == 'i':
                final = 'ɿ'
            elif c in ['zh', 'ch', 'sh', 'r'] and v_without_tone == 'i':
                final = 'ʅ'
            elif c in ['j','q','x'] and v_without_tone == 'un':
                final = 'yẽ'
            elif c in ['j','q','x'] and v_without_tone == 'uan':
                final = 'yã'
            elif v_without_tone in self.final_rules:
                final = self.final_rules[v_without_tone]
            else:
                final = v_without_tone
                
            # 添加声调
            if tone in self.tone_rules:
                final += self.tone_rules[tone]
            
            trans_initials.append(initial)
            trans_finals.append(final)
        
        return trans_initials, trans_finals

    def convert(self, text: str) -> Tuple[List[str], List[str], str]:
        """将文本转换为西安方言读音序列，返回(声母列表,韵母列表,音素表示)"""
        if text in self.cache:
            return self.cache[text]
        
        result_initials = []
        result_finals = []
        
        # 分词处理
        words = list(jieba.cut(text))
        
        for word in words:
            # 检查整词是否在dialect_dict中
            if word in self.dialect_dict:
                initial, final = self._normalize_dict_item(self.dialect_dict[word])
                result_initials.append(initial)
                result_finals.append(final)
                continue
            
            # 获取整个词的拼音序列
            orig_initials = lazy_pinyin(word, neutral_tone_with_five=True, style=Style.INITIALS)
            orig_finals = lazy_pinyin(word, neutral_tone_with_five=True, style=Style.FINALS_TONE3)
            
            # 逐字处理
            for i, char in enumerate(word):
                if char in self.dialect_dict:
                    # 使用预定义的方言读音
                    initial, final = self._normalize_dict_item(self.dialect_dict[char])
                    result_initials.append(initial)
                    result_finals.append(final)
                elif char in "，。、？!,.?":  # 标点符号
                    result_initials.append("")
                    result_finals.append(char)
                else:
                    # 使用拼音转换规则
                    if i < len(orig_initials) and i < len(orig_finals):
                        char_initials, char_finals = self._apply_phonological_rules(
                            [orig_initials[i]], [orig_finals[i]]
                        )
                        result_initials.extend(char_initials)
                        result_finals.extend(char_finals)
        
        # 生成音素表示
        text_phone = []
        for _o in zip(result_initials, result_finals):
            if _o[0] != _o[1] and _o[0] != '':
                _o = ['@'+i for i in _o]
                text_phone.extend(_o)
            elif _o[0] != _o[1] and _o[0] == '':
                if _o[1] not in "，。、？!,.?":
                    text_phone.append('@'+_o[1])
                else:
                    text_phone.append(_o[1])
            else:
                text_phone.extend(list(_o[0]))

        text_phone = " ".join(text_phone)
        
        # 缓存结果
        self.cache[text] = (result_initials, result_finals, text_phone)
        return result_initials, result_finals, text_phone

