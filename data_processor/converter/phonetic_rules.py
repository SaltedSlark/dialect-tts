from .tone_type import ToneType

# 声母转换规则
INITIAL_RULES = {
    'b': 'p',
    'p': 'pʰ',
    'm': 'm',
    'f': 'f',
    'd': 't',
    't': 'tʰ',
    'n': 'n',
    'l': 'l',
    'z': 'ts',   # 知组声母转ts系列
    'c': 'tsʰ',
    's': 's',
    'zh': 'tʂ',  # 精组声母
    'ch': 'tʂʰ',
    'sh': 'ʂ',
    'r': 'ʐ',
    'j': 'ʨ',
    'q': 'ʨʰ',
    'x': 'ɕ',
    'g': 'k',
    'k': 'kʰ',
    'h': 'x',
    'y': '',
    'w': ''
}

# 韵母转换规则
FINAL_RULES = {
    'i': 'i',      
    'er': 'ər',
    'a': 'a',
    'e': 'ɤ',
    'ai': 'ai',    
    'ei': 'ei',    
    'ao': 'au',
    'ou': 'ou',
    'en': 'ẽ',
    'an': 'ã',
    'eng': 'əŋ',
    'ang': 'aŋ',
    'ia': 'ia',
    'ie': 'iɛ',
    'iao': 'iau',
    'iu': 'iou',
    'iou': 'iou',
    'in': 'iẽ',
    'ian': 'iã',
    'ing': 'iŋ',
    'iang': 'iaŋ',
    'u': 'u',
    'ua': 'ua',
    'uai': 'uɛ',
    'uo': 'uo',
    'o': 'uo',
    'uei': 'uei',
    'uan': 'uã',
    'van': 'yã',
    'uang': 'uaŋ',
    'v': 'y',
    'ue': 'yɛ',
    've': 'yɛ',
    'vn': 'yẽ',
    'un': 'uẽ',
    'uen': 'uẽ',
    'ong': 'uŋ',
    'ueng': 'uŋ',
    'iong': 'yŋ',
}

# 声调转换规则
TONE_RULES = {
    '1': ToneType.阴平.value,
    '2': ToneType.阳平.value,
    '3': ToneType.上声.value,
    '4': ToneType.去声.value,
    '5': ToneType.入声.value
}

# 基础方言字典
BASE_DIALECT_DICT = {
    "白": ["p","ei˨˦"],
    "百": ["p","ei˨˦"],
    "我": ["ŋ","ɤ˥˧"],
    "色": ["s","ei˥"],
    "谁": ["s","ei˨˦"],
    "药": ["yo˥"],
    "脚": ["ʨ","yo˥˧"],
    "角": ["ʨ","yo˥˧"],
    "觉": ["ʨ","yo˨˦"],
    "嚼": ["ʨ","yo˨˦"],
    "却": ["ʨʰ","yo˥˧"],
    "确": ["ʨʰ","yo˨˦"],
    "了": ["l","iɛ"],
    "的": ["t","i"],
    "日": ["ər˨˩"],
    "硬":["n","iŋ˥"],
    "，":["，"],
    "、":["、"],
    "。":["。"],
    "？":["？"],
    # ... 其他已知读音
}

