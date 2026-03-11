# api/projects/photoelectric.py
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Body
from datetime import datetime
import os
import shutil
import cv2
from config import ALLOWED_VIDEO_TYPES, MAX_VIDEO_SIZE, UPLOAD_DIR, MEDIA_EXTRACT_DIR, PRESET_PHOTOELECTRIC_PROJECTS
from models import (
    AnalysisRequest, HistoryRequest, CreateTrainingDayRequest,
    ProjectAnalyzeRequest, TrainingDaySummaryRequest, TrainingDayIdRequest
)
from video_utils import get_file_size, extract_video_audio_text, extract_video_key_frames
from llm_utils import call_qwen35, call_qwen_project_analysis, call_qwen_training_summary
from record_utils import save_analysis_record, get_analysis_history
from training_utils import (
    create_training_day, get_user_training_day_list,
    get_training_day, update_project_analysis, update_training_day_summary
)

# 路由前缀：/api/photoelectric（区分项目）
router = APIRouter(prefix="/api/photoelectric", tags=["光电项目"])


# ------------------- 获取历史分析记录 -------------------
@router.post("/video/analysis/history")
async def get_analysis_history_api(history_req: HistoryRequest = Body(...)):
    username = history_req.username
    records = get_analysis_history(username)
    return {
        "code": 200,
        "history": records
    }


# ------------------- 光电项目视频上传 -------------------
@router.post("/video/upload")
async def upload_video_photoelectric(
    file: UploadFile = File(...),
    chunk: str = Form(None),
    chunks: str = Form(None),
    filename: str = Form(None),
    username: str = Form(...)
):
    # 复制原main.py中 /api/photoelectric/video/upload 的所有代码（完全不变）
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

# ------------------- 光电项目训练日创建 -------------------
@router.post("/training/day/create")
async def create_training_day_photoelectric(req: CreateTrainingDayRequest = Body(...)):
    # 复制原main.py中 /api/training/photoelectric/day/create 的所有代码
    try:
        training_day_data = create_training_day(req)
        return {
            "code": 200,
            "message": "训练日创建成功",
            "training_day_data": training_day_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建训练日失败：{str(e)}")

# ------------------- 光电项目训练日列表 -------------------
@router.post("/training/day/list")
async def get_training_day_list_photoelectric(req: HistoryRequest = Body(...)):
    # 复制原main.py中 /api/training/photoelectric/day/list 的所有代码
    try:
        list_data = get_user_training_day_list(req.username)
        return {
            "code": 200,
            "list": list_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取训练日列表失败：{str(e)}")

# ------------------- 光电项目训练日详情 -------------------
@router.post("/training/day/detail")
async def get_training_day_detail_photoelectric(req: TrainingDayIdRequest = Body(...)):
    # 复制原main.py中 /api/training/photoelectric/day/detail 的所有代码
    training_day = get_training_day(req.training_day_id, req.username)
    if not training_day:
        raise HTTPException(status_code=404, detail="训练日不存在或无权限")
    return {
        "code": 200,
        "detail": training_day
    }

# ------------------- 光电项目专项分析 -------------------
@router.post("/training/project/analyze")
async def project_analyze_photoelectric(req: ProjectAnalyzeRequest = Body(...)):
    # 复制原main.py中 /api/training/photoelectric/project/analyze 的所有代码
    training_day = get_training_day(req.training_day_id, req.username)
    if not training_day:
        raise HTTPException(status_code=404, detail="训练日不存在或无权限")
    target_project = None
    for project in training_day["project_list"]:
        if project["project_id"] == req.project_id:
            target_project = project
            break
    if not target_project:
        raise HTTPException(status_code=404, detail="项目不存在")
    video_path = os.path.join(UPLOAD_DIR, req.filename)
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="视频文件不存在")
    extract_dir_name = f"{req.training_day_id}_{req.project_id}"
    extract_save_dir = os.path.join(MEDIA_EXTRACT_DIR, extract_dir_name)
    if not os.path.exists(extract_save_dir):
        os.makedirs(extract_save_dir)
    video_text, is_audio_useful = extract_video_audio_text(video_path, extract_save_dir)
    key_frames = extract_video_key_frames(video_path, extract_save_dir, num_frames=16)
    analysis_result = call_qwen_project_analysis(
        project_name=target_project["project_name"],
        project_desc=target_project["project_desc"],
        video_text=video_text,
        key_frames_base64=key_frames,
        username=req.username,
        is_audio_useful=is_audio_useful
    )
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    video_duration = round(total_frames / fps, 2) if fps and total_frames else 0
    cap.release()
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

# ------------------- 光电项目训练日汇总 -------------------
@router.post("/training/day/summary")
async def training_day_summary_photoelectric(req: TrainingDaySummaryRequest = Body(...)):
    # 复制原main.py中 /api/training/photoelectric/day/summary 的所有代码
    training_day = get_training_day(req.training_day_id, req.username)
    if not training_day:
        raise HTTPException(status_code=404, detail="训练日不存在或无权限")
    all_finished = all([p["is_analyzed"] for p in training_day["project_list"]])
    if not all_finished:
        raise HTTPException(status_code=400, detail="还有项目未完成分析，无法生成整体汇总")
    summary_result = call_qwen_training_summary(training_day, req.username)
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

# ------------------- 光电项目预设项目列表 -------------------
@router.get("/training/project/preset")
async def get_preset_projects_photoelectric():
    # 复制原main.py中 /api/training/photoelectric/project/preset 的所有代码
    return {
        "code": 200,
        "preset_projects": PRESET_PHOTOELECTRIC_PROJECTS
    }