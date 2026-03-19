# api/projects/network.py
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Body
from datetime import datetime
import os
import shutil
import cv2
import base64
import fitz  # PyMuPDF，用于PDF解析
from PIL import Image  # Pillow，用于图片处理
from config import ALLOWED_VIDEO_TYPES, MAX_VIDEO_SIZE, UPLOAD_DIR, MEDIA_EXTRACT_DIR, PRESET_PROJECTS,PRESET_NETWORK_PROJECTS
from models import (
    AnalysisRequest, HistoryRequest, CreateTrainingDayRequest,
    ProjectAnalyzeRequest, TrainingDaySummaryRequest, TrainingDayIdRequest
)
from utils.video_utils import get_file_size, extract_video_audio_text, extract_video_key_frames
from utils.llm_utils import call_qwen35, call_qwen_project_analysis_network, call_qwen_training_summary
from utils.record_utils import save_analysis_record, get_analysis_history
from utils.training_utils import (
    create_training_day, get_user_training_day_list,
    get_training_day, update_project_analysis, update_training_day_summary
)

import re
from typing_extensions import List, Dict, Optional



# ------------------- 配置补充 -------------------
ALLOWED_DOC_TYPES = ["text/plain", "application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
MAX_DOC_SIZE = 20 * 1024 * 1024  # 20MB
ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/jpg"]
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_STEP_SCREENSHOTS = 10  # 最多10张步骤截图

# 路由前缀：/api/network（区分项目，避免接口冲突）
router = APIRouter(prefix="/api/network", tags=["网络布线项目"])


# ------------------- 获取历史分析记录 -------------------
@router.post("/video/analysis/history")
async def get_analysis_history_api(history_req: HistoryRequest = Body(...)):
    username = history_req.username
    records = get_analysis_history(username)
    return {
        "code": 200,
        "history": records
    }


# ------------------- 网络布线项目视频上传 -------------------
@router.post("/video/upload")
async def upload_video_network(
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

# ------------------- 网络布线视频分析（原有接口保留） -------------------
@router.post("/video/analyze")
async def analyze_video_network(analysis_req: AnalysisRequest = Body(...)):
    video_filename = analysis_req.filename
    username = analysis_req.username
    video_path = os.path.join(UPLOAD_DIR, video_filename)
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail=f"视频文件不存在：{video_filename}")
    extract_dir_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{username}"
    extract_save_dir = os.path.join(MEDIA_EXTRACT_DIR, extract_dir_name)
    if not os.path.exists(extract_save_dir):
        os.makedirs(extract_save_dir)
    print(f"本次分析的媒体文件保存目录: {extract_save_dir}")
    video_text, is_audio_useful = extract_video_audio_text(video_path, extract_save_dir)
    key_frames = extract_video_key_frames(video_path, extract_save_dir, num_frames=16)
    analysis_result = call_qwen35(video_text, key_frames, username, is_audio_useful)
    record = save_analysis_record(username, video_filename, video_path, analysis_result)
    return {
        "code": 200,
        "message": "视频分析完成",
        "analysis_record": record
    }

# ------------------- 网络布线项目训练日创建 -------------------
@router.post("/training/day/create")
async def create_training_day_network(req: CreateTrainingDayRequest = Body(...)):
    try:
        req.project_type = "network"  # 强制标记为网络布线项目
        training_day_data = create_training_day(req)
        return {
            "code": 200,
            "message": "网络布线训练日创建成功",
            "training_day_data": training_day_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"网络布线创建训练日失败：{str(e)}")

# ------------------- 网络布线项目训练日列表 -------------------
@router.post("/training/day/list")
async def get_training_day_list_network(req: HistoryRequest = Body(...)):
    try:
        list_data = get_user_training_day_list(req.username, project_type="network")
        return {
            "code": 200,
            "list": list_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取训练日列表失败：{str(e)}")

# ------------------- 网络布线项目训练日详情 -------------------
@router.post("/training/day/detail")
async def get_training_day_detail_network(req: TrainingDayIdRequest = Body(...)):
    training_day = get_training_day(req.training_day_id, req.username)
    if not training_day:
        raise HTTPException(status_code=404, detail="训练日不存在或无权限")
    if training_day.get("project_type") != "network":
        raise HTTPException(status_code=403, detail="无权限访问非网络布线项目训练日")
    return {
        "code": 200,
        "detail": training_day
    }

# ------------------- 网络布线项目专项分析 -------------------
@router.post("/training/project/analyze")
async def project_analyze_network(req: ProjectAnalyzeRequest = Body(...)):
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
    analysis_result = call_qwen_project_analysis_network(
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

# ------------------- 网络布线项目训练日汇总 -------------------
@router.post("/training/day/summary")
async def training_day_summary_network(req: TrainingDaySummaryRequest = Body(...)):
    training_day = get_training_day(req.training_day_id, req.username)
    if not training_day:
        raise HTTPException(status_code=404, detail="训练日不存在或无权限")
    if training_day.get("project_type") != "network":
        raise HTTPException(status_code=403, detail="无权限访问非网络布线项目训练日")
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

# ------------------- 网络布线项目预设项目列表 -------------------
@router.get("/training/project/preset")
async def get_preset_projects_network():
    return {
        "code": 200,
        "preset_projects": PRESET_NETWORK_PROJECTS
    }

# ------------------- 网络布线项目文档上传 -------------------
@router.post("/doc/upload")
async def doc_upload_network(
    file: UploadFile = File(...),
    chunk: str = Form(None),
    chunks: str = Form(None),
    filename: str = Form(None),
    username: str = Form(...),
    project_id: str = Form(...)
):
    # 文档格式校验
    if file.content_type not in ALLOWED_DOC_TYPES:
        raise HTTPException(
            status_code=400, 
            detail=f"仅支持上传txt/pdf/docx格式文档，当前格式：{file.content_type}"
        )
    file_size = await get_file_size(file)
    if file_size > MAX_DOC_SIZE:
        raise HTTPException(
            status_code=400, 
            detail=f"文档大小超过限制（最大20MB），当前大小：{round(file_size/1024/1024, 2)}MB"
        )
    if not filename:
        filename = file.filename or "unknown_doc"
    # 生成唯一文件名（包含项目ID）
    unique_filename = f"{project_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    # 分片上传逻辑（和视频上传完全一致）
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
            status = "文档分片合并完成"
        else:
            status = f"文档分片{chunk_int+1}/{chunks_int}上传成功"
    else:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        status = "文档普通上传完成"
    
    return {
        "code": 200,
        "message": f"文档上传成功！{status}",
        "file_info": {
            "filename": unique_filename,
            "size_mb": round(file_size/1024/1024, 2),
            "save_path": file_path.replace("\\", "/")
        }
    }

# ------------------- 网络布线项目图片上传（用户操作图/步骤截图） -------------------
@router.post("/image/upload")
async def image_upload_network(
    file: UploadFile = File(...),
    chunk: str = Form(None),
    chunks: str = Form(None),
    filename: str = Form(None),
    username: str = Form(...),
    project_id: str = Form(...),
    type: str = Form("user")  # user:用户操作图, step:步骤截图
):
    # 图片格式校验
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400, 
            detail=f"仅支持上传jpg/png/jpeg格式图片，当前格式：{file.content_type}"
        )
    file_size = await get_file_size(file)
    if file_size > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=400, 
            detail=f"图片大小超过限制（最大5MB），当前大小：{round(file_size/1024/1024, 2)}MB"
        )
    if not filename:
        filename = file.filename or "unknown_image"
    # 生成唯一文件名（包含项目ID和类型）
    unique_filename = f"{project_id}_{type}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    # 分片上传逻辑
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
            status = "图片分片合并完成"
        else:
            status = f"图片分片{chunk_int+1}/{chunks_int}上传成功"
    else:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        status = "图片普通上传完成"
    
    return {
        "code": 200,
        "message": f"图片上传成功！{status}",
        "file_info": {
            "filename": unique_filename,
            "size_mb": round(file_size/1024/1024, 2),
            "save_path": file_path.replace("\\", "/")
        }
    }

# ------------------- 网络布线项目步骤截图上传（复用图片上传逻辑，仅做数量校验） -------------------
@router.post("/step/screenshot/upload")
async def step_screenshot_upload_network(
    file: UploadFile = File(...),
    chunk: str = Form(None),
    chunks: str = Form(None),
    filename: str = Form(None),
    username: str = Form(...),
    project_id: str = Form(...)
):
    # 先校验当前项目已上传的截图数量
    project_screenshot_dir = os.path.join(UPLOAD_DIR, f"{project_id}_step_")
    existing_screenshots = [f for f in os.listdir(UPLOAD_DIR) if f.startswith(f"{project_id}_step_")]
    if len(existing_screenshots) >= MAX_STEP_SCREENSHOTS:
        raise HTTPException(
            status_code=400, 
            detail=f"步骤截图最多上传{MAX_STEP_SCREENSHOTS}张，当前已上传{len(existing_screenshots)}张"
        )
    
    # 复用图片上传逻辑，指定type=step
    return await image_upload_network(
        file=file,
        chunk=chunk,
        chunks=chunks,
        filename=filename,
        username=username,
        project_id=project_id,
        type="step"
    )

# ------------------- 网络布线项目文档分析接口 -------------------
@router.post("/training/project/analyze/doc")
async def project_analyze_doc_network(req: ProjectAnalyzeRequest = Body(...)):
    # 基础校验（和视频分析一致）
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
    
    # 读取文档内容
    doc_path = os.path.join(UPLOAD_DIR, req.filename)
    if not os.path.exists(doc_path):
        raise HTTPException(status_code=404, detail="文档文件不存在")
    
    doc_content = ""
    try:
        # 根据文档类型解析内容
        if doc_path.endswith(".txt"):
            with open(doc_path, "r", encoding="utf-8") as f:
                doc_content = f.read()
        elif doc_path.endswith(".pdf"):
            doc = fitz.open(doc_path)
            for page in doc:
                doc_content += page.get_text()
            doc.close()
        elif doc_path.endswith(".docx"):
            # 简易docx解析（如需完整解析可安装python-docx）
            import zipfile
            with zipfile.ZipFile(doc_path) as zf:
                doc_content = zf.read("word/document.xml").decode("utf-8")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"解析文档失败：{str(e)}")
    
    # 调用大模型分析文档
    analysis_result = call_qwen_project_analysis_network(
        project_name=target_project["project_name"],
        project_desc=target_project["project_desc"],
        video_text=doc_content,  # 文档内容传入video_text字段（复用函数）
        key_frames_base64=[],    # 无图片，传空列表
        username=req.username,
        is_audio_useful=False
    )
    
    # 更新项目分析结果（复用原有逻辑）
    success, result = update_project_analysis(
        training_day_id=req.training_day_id,
        project_id=req.project_id,
        username=req.username,
        video_info={"filename": req.filename, "duration": 0},  # 文档无时长
        analysis_result=analysis_result
    )
    if not success:
        raise HTTPException(status_code=500, detail=result)
    
    return {
        "code": 200,
        "message": "文档分析完成",
        "training_day_data": result,
        "project_analysis": analysis_result
    }

