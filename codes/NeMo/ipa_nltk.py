import nltk
import re
from nltk.corpus import cmudict
from pypinyin import pinyin, Style

# 下载 CMU Pronouncing Dictionary（首次运行时需要）
# nltk.download('cmudict')

# 加载 CMU Pronouncing Dictionary
cmu_dict = cmudict.dict()

# 自定义英文发音字典（处理未找到的英文单词）
custom_pronunciations = {
    "steins": ["S", "T", "AY1", "N", "Z"],  # 自定义 Steins 的发音
}

# ARPAbet 到 IPA 的映射表
arpabet_to_ipa = {
    "AA": "ɑ", "AE": "æ", "AH": "ʌ", "AO": "ɔ", "AW": "aʊ", "AY": "aɪ",
    "B": "b", "CH": "tʃ", "D": "d", "DH": "ð", "EH": "ɛ", "ER": "ɝ", "EY": "eɪ",
    "F": "f", "G": "ɡ", "HH": "h", "IH": "ɪ", "IY": "i", "JH": "dʒ", "K": "k",
    "L": "l", "M": "m", "N": "n", "NG": "ŋ", "OW": "oʊ", "OY": "ɔɪ", "P": "p",
    "R": "ɹ", "S": "s", "SH": "ʃ", "T": "t", "TH": "θ", "UH": "ʊ", "UW": "u",
    "V": "v", "W": "w", "Y": "j", "Z": "z", "ZH": "ʒ"
}

# 拼音声母到 IPA 的映射表
pinyin_initial_to_ipa = {
    "b": "p", "p": "pʰ", "m": "m", "f": "f",
    "d": "d", "t": "tʰ", "n": "n", "l": "l",
    "g": "k", "k": "kʰ", "h": "x",
    "j": "tɕ", "q": "tɕʰ", "x": "ɕ",
    "zh": "ʈʂ", "ch": "ʈʂʰ", "sh": "ʂ", "r": "ɻ",
    "z": "ts", "c": "tsʰ", "s": "s",
    "y": "j", "w": "w"
}

