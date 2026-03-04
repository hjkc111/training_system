import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException, Body, Form
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import jwt
import os
from dotenv import load_dotenv
from pydantic import BaseModel
import shutil
import cv2
import whisper
from PIL import Image
import base64
from io import BytesIO
import json
from dashscope import Generation  # 通义千问SDK

# 加载环境变量
load_dotenv()

# 初始化FastAPI
app = FastAPI(title="学生训练管理系统-视频分析")

# 跨域配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------- 基础配置 -------------------
# 模拟用户
FAKE_USERS = {
    "player1": {"password": "123456", "role": "player"},
    "coach1": {"password": "123456", "role": "coach"}
}
# 上传目录
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
# 分析结果存储目录
ANALYSIS_DIR = os.path.join(os.path.dirname(__file__), "analysis_records")
# 新增：关键帧和音频保存目录
MEDIA_EXTRACT_DIR = os.path.join(os.path.dirname(__file__), "media_extracts")
# 创建目录
for dir_path in [UPLOAD_DIR, ANALYSIS_DIR, MEDIA_EXTRACT_DIR]:
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
# 加载Whisper模型（轻量级，用于音频转文字）
WHISPER_MODEL = whisper.load_model("base")
# Qwen3.5-Plus API Key
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
if not DASHSCOPE_API_KEY:
    raise ValueError("请在.env文件中配置DASHSCOPE_API_KEY")

# ------------------- 数据模型 -------------------
class LoginRequest(BaseModel):
    username: str
    password: str
    role: str

class AnalysisRequest(BaseModel):
    filename: str
    username: str

class HistoryRequest(BaseModel):
    username: str

# ------------------- 登录接口 -------------------
@app.post("/api/auth/login")
async def login(login_data: LoginRequest = Body(...)):
    username = login_data.username
    password = login_data.password
    role = login_data.role
    
    if username not in FAKE_USERS:
        raise HTTPException(status_code=400, detail="用户名不存在")
    user = FAKE_USERS[username]
    if user["password"] != password or user["role"] != role:
        raise HTTPException(status_code=400, detail="密码或身份错误")
    
    expire_minutes = int(os.getenv("JWT_EXPIRE_MINUTES", 60))
    expire = datetime.utcnow() + timedelta(minutes=expire_minutes)
    jwt_secret = os.getenv("JWT_SECRET_KEY", "default_secret_key_for_test")
    token = jwt.encode(
        {"sub": username, "role": role, "exp": expire},
        jwt_secret,
        algorithm="HS256"
    )
    
    return {
        "code": 200,
        "message": "登录成功",
        "token": token,
        "user_info": {"username": username, "role": role}
    }

# ------------------- 视频处理工具函数 -------------------
def extract_video_audio_text(video_path, save_dir):
    """提取视频音频并转文字，同时保存音频文件"""
    import subprocess
    import tempfile
    FFMPEG_PATH = r"D:\ffmpeg\ffmpeg-7.1.1-essentials_build\ffmpeg-7.1.1-essentials_build\bin\ffmpeg.exe"
    
    try:
        print(f"开始提取音频文本: {video_path}")
        # 1. 保存音频文件到指定目录
        audio_filename = os.path.basename(video_path).replace('.MP4', '.wav').replace('.mp4', '.wav')
        audio_save_path = os.path.join(save_dir, audio_filename)
        
        # 2. 用FFmpeg提取音频
        cmd = [
            FFMPEG_PATH,
            "-i", video_path,
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            "-y",
            audio_save_path
        ]
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8"
        )
        
        if result.returncode != 0:
            raise Exception(f"FFmpeg提取音频失败：{result.stderr}")
        
        # 3. 用Whisper解析音频
        result = WHISPER_MODEL.transcribe(
            audio_save_path,
            language="zh",
            fp16=False
        )
        audio_text = result["text"]
        
        # 4. 智能判断音频是否有用：长度<20字符或全是标点/空格则视为无用
        is_audio_useful = len(audio_text.strip()) > 20 and any(c.isalnum() for c in audio_text)
        
        print(f"音频文本提取成功: {audio_text[:100]}...")
        print(f"音频是否有用: {is_audio_useful}")
        
        # 5. 保存音频文本到文件
        text_filename = os.path.basename(video_path).replace('.MP4', '.txt').replace('.mp4', '.txt')
        text_save_path = os.path.join(save_dir, text_filename)
        with open(text_save_path, "w", encoding="utf-8") as f:
            f.write(audio_text)
        
        return audio_text, is_audio_useful
    except Exception as e:
        error_msg = f"音频转文字失败：{str(e)}"
        print(error_msg)
        return "", False