# ------------------- 网络布线项目图片对比分析接口 -------------------
@router.post("/training/project/analyze/image")
async def project_analyze_image_network(
    training_day_id: str = Body(...),
    project_id: str = Body(...),
    user_image_filename: str = Body(...),
    username: str = Body(...)
):
    # 基础校验
    training_day = get_training_day(training_day_id, username)
    if not training_day:
        raise HTTPException(status_code=404, detail="训练日不存在或无权限")
    target_project = None
    for project in training_day["project_list"]:
        if project["project_id"] == project_id:
            target_project = project
            break
    if not target_project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 读取用户图片并转为base64
    user_image_path = os.path.join(UPLOAD_DIR, user_image_filename)
    if not os.path.exists(user_image_path):
        raise HTTPException(status_code=404, detail="用户操作图片不存在")
    
    # 读取标准图片（从预设项目中获取）
    standard_image_url = target_project.get("standard_image_url", "")
    standard_image_base64 = ""
    if standard_image_url and os.path.exists(standard_image_url):
        with open(standard_image_url, "rb") as f:
            standard_image_base64 = base64.b64encode(f.read()).decode("utf-8")
    
    # 读取用户图片base64
    with open(user_image_path, "rb") as f:
        user_image_base64 = base64.b64encode(f.read()).decode("utf-8")
    
    # 调用大模型对比分析（传入两张图片）
    analysis_result = call_qwen_project_analysis_network(
        project_name=target_project["project_name"],
        project_desc=target_project["project_desc"],
        video_text=f"用户操作图片对比标准图片分析，标准图URL：{standard_image_url}",
        key_frames_base64=[user_image_base64, standard_image_base64],  # 传入两张图
        username=username,
        is_audio_useful=False
    )
    
    # 更新项目分析结果
    success, result = update_project_analysis(
        training_day_id=training_day_id,
        project_id=project_id,
        username=username,
        video_info={"filename": user_image_filename, "duration": 0},
        analysis_result=analysis_result
    )
    if not success:
        raise HTTPException(status_code=500, detail=result)
    
    return {
        "code": 200,
        "message": "图片对比分析完成",
        "training_day_data": result,
        "project_analysis": analysis_result
    }