# 拼音韵母到 IPA 的映射表（包含轻声形式）
pinyin_final_to_ipa_with_tone = {
    # 单韵母
    "a1": "a˥", "a2": "a˧˥", "a3": "a˨˩˦", "a4": "a˥˩", "a": "a",
    "o1": "o˥", "o2": "o˧˥", "o3": "o˨˩˦", "o4": "o˥˩", "o": "o",
    "e1": "ɤ˥", "e2": "ɤ˧˥", "e3": "ɤ˨˩˦", "e4": "ɤ˥˩", "e": "ɤ",
    "i1": "i˥", "i2": "i˧˥", "i3": "i˨˩˦", "i4": "i˥˩", "i": "i",
    "u1": "u˥", "u2": "u˧˥", "u3": "u˨˩˦", "u4": "u˥˩", "u": "u",
    "ü1": "y˥", "ü2": "y˧˥", "ü3": "y˨˩˦", "ü4": "y˥˩", "ü": "y",

    # 复合韵母
    "ai1": "aɪ˥", "ai2": "aɪ˧˥", "ai3": "aɪ˨˩˦", "ai4": "aɪ˥˩", "ai": "aɪ",
    "ei1": "eɪ˥", "ei2": "eɪ˧˥", "ei3": "eɪ˨˩˦", "ei4": "eɪ˥˩", "ei": "eɪ",
    "ao1": "aʊ˥", "ao2": "aʊ˧˥", "ao3": "aʊ˨˩˦", "ao4": "aʊ˥˩", "ao": "aʊ",
    "ou1": "oʊ˥", "ou2": "oʊ˧˥", "ou3": "oʊ˨˩˦", "ou4": "oʊ˥˩", "ou": "oʊ",

    # 鼻韵母
    "an1": "an˥", "an2": "an˧˥", "an3": "an˨˩˦", "an4": "an˥˩", "an": "an",
    "en1": "ən˥", "en2": "ən˧˥", "en3": "ən˨˩˦", "en4": "ən˥˩", "en": "ən",
    "ang1": "ɑŋ˥", "ang2": "ɑŋ˧˥", "ang3": "ɑŋ˨˩˦", "ang4": "ɑŋ˥˩", "ang": "ɑŋ",
    "eng1": "əŋ˥", "eng2": "əŋ˧˥", "eng3": "əŋ˨˩˦", "eng4": "əŋ˥˩", "eng": "əŋ",
    "ong1": "ʊŋ˥", "ong2": "ʊŋ˧˥", "ong3": "ʊŋ˨˩˦", "ong4": "ʊŋ˥˩", "ong": "ʊŋ",

    # 特殊韵母
    "er1": "ɚ˥", "er2": "ɚ˧˥", "er3": "ɚ˨˩˦", "er4": "ɚ˥˩", "er": "ɚ",

    # 复合鼻韵母
    "ian1": "iɛn˥", "ian2": "iɛn˧˥", "ian3": "iɛn˨˩˦", "ian4": "iɛn˥˩", "ian": "iɛn",
    "uan1": "uæn˥", "uan2": "uæn˧˥", "uan3": "uæn˨˩˦", "uan4": "uæn˥˩", "uan": "uæn",
    "üan1": "yæn˥", "üan2": "yæn˧˥", "üan3": "yæn˨˩˦", "üan4": "yæn˥˩", "üan": "yæn",
    "iang1": "iɑŋ˥", "iang2": "iɑŋ˧˥", "iang3": "iɑŋ˨˩˦", "iang4": "iɑŋ˥˩", "iang": "iɑŋ",
    "uang1": "uɑŋ˥", "uang2": "uɑŋ˧˥", "uang3": "uɑŋ˨˩˦", "uang4": "uɑŋ˥˩", "uang": "uɑŋ",

    # 特殊复合韵母
    "iong1": "iʊŋ˥", "iong2": "iʊŋ˧˥", "iong3": "iʊŋ˨˩˦", "iong4": "iʊŋ˥˩", "iong": "iʊŋ",
    "üe1": "yɛ˥", "üe2": "yɛ˧˥", "üe3": "yɛ˨˩˦", "üe4": "yɛ˥˩", "üe": "yɛ"
}
pinyin_final_to_ipa_with_tone = {
    # 单韵母
    "a1": "a˥", "a2": "a˧˥", "a3": "a˨˩˦", "a4": "a˥˩", "a": "a",
    "o1": "o˥", "o2": "o˧˥", "o3": "o˨˩˦", "o4": "o˥˩", "o": "o",
    "e1": "ɤ˥", "e2": "ɤ˧˥", "e3": "ɤ˨˩˦", "e4": "ɤ˥˩", "e": "ɤ",
    "i1": "i˥", "i2": "i˧˥", "i3": "i˨˩˦", "i4": "i˥˩", "i": "i",
    "u1": "u˥", "u2": "u˧˥", "u3": "u˨˩˦", "u4": "u˥˩", "u": "u",
    "ü1": "y˥", "ü2": "y˧˥", "ü3": "y˨˩˦", "ü4": "y˥˩", "ü": "y",

    # 复合韵母
    "ai1": "aɪ˥", "ai2": "aɪ˧˥", "ai3": "aɪ˨˩˦", "ai4": "aɪ˥˩", "ai": "aɪ",
    "ei1": "eɪ˥", "ei2": "eɪ˧˥", "ei3": "eɪ˨˩˦", "ei4": "eɪ˥˩", "ei": "eɪ",
    "ao1": "aʊ˥", "ao2": "aʊ˧˥", "ao3": "aʊ˨˩˦", "ao4": "aʊ˥˩", "ao": "aʊ",
    "ou1": "oʊ˥", "ou2": "oʊ˧˥", "ou3": "oʊ˨˩˦", "ou4": "oʊ˥˩", "ou": "oʊ",
    "ui1": "ueɪ˥", "ui2": "ueɪ˧˥", "ui3": "ueɪ˨˩˦", "ui4": "ueɪ˥˩", "ui": "ueɪ",  # 补充 ui
    "iu1": "iəʊ˥", "iu2": "iəʊ˧˥", "iu3": "iəʊ˨˩˦", "iu4": "iəʊ˥˩", "iu": "iəʊ",  # 补充 iu

    # 鼻韵母
    "an1": "an˥", "an2": "an˧˥", "an3": "an˨˩˦", "an4": "an˥˩", "an": "an",
    "en1": "ən˥", "en2": "ən˧˥", "en3": "ən˨˩˦", "en4": "ən˥˩", "en": "ən",
    "ang1": "ɑŋ˥", "ang2": "ɑŋ˧˥", "ang3": "ɑŋ˨˩˦", "ang4": "ɑŋ˥˩", "ang": "ɑŋ",
    "eng1": "əŋ˥", "eng2": "əŋ˧˥", "eng3": "əŋ˨˩˦", "eng4": "əŋ˥˩", "eng": "əŋ",
    "ong1": "ʊŋ˥", "ong2": "ʊŋ˧˥", "ong3": "ʊŋ˨˩˦", "ong4": "ʊŋ˥˩", "ong": "ʊŋ",

    # 特殊韵母
    "er1": "ɚ˥", "er2": "ɚ˧˥", "er3": "ɚ˨˩˦", "er4": "ɚ˥˩", "er": "ɚ",

    # 复合鼻韵母
    "ian1": "iɛn˥", "ian2": "iɛn˧˥", "ian3": "iɛn˨˩˦", "ian4": "iɛn˥˩", "ian": "iɛn",
    "uan1": "uæn˥", "uan2": "uæn˧˥", "uan3": "uæn˨˩˦", "uan4": "uæn˥˩", "uan": "uæn",
    "üan1": "yæn˥", "üan2": "yæn˧˥", "üan3": "yæn˨˩˦", "üan4": "yæn˥˩", "üan": "yæn",
    "iang1": "iɑŋ˥", "iang2": "iɑŋ˧˥", "iang3": "iɑŋ˨˩˦", "iang4": "iɑŋ˥˩", "iang": "iɑŋ",
    "uang1": "uɑŋ˥", "uang2": "uɑŋ˧˥", "uang3": "uɑŋ˨˩˦", "uang4": "uɑŋ˥˩", "uang": "uɑŋ",

    # 特殊复合韵母
    "iong1": "iʊŋ˥", "iong2": "iʊŋ˧˥", "iong3": "iʊŋ˨˩˦", "iong4": "iʊŋ˥˩", "iong": "iʊŋ",
    "üe1": "yɛ˥", "üe2": "yɛ˧˥", "üe3": "yɛ˨˩˦", "üe4": "yɛ˥˩", "üe": "yɛ",

    # 补充其他复合韵母
    "ua1": "ua˥", "ua2": "ua˧˥", "ua3": "ua˨˩˦", "ua4": "ua˥˩", "ua": "ua",
    "uo1": "uo˥", "uo2": "uo˧˥", "uo3": "uo˨˩˦", "uo4": "uo˥˩", "uo": "uo",
    "ie1": "iɛ˥", "ie2": "iɛ˧˥", "ie3": "iɛ˨˩˦", "ie4": "iɛ˥˩", "ie": "iɛ",
    "ue1": "ue˥", "ue2": "ue˧˥", "ue3": "ue˨˩˦", "ue4": "ue˥˩", "ue": "ue",
    "in1": "in˥", "in2": "in˧˥", "in3": "in˨˩˦", "in4": "in˥˩", "in": "in",
    "un1": "un˥", "un2": "un˧˥", "un3": "un˨˩˦", "un4": "un˥˩", "un": "un",
    "ün1": "yn˥", "ün2": "yn˧˥", "ün3": "yn˨˩˦", "ün4": "yn˥˩", "ün": "yn",
    "ing1": "iŋ˥", "ing2": "iŋ˧˥", "ing3": "iŋ˨˩˦", "ing4": "iŋ˥˩", "ing": "iŋ",
    "uai1": "uaɪ˥", "uai2": "uaɪ˧˥", "uai3": "uaɪ˨˩˦", "uai4": "uaɪ˥˩", "uai": "uaɪ",
    "uei1": "ueɪ˥", "uei2": "ueɪ˧˥", "uei3": "ueɪ˨˩˦", "uei4": "ueɪ˥˩", "uei": "ueɪ",
    "iao1": "iɑʊ˥", "iao2": "iɑʊ˧˥", "iao3": "iɑʊ˨˩˦", "iao4": "iɑʊ˥˩", "iao": "iɑʊ",
    "iou1": "iəʊ˥", "iou2": "iəʊ˧˥", "iou3": "iəʊ˨˩˦", "iou4": "iəʊ˥˩", "iou": "iəʊ"
}
# 分解拼音为声母和韵母
def split_pinyin(pinyin_syllable):
    initials = list(pinyin_initial_to_ipa.keys())
    for initial in initials:
        if pinyin_syllable.startswith(initial):
            return initial, pinyin_syllable[len(initial):]
    return "", pinyin_syllable  # 无声母时（如 "a", "ai"）

