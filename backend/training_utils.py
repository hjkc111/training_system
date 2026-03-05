"""
训练日业务逻辑工具函数
包含训练日的创建、查询、数据更新、状态管理等核心逻辑
"""
import os
import json
from datetime import datetime

# 同样用兼容写法，和models.py保持一致
try:
    from typing import List
except ImportError:
    from typing_extensions import List

from config import TRAINING_DAY_DIR, PRESET_PROJECTS
from models import TrainingProject, CreateTrainingDayRequest
# ------------------- 训练日基础操作 -------------------
def create_training_day(req: CreateTrainingDayRequest):
    """创建新的训练日"""
    # 生成训练日唯一ID
    training_day_id = f"training_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    # 确定项目列表：自定义优先，否则用预设
    project_list = req.custom_projects if req.custom_projects else [
        TrainingProject(
            project_id=item["project_id"],
            project_name=item["project_name"],
            project_desc=item["project_desc"],
            project_order=idx+1
        ) for idx, item in enumerate(PRESET_PROJECTS)
    ]

    # 训练日基础数据
    training_day_data = {
        "training_day_id": training_day_id,
        "username": req.username,
        "training_day_name": req.training_day_name,
        "project_list": [p.model_dump() for p in project_list],
        "total_duration": 0,  # 总时长（所有项目视频时长之和）
        "overall_score": 0,  # 整体评分
        "overall_analysis": None,  # 整体汇总分析结果
        "created_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "finished_time": None,  # 完成时间
        "is_finished": False  # 是否全部完成
    }

    # 保存到文件
    save_path = os.path.join(TRAINING_DAY_DIR, f"{training_day_id}.json")
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(training_day_data, f, ensure_ascii=False, indent=4)
    
    return training_day_data

def get_training_day(training_day_id: str, username: str):
    """获取训练日详情，校验所属用户"""
    file_path = os.path.join(TRAINING_DAY_DIR, f"{training_day_id}.json")
    if not os.path.exists(file_path):
        return None
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if data.get("username") != username:
                return None
            return data
    except Exception as e:
        print(f"读取训练日失败：{str(e)}")
        return None

def save_training_day(training_day_data: dict):
    """保存训练日数据到文件"""
    save_path = os.path.join(TRAINING_DAY_DIR, f"{training_day_data['training_day_id']}.json")
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(training_day_data, f, ensure_ascii=False, indent=4)
    return True

def get_user_training_day_list(username: str):
    """获取用户的所有训练日列表"""
    training_list = []
    for file in os.listdir(TRAINING_DAY_DIR):
        if file.endswith(".json") and file.startswith("training_"):
            try:
                with open(os.path.join(TRAINING_DAY_DIR, file), "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("username") == username:
                        training_list.append({
                            "training_day_id": data["training_day_id"],
                            "training_day_name": data["training_day_name"],
                            "created_time": data["created_time"],
                            "is_finished": data["is_finished"],
                            "overall_score": data["overall_score"],
                            "project_count": len(data["project_list"]),
                            "finished_project_count": len([p for p in data["project_list"] if p["is_analyzed"]])
                        })
            except Exception as e:
                print(f"读取训练日列表失败：{file}，错误：{str(e)}")
    # 按创建时间倒序
    training_list.sort(key=lambda x: x["created_time"], reverse=True)
    return training_list

# ------------------- 项目数据更新 -------------------
def update_project_analysis(training_day_id: str, project_id: str, username: str, video_info: dict, analysis_result: dict):
    """更新项目的视频信息和分析结果"""
    training_day = get_training_day(training_day_id, username)
    if not training_day:
        return False, "训练日不存在或无权限"
    
    # 找到对应项目
    project_idx = None
    for idx, project in enumerate(training_day["project_list"]):
        if project["project_id"] == project_id:
            project_idx = idx
            break
    if project_idx is None:
        return False, "项目不存在"
    
    # 更新项目数据
    training_day["project_list"][project_idx]["video_filename"] = video_info.get("filename")
    training_day["project_list"][project_idx]["video_duration"] = video_info.get("duration", 0)
    training_day["project_list"][project_idx]["analysis_result"] = analysis_result
    training_day["project_list"][project_idx]["upload_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    training_day["project_list"][project_idx]["is_analyzed"] = True

    # 重新计算总时长
    total_duration = sum([p.get("video_duration", 0) for p in training_day["project_list"] if p["is_analyzed"]])
    training_day["total_duration"] = round(total_duration, 2)

    # 检查是否全部项目完成
    all_finished = all([p["is_analyzed"] for p in training_day["project_list"]])
    if all_finished:
        training_day["is_finished"] = True
        training_day["finished_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 保存数据
    save_training_day(training_day)
    return True, training_day

def update_training_day_summary(training_day_id: str, username: str, overall_analysis: dict):
    """更新训练日的整体汇总分析"""
    training_day = get_training_day(training_day_id, username)
    if not training_day:
        return False, "训练日不存在或无权限"
    
    training_day["overall_analysis"] = overall_analysis
    training_day["overall_score"] = overall_analysis.get("overall_score", 0)
    save_training_day(training_day)
    return True, training_day