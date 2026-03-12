import os
from dotenv import load_dotenv
import whisper

# 加载环境变量
load_dotenv()

# ------------------- 路径配置 -------------------
# 上传目录
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
# 分析结果存储目录
ANALYSIS_DIR = os.path.join(os.path.dirname(__file__), "analysis_records")
# 关键帧和音频保存目录
MEDIA_EXTRACT_DIR = os.path.join(os.path.dirname(__file__), "media_extracts")

# ------------------- 常量配置 -------------------
# 模拟用户
FAKE_USERS = {
    "player1": {"password": "123456", "role": "player"},
    "coach1": {"password": "123456", "role": "coach"}
}
# 允许的视频格式
ALLOWED_VIDEO_TYPES = ["video/mp4", "video/mov", "video/avi"]
# 最大文件大小（100MB）
MAX_VIDEO_SIZE = 100 * 1024 * 1024
# FFmpeg路径
FFMPEG_PATH = r"D:\ffmpeg\ffmpeg-7.1.1-essentials_build\ffmpeg-7.1.1-essentials_build\bin\ffmpeg.exe"

# ------------------- 模型配置 -------------------
# 加载Whisper模型（轻量级，用于音频转文字）
WHISPER_MODEL = whisper.load_model("base")
# Qwen3.5-Plus API Key
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
if not DASHSCOPE_API_KEY:
    raise ValueError("请在.env文件中配置DASHSCOPE_API_KEY")

# ------------------- 初始化目录 -------------------
def init_directories():
    """初始化所需目录"""
    for dir_path in [UPLOAD_DIR, ANALYSIS_DIR, MEDIA_EXTRACT_DIR]:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

# 初始化目录
init_directories()

# ------------------- 新增：训练日&比赛项目配置 -------------------
# 训练日数据存储目录
TRAINING_DAY_DIR = os.path.join(os.path.dirname(__file__), "training_days")
# 预设比赛项目（以网络布线为例，可自行修改/增删）
PRESET_PROJECTS = [
    {"project_id": "project_1", "project_name": "RJ45水晶头端接", "project_desc": "网络布线标准水晶头端接操作，考核端接规范性、线序正确率、操作时长"},
    {"project_id": "project_2", "project_name": "110配线架端接", "project_desc": "110语音配线架端接操作，考核打线规范性、导通率、操作时长"},
    {"project_id": "project_3", "project_name": "光纤熔接操作", "project_desc": "光纤熔接标准流程，考核端面处理、熔接损耗、热缩管封装规范性"},
    {"project_id": "project_4", "project_name": "链路通断测试", "project_desc": "网络链路通断、串扰、衰减测试操作，考核仪器使用规范性、结果判读正确率"},
    {"project_id": "project_5", "project_name": "机柜理线与标签", "project_desc": "机柜内线缆整理、标签粘贴操作，考核理线美观度、标签规范性、扎带使用标准"}
]
#预设比赛项目（光电项目）
# config.py
PRESET_PHOTOELECTRIC_PROJECTS = [
    {
        "project_id": "photoelectric_1",
        "project_name": "光纤熔接操作",
        "project_desc": "考核光纤熔接的端面处理、熔接参数设置、熔接损耗控制等规范性",
        "evaluation_type": "video_analysis"  # 视频分析（原有逻辑）
    },
    {
        "project_id": "photoelectric_2",
        "project_name": "光电测试仪使用",
        "project_desc": "考核仪器连接规范性、参数设置正确率、结果判读准确性",
        "evaluation_type": "video_analysis"  # 视频分析（原有逻辑）
    },
    {
        "project_id": "photoelectric_3",
        "project_name": "光纤端面清洁",
        "project_desc": "考核清洁步骤、工具使用、清洁效果",
        "evaluation_type": "image_compare",  # 图片对比（上传用户图 vs 标准图）
        "standard_image_url": "http://localhost:8000/static/assets/standard_clean.jpg"  # 标准图路径（需预先准备好）
    },
    {
        "project_id": "photoelectric_4",
        "project_name": "光纤识别与分类",
        "project_desc": "考核光纤类型识别、分类标记",
        "evaluation_type": "doc_upload"  # 文档上传（提交识别结果文档）
    },
    {
        "project_id": "photoelectric_5",
        "project_name": "光纤连接器安装",
        "project_desc": "考核连接器安装步骤、压接规范、损耗测试",
        "evaluation_type": "step_screenshot"  # 步骤截图（上传关键步骤截图）
    }
]

# 初始化训练日目录
def init_training_dir():
    if not os.path.exists(TRAINING_DAY_DIR):
        os.makedirs(TRAINING_DAY_DIR)

# 执行初始化
init_training_dir()