# 将中文句子转换为 IPA（声母和韵母拆开并附加音调）
def chinese_to_ipa_segmented(sentence):
    pinyin_list = pinyin(sentence, style=Style.TONE3)  # 获取拼音（带声调）
    ipa_result = []
    for syllables in pinyin_list:
        for syllable in syllables:
            initial, final = split_pinyin(syllable)
            ipa_initial = pinyin_initial_to_ipa.get(initial, "")
            ipa_final = pinyin_final_to_ipa_with_tone.get(final, "")
            if ipa_initial != "":
                ipa_result.append(ipa_initial)  # 声母
            if ipa_final != "":
                ipa_result.append(ipa_final)   # 韵母（带音调）
    return ipa_result

# 将英文单词转换为 IPA 并分解为音节
def process_stress(phoneme):
    if phoneme[-1] in "012":  # 判断是否有重音标记
        stress = phoneme[-1]
        phoneme = phoneme[:-1]  # 去掉重音标记
        ipa = arpabet_to_ipa.get(phoneme, phoneme)  # 转换为IPA
        if stress == "1":  # 主重音
            return f"ˈ{ipa}"
        elif stress == "2":  # 次重音
            return f"ˌ{ipa}"
        else:  # 无重音
            return ipa
    else:
        return arpabet_to_ipa.get(phoneme, phoneme)

