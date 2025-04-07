from pydub import AudioSegment

def get_audio_duration(filepath):
    """获取音频文件时长（秒）"""
    audio = AudioSegment.from_file(filepath)
    return len(audio) / 1000.0  # 转换为秒

