import os
import subprocess
import cv2
import base64
from PIL import Image
from io import BytesIO
from fastapi import UploadFile
from config import WHISPER_MODEL, FFMPEG_PATH

# 新增：规范化文件名（移除特殊字符、中文，避免路径问题）
def normalize_filename(filename):
    """
    规范化文件名：移除中文、特殊字符，仅保留字母/数字/下划线/横线
    解决Windows路径编码问题
    """
    import re
    # 移除中文
    filename = re.sub(r'[^\x00-\x7F]+', '', filename)
    # 移除特殊字符（保留字母、数字、下划线、横线、点）
    filename = re.sub(r'[^\w\-\.]', '_', filename)
    return filename

def extract_video_audio_text(video_path, save_dir):
    """提取视频音频并转文字，同时保存音频文件"""
    try:
        print(f"开始提取音频文本: {video_path}")
        # 1. 保存音频文件到指定目录
        audio_filename = os.path.basename(video_path).replace('.MP4', '.wav').replace('.mp4', '.wav')
        # 规范化音频文件名
        audio_filename = normalize_filename(audio_filename)
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
        text_filename = normalize_filename(text_filename)
        text_save_path = os.path.join(save_dir, text_filename)
        with open(text_save_path, "w", encoding="utf-8") as f:
            f.write(audio_text)
        
        return audio_text, is_audio_useful
    except Exception as e:
        error_msg = f"音频转文字失败：{str(e)}"
        print(error_msg)
        return "", False

def extract_video_key_frames(video_path, save_dir, num_frames=16):
    """提取视频关键帧，保存到指定目录，返回带data:image前缀的base64列表（修复Windows路径编码问题）"""
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

    # 创建关键帧保存子目录（规范化目录名，避免中文/特殊字符）
    video_name = os.path.basename(video_path).replace('.MP4', '').replace('.mp4', '')
    video_name = normalize_filename(video_name)  # 关键：规范化视频名
    frame_save_dir = os.path.join(save_dir, f"{video_name}_frames")
    
    # 确保目录存在（强制创建，避免路径问题）
    os.makedirs(frame_save_dir, exist_ok=True)
    print(f"关键帧保存目录（规范化后）: {frame_save_dir}")

    for i in range(num_frames):
        cap.set(cv2.CAP_PROP_POS_FRAMES, i * frame_interval)
        ret, frame = cap.read()
        if not ret:
            print(f"读取第 {i} 帧失败")
            break
        
        # 1. 规范化帧文件名
        frame_filename = f"frame_{i:03d}.jpg"
        frame_save_path = os.path.join(frame_save_dir, frame_filename)
        
        # 2. 修复Windows下OpenCV保存中文路径问题：先保存到内存，再用PIL写入（绕过cv2.imwrite的编码问题）
        try:
            # 方法1：用PIL保存（兼容中文/特殊路径）
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            # 保存图片（带质量压缩）
            img.save(frame_save_path, format="JPEG", quality=80)
            
            # 校验文件是否真的保存成功
            if not os.path.exists(frame_save_path):
                raise Exception(f"图片保存后不存在：{frame_save_path}")
            
            # 3. 转换为带data:image前缀的base64（核心修改：解决Qwen3.5-Plus URL无效问题）
            buffer = BytesIO()
            img.save(buffer, format="JPEG", quality=80)
            buffer.seek(0)
            # 第一步：生成纯base64编码
            pure_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
            # 第二步：拼接data:image前缀（Qwen3.5-Plus必须的格式）
            complete_base64 = f"data:image/jpg;base64,{pure_base64}"
            
            # 校验base64有效性（包含前缀后的长度校验）
            if len(complete_base64) < 200:  # 带前缀后长度至少200，避免无效编码
                print(f"第 {i} 帧base64编码无效（带前缀后长度：{len(complete_base64)}），跳过")
                continue
            
            key_frames_base64.append(complete_base64)
            print(f"✅ 成功提取第 {i} 帧（带前缀base64长度：{len(complete_base64)}），实际保存路径: {frame_save_path}")
            print(f"   文件大小: {os.path.getsize(frame_save_path) / 1024:.2f} KB")  # 验证文件大小
            print(f"   base64前缀校验: {complete_base64[:30]}...")  # 新增：验证前缀是否正确
        
        except Exception as e:
            print(f"❌ 第 {i} 帧保存失败：{str(e)}")
            continue

    cap.release()
    
    # 最终校验：打印目录下的文件列表
    try:
        saved_files = os.listdir(frame_save_dir)
        print(f"\n关键帧提取完成：")
        print(f"- 有效base64数量：{len(key_frames_base64)} / {num_frames}")
        print(f"- 保存目录实际文件数：{len(saved_files)}")
        print(f"- 目录下文件列表：{saved_files[:5]}..." if len(saved_files) >5 else f"- 目录下文件列表：{saved_files}")
    except Exception as e:
        print(f"读取关键帧目录失败：{str(e)}")
    
    # 兜底：如果无有效关键帧，返回空列表并提示
    if len(key_frames_base64) == 0:
        print("⚠️ 警告：未生成任何有效关键帧base64！")
    
    return key_frames_base64

async def get_file_size(file: UploadFile):
    """获取上传文件的大小（字节）"""
    file.file.seek(0, os.SEEK_END)
    size = file.file.tell()
    file.file.seek(0)
    return size