# ------------------- 网络布线项目步骤截图分析接口 -------------------
@router.post("/training/project/analyze/step")
async def project_analyze_step_network(
    training_day_id: str = Body(...),
    project_id: str = Body(...),
    image_base64_list: list = Body(...),  # 改动1：接收前端传的Base64列表（替代filenames）
    username: str = Body(...),
    # 可选：接收项目名称/描述（前端传的话）
    project_name: str = Body(None),
    project_desc: str = Body(None)
):
    # 基础校验（保留原有逻辑）
    training_day = get_training_day(training_day_id, username)
    if not training_day:
        raise HTTPException(status_code=404, detail="训练日不存在或无权限")
    target_project = None
    for project in training_day["project_list"]:
        if project["project_id"] == project_id:
            target_project = project
            break
    if not target_project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 改动2：处理前端传的Base64列表（剥离data:image前缀，保留纯Base64）
    step_images_base64 = []
    for base64_str in image_base64_list:
        if not isinstance(base64_str, str) or not base64_str.strip():
            continue  # 过滤空值
        
        # 解析Data URL格式的Base64（data:image/jpeg;base64,xxxx）
        base64_pattern = r"data:image/[a-zA-Z0-9]+;base64,(.+)"
        match = re.match(base64_pattern, base64_str.strip())
        if match:
            # 提取纯Base64部分
            pure_base64 = match.group(1)
            step_images_base64.append(pure_base64)
        else:
            # 兼容纯Base64（无前缀）的情况
            step_images_base64.append(base64_str.strip())
    
    # 校验有效Base64数量
    if len(step_images_base64) == 0:
        raise HTTPException(status_code=400, detail="无有效步骤截图Base64数据")
    if len(step_images_base64) > MAX_STEP_SCREENSHOTS:
        raise HTTPException(status_code=400, detail=f"步骤截图最多上传{MAX_STEP_SCREENSHOTS}张")
    
    # 调用大模型分析（保留原有逻辑，传入处理后的纯Base64列表）
    # 优先用前端传的project_name/desc，没有则用训练日里的
    final_project_name = project_name or target_project["project_name"]
    final_project_desc = project_desc or target_project["project_desc"]
    
    analysis_result = call_qwen_project_analysis_network(
        project_name=final_project_name,
        project_desc=final_project_desc,
        video_text="分析关键步骤截图的完整性、规范性、操作顺序",
        key_frames_base64=step_images_base64[:8],  # 最多传8张（大模型限制）
        username=username,
        is_audio_useful=False
    )
    
    # 更新项目分析结果（保留原有逻辑）
    success, result = update_project_analysis(
        training_day_id=training_day_id,
        project_id=project_id,
        username=username,
        video_info={"filename": f"step_screenshots_{len(step_images_base64)}_imgs", "duration": 0},
        analysis_result=analysis_result
    )
    if not success:
        raise HTTPException(status_code=500, detail=result)
    
    return {
        "code": 200,
        "message": "步骤截图分析完成",
        "training_day_data": result,
        "project_analysis": analysis_result
    }