# 将英文单词转换为IPA并分解为音节
def word_to_ipa_syllables(word):
    word_lower = word.lower()
    if word_lower in custom_pronunciations:  # 检查自定义发音
        arpabet = custom_pronunciations[word_lower]
    elif word_lower in cmu_dict:  # 检查CMU字典
        arpabet = cmu_dict[word_lower][0]
    else:
        return ["failed"]
    ipa_syllables = [process_stress(phoneme) for phoneme in arpabet]
    return ipa_syllables

# 综合处理英文和中文句子
def multilingual_to_ipa(sentence):
    ipa_result = []
    tokens = re.findall(r'[\u4e00-\u9fff]|[a-zA-Z]+|\S', sentence)  # 分割为中文字符、英文单词和其他符号
    for token in tokens:
        if re.match(r'[\u4e00-\u9fff]', token):  # 中文字符
            ipa_result.extend(chinese_to_ipa_segmented(token))
        elif re.match(r'[a-zA-Z]+', token):  # 英文单词
            if "failed" in word_to_ipa_syllables(token):
                continue
            ipa_result.extend(word_to_ipa_syllables(token))
        else:  # 其他符号
            ipa_result.append(token)
    return ipa_result,[len(ipa) for ipa in ipa_result]

# 示例输入
sentence = "而这又是怎么回事？"
result = multilingual_to_ipa(sentence)
print(result)