def extract_video_key_frames(video_path, save_dir, num_frames=16):
    """提取视频关键帧，保存到指定目录，返回base64列表"""
    key_frames_base64 = []
    print(f"开始提取关键帧: {video_path}")
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print(f"OpenCV 无法打开视频文件: {video_path}")
        return key_frames_base64

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"视频总帧数: {total_frames}")
    frame_interval = max(1, total_frames // num_frames)
    print(f"帧间隔: {frame_interval}")

    # 创建关键帧保存子目录
    video_name = os.path.basename(video_path).replace('.MP4', '').replace('.mp4', '')
    frame_save_dir = os.path.join(save_dir, f"{video_name}_frames")
    if not os.path.exists(frame_save_dir):
        os.makedirs(frame_save_dir)

    for i in range(num_frames):
        cap.set(cv2.CAP_PROP_POS_FRAMES, i * frame_interval)
        ret, frame = cap.read()
        if not ret:
            print(f"读取第 {i} 帧失败")
            break
        
        # 保存关键帧到本地
        frame_filename = f"frame_{i:03d}.jpg"
        frame_save_path = os.path.join(frame_save_dir, frame_filename)
        cv2.imwrite(frame_save_path, frame)
        
        # 转换为base64
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        buffer = BytesIO()
        img.save(buffer, format="JPEG")
        img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        key_frames_base64.append(img_base64)
        print(f"成功提取第 {i} 帧，已保存到: {frame_save_path}")

    cap.release()
    print(f"关键帧提取完成，共 {len(key_frames_base64)} 帧，保存目录: {frame_save_dir}")
    return key_frames_base64

def call_qwen35(video_text, key_frames_base64, username, is_audio_useful):
    """调用Qwen3.5-Plus分析视频，适配世界技能大赛，输出token消耗"""
    # 提示词：世界技能大赛技术动作识别
    prompt = f"""
    你是一名专业的世界技能大赛技术动作分析师，现在需要分析用户{username}上传的训练视频：
    1. 视频音频文字内容：{video_text if is_audio_useful else '（音频内容无效，仅分析视频画面）'}
    2. 视频关键帧：已提供，按时间顺序排列，用于辅助分析画面内容。
    3. 分析要求：
       - 首先描述视频中实际出现的核心技术动作/操作流程（如网络布线、焊接、编程等）；
       - 评估技术动作的规范性、操作流程的合理性；
       - 指出操作中存在的问题或需要改进的地方；
       - 给出具体的、可落地的优化建议；
       - 统计视频时长（秒）、关键技术动作数量；
    4. 输出格式：严格的JSON字符串，包含以下字段：
       - analysis_summary（分析总结，200字以内）；
       - action_norm_score（技术动作规范性评分，0-100）；
       - improvement_suggestions（改进建议，列表形式）；
       - video_stats（视频统计：duration（时长）、action_count（关键技术动作数））；
       - key_frame_analysis（关键帧分析，简要描述）。
    """
    
    try:
        print("开始调用Qwen3.5-Plus...")
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    *[{"type": "image", "image": frame} for frame in key_frames_base64[:16]]
                ]
            }
        ]
        
        response = Generation.call(
            model="qwen-plus",
            api_key=DASHSCOPE_API_KEY,
            messages=messages,
            result_format="json",
            temperature=0.7,
            top_p=0.8
        )
        
        # 输出token消耗
        if response.status_code == 200:
            usage = response.usage
            print(f"Qwen3.5-Plus Token消耗: 输入={usage.input_tokens}, 输出={usage.output_tokens}, 总计={usage.total_tokens}")
            
            try:
                analysis_result = json.loads(response.output.choices[0].message.content)
            except json.JSONDecodeError as e:
                analysis_result = {
                    "analysis_summary": "大模型返回结果格式异常，无法解析",
                    "action_norm_score": 0,
                    "improvement_suggestions": ["解析大模型结果失败"],
                    "video_stats": {"duration": 0, "action_count": 0},
                    "key_frame_analysis": "解析失败"
                }
            return analysis_result
        else:
            print(f"大模型调用失败：{response.message}")
            return {
                "analysis_summary": f"大模型调用失败：{response.message}",
                "action_norm_score": 0,
                "improvement_suggestions": ["大模型调用失败"],
                "video_stats": {"duration": 0, "action_count": 0},
                "key_frame_analysis": "调用失败"
            }
    except Exception as e:
        print(f"调用Qwen3.5-Plus出错：{str(e)}")
        return {
            "analysis_summary": f"调用Qwen3.5-Plus出错：{str(e)}",
            "action_norm_score": 0,
            "improvement_suggestions": [f"调用出错：{str(e)}"],
            "video_stats": {"duration": 0, "action_count": 0},
            "key_frame_analysis": "调用出错"
        }

