import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException, Body, Form
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import jwt
import os
import shutil

# 导入拆分后的模块
from config import (
    FAKE_USERS, UPLOAD_DIR, MEDIA_EXTRACT_DIR,
    ALLOWED_VIDEO_TYPES, MAX_VIDEO_SIZE
)
from models import LoginRequest, AnalysisRequest, HistoryRequest
from video_utils import (
    extract_video_audio_text, extract_video_key_frames, get_file_size
)
from llm_utils import call_qwen35
from record_utils import save_analysis_record, get_analysis_history

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

# ------------------- 视频上传接口 -------------------
@app.post("/api/video/upload")
async def upload_video(
    file: UploadFile = File(...),
    chunk: str = Form(None),
    chunks: str = Form(None),
    filename: str = Form(None),
    username: str = Form(...)
):
    if file.content_type not in ALLOWED_VIDEO_TYPES:
        raise HTTPException(
            status_code=400, 
            detail=f"仅支持上传mp4/mov/avi格式视频，当前格式：{file.content_type}"
        )
    
    file_size = await get_file_size(file)
    if file_size > MAX_VIDEO_SIZE:
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
async def get_analysis_history_api(history_req: HistoryRequest = Body(...)):
    username = history_req.username
    records = get_analysis_history(username)
    return {
        "code": 200,
        "history": records
    }


# ------------------- 新增：训练日相关接口 -------------------
from models import (
    CreateTrainingDayRequest, ProjectAnalyzeRequest,
    TrainingDaySummaryRequest, TrainingDayIdRequest
)
from training_utils import (
    create_training_day, get_user_training_day_list,
    get_training_day, update_project_analysis,
    update_training_day_summary
)
from video_utils import extract_video_audio_text, extract_video_key_frames
from llm_utils import call_qwen_project_analysis, call_qwen_training_summary
import cv2

# 1. 创建新训练日
@app.post("/api/training/day/create")
async def create_training_day_api(req: CreateTrainingDayRequest = Body(...)):
    try:
        training_day_data = create_training_day(req)
        return {
            "code": 200,
            "message": "训练日创建成功",
            "training_day_data": training_day_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建训练日失败：{str(e)}")

# 2. 获取用户的训练日列表
@app.post("/api/training/day/list")
async def get_training_day_list_api(req: HistoryRequest = Body(...)):
    try:
        list_data = get_user_training_day_list(req.username)
        return {
            "code": 200,
            "list": list_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取训练日列表失败：{str(e)}")

# 3. 获取训练日详情
@app.post("/api/training/day/detail")
async def get_training_day_detail_api(req: TrainingDayIdRequest = Body(...)):
    training_day = get_training_day(req.training_day_id, req.username)
    if not training_day:
        raise HTTPException(status_code=404, detail="训练日不存在或无权限")
    return {
        "code": 200,
        "detail": training_day
    }

# 4. 单个项目视频分析
@app.post("/api/training/project/analyze")
async def project_analyze_api(req: ProjectAnalyzeRequest = Body(...)):
    # 1. 校验训练日和项目
    training_day = get_training_day(req.training_day_id, req.username)
    if not training_day:
        raise HTTPException(status_code=404, detail="训练日不存在或无权限")
    
    # 找到对应项目
    target_project = None
    for project in training_day["project_list"]:
        if project["project_id"] == req.project_id:
            target_project = project
            break
    if not target_project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 2. 校验视频文件
    video_path = os.path.join(UPLOAD_DIR, req.filename)
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="视频文件不存在")
    
    # 3. 创建媒体保存目录
    extract_dir_name = f"{req.training_day_id}_{req.project_id}"
    extract_save_dir = os.path.join(MEDIA_EXTRACT_DIR, extract_dir_name)
    if not os.path.exists(extract_save_dir):
        os.makedirs(extract_save_dir)
    
    # 4. 提取音频和关键帧（复用原有工具函数）
    video_text, is_audio_useful = extract_video_audio_text(video_path, extract_save_dir)
    key_frames = extract_video_key_frames(video_path, extract_save_dir, num_frames=16)
    
    # 5. 调用大模型专项分析
    analysis_result = call_qwen_project_analysis(
        project_name=target_project["project_name"],
        project_desc=target_project["project_desc"],
        video_text=video_text,
        key_frames_base64=key_frames,
        username=req.username,
        is_audio_useful=is_audio_useful
    )
    
    # 6. 获取视频时长
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    video_duration = round(total_frames / fps, 2) if fps and total_frames else 0
    cap.release()
    
    # 7. 更新项目数据
    success, result = update_project_analysis(
        training_day_id=req.training_day_id,
        project_id=req.project_id,
        username=req.username,
        video_info={"filename": req.filename, "duration": video_duration},
        analysis_result=analysis_result
    )
    
    if not success:
        raise HTTPException(status_code=500, detail=result)
    
    return {
        "code": 200,
        "message": "项目分析完成",
        "training_day_data": result,
        "project_analysis": analysis_result
    }

# 5. 生成训练日整体汇总报告
@app.post("/api/training/day/summary")
async def training_day_summary_api(req: TrainingDaySummaryRequest = Body(...)):
    # 1. 校验训练日
    training_day = get_training_day(req.training_day_id, req.username)
    if not training_day:
        raise HTTPException(status_code=404, detail="训练日不存在或无权限")
    
    # 2. 校验是否全部项目完成
    all_finished = all([p["is_analyzed"] for p in training_day["project_list"]])
    if not all_finished:
        raise HTTPException(status_code=400, detail="还有项目未完成分析，无法生成整体汇总")
    
    # 3. 调用大模型生成汇总
    summary_result = call_qwen_training_summary(training_day, req.username)
    
    # 4. 更新训练日数据
    success, result = update_training_day_summary(
        training_day_id=req.training_day_id,
        username=req.username,
        overall_analysis=summary_result
    )
    
    if not success:
        raise HTTPException(status_code=500, detail=result)
    
    return {
        "code": 200,
        "message": "整体汇总生成完成",
        "training_day_data": result,
        "summary_result": summary_result
    }

# 6. 获取预设项目列表
@app.get("/api/training/project/preset")
async def get_preset_projects_api():
    from config import PRESET_PROJECTS
    return {
        "code": 200,
        "preset_projects": PRESET_PROJECTS
    }


# ------------------- 注册静态资源路由 -------------------
from static_resource import static_router, mount_static_resources

# 挂载静态资源目录
mount_static_resources(app)
# 注册静态资源接口
app.include_router(static_router)



# ------------------- 启动 -------------------
if __name__ == "__main__":
    uvicorn.run("main:app", reload=True, host="0.0.0.0", port=8000)