def save_analysis_record(username, filename, video_path, analysis_result):
    """保存分析记录到JSON文件"""
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    video_duration = round(total_frames / fps, 2) if fps and total_frames else 0
    cap.release()
    
    record = {
        "id": f"analysis_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
        "username": username,
        "video_filename": filename,
        "video_path": video_path.replace("\\", "/"),
        "video_duration": video_duration,
        "analysis_result": analysis_result,
        "analysis_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    record_file = os.path.join(ANALYSIS_DIR, f"{record['id']}.json")
    with open(record_file, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=4)
    
    return record

# ------------------- 视频上传接口 -------------------
@app.post("/api/video/upload")
async def upload_video(
    file: UploadFile = File(...),
    chunk: str = Form(None),
    chunks: str = Form(None),
    filename: str = Form(None),
    username: str = Form(...)
):
    ALLOWED_TYPES = ["video/mp4", "video/mov", "video/avi"]
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400, 
            detail=f"仅支持上传mp4/mov/avi格式视频，当前格式：{file.content_type}"
        )
    
    MAX_SIZE = 100 * 1024 * 1024
    file_size = await get_file_size(file)
    if file_size > MAX_SIZE:
        raise HTTPException(
            status_code=400, 
            detail=f"文件大小超过限制（最大100MB），当前大小：{round(file_size/1024/1024, 2)}MB"
        )
    
    if not filename:
        filename = file.filename or "unknown_video"
    unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    try:
        chunk_int = int(chunk) if chunk is not None else None
        chunks_int = int(chunks) if chunks is not None else None
    except (ValueError, TypeError):
        chunk_int = None
        chunks_int = None
    
    if chunk_int is not None and chunks_int is not None:
        temp_chunk_path = f"{file_path}.part{chunk_int}"
        with open(temp_chunk_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        if chunk_int == chunks_int - 1:
            with open(file_path, "wb") as final_file:
                for i in range(chunks_int):
                    part_path = f"{file_path}.part{i}"
                    if os.path.exists(part_path):
                        with open(part_path, "rb") as part_file:
                            final_file.write(part_file.read())
                        os.remove(part_path)
            status = "合并完成"
        else:
            status = f"分片{chunk_int+1}/{chunks_int}上传成功"
    else:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        status = "普通上传完成"
    
    return {
        "code": 200,
        "message": f"视频上传成功！{status}",
        "file_info": {
            "filename": unique_filename,
            "size_mb": round(file_size/1024/1024, 2),
            "save_path": file_path.replace("\\", "/")
        }
    }

# ------------------- 视频分析接口 -------------------
@app.post("/api/video/analyze")
async def analyze_video(analysis_req: AnalysisRequest = Body(...)):
    video_filename = analysis_req.filename
    username = analysis_req.username
    
    video_path = os.path.join(UPLOAD_DIR, video_filename)
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail=f"视频文件不存在：{video_filename}")
    
    # 1. 创建本次分析的媒体保存目录
    extract_dir_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{username}"
    extract_save_dir = os.path.join(MEDIA_EXTRACT_DIR, extract_dir_name)
    if not os.path.exists(extract_save_dir):
        os.makedirs(extract_save_dir)
    print(f"本次分析的媒体文件保存目录: {extract_save_dir}")
    
    # 2. 提取音频和关键帧
    video_text, is_audio_useful = extract_video_audio_text(video_path, extract_save_dir)
    key_frames = extract_video_key_frames(video_path, extract_save_dir, num_frames=16)
    
    # 3. 调用Qwen3.5-Plus
    analysis_result = call_qwen35(video_text, key_frames, username, is_audio_useful)
    
    # 4. 保存分析记录
    record = save_analysis_record(username, video_filename, video_path, analysis_result)
    
    return {
        "code": 200,
        "message": "视频分析完成",
        "analysis_record": record
    }

# ------------------- 获取历史分析记录 -------------------
@app.post("/api/video/analysis/history")
async def get_analysis_history(history_req: HistoryRequest = Body(...)):
    username = history_req.username
    records = []
    for file in os.listdir(ANALYSIS_DIR):
        if file.endswith(".json"):
            try:
                with open(os.path.join(ANALYSIS_DIR, file), "r", encoding="utf-8") as f:
                    record = json.load(f)
                    if record.get("username") == username:
                        records.append(record)
            except Exception as e:
                print(f"读取分析记录失败：{file}，错误：{str(e)}")
    
    records.sort(key=lambda x: x["analysis_time"], reverse=True)
    return {
        "code": 200,
        "history": records
    }

# ------------------- 辅助函数 -------------------
async def get_file_size(file: UploadFile):
    file.file.seek(0, os.SEEK_END)
    size = file.file.tell()
    file.file.seek(0)
    return size

# ------------------- 启动 -------------------
if __name__ == "__main__":
    uvicorn.run("main:app", reload=True, host="0.0.0.0", port=8000)