import os
import json
from datetime import datetime
from typing_extensions import List, Dict, Optional
from models import TrainingProject

# ------------------- 基础配置（核心：按项目类型分目录） -------------------
# 训练日根目录
TRAINING_DAY_DIR = "./training_days"

# 项目类型映射（避免硬编码）
PROJECT_TYPE_MAP = {
    "photoelectric": "光电项目",
    "network": "网络布线项目"
}

# 初始化根目录（确保存在）
os.makedirs(TRAINING_DAY_DIR, exist_ok=True)

# ------------------- 核心函数改造（全部替换原有函数） -------------------
def create_training_day(req: "CreateTrainingDayRequest"):
    """创建训练日（按项目类型分目录存储）"""
    # 1. 校验项目类型（仅允许光电/网络布线）
    project_type = req.project_type.lower()
    if project_type not in PROJECT_TYPE_MAP:
        raise ValueError(f"不支持的项目类型：{project_type}，仅支持 {list(PROJECT_TYPE_MAP.keys())}")
    
    # 2. 生成带项目类型的唯一ID（格式：training_项目类型_时间戳）
    training_day_id = f"training_{project_type}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    
    # 3. 选择对应项目的预设列表（修复原代码引用错误）
    if req.custom_projects:
        project_list = req.custom_projects
    else:
        if project_type == "photoelectric":
            from config import PRESET_PHOTOELECTRIC_PROJECTS
            preset_items = PRESET_PHOTOELECTRIC_PROJECTS
        else:  # network
            from config import PRESET_NETWORK_PROJECTS
            preset_items = PRESET_NETWORK_PROJECTS
        
        # 转换为TrainingProject模型
        project_list = [
            TrainingProject(
                project_id=item["project_id"],
                project_name=item["project_name"],
                project_desc=item["project_desc"],
                project_order=idx + 1,
                evaluation_type=item.get("evaluation_type", "video_analysis"),
                standard_image_url=item.get("standard_image_url", ""),
                is_analyzed=False
            ) for idx, item in enumerate(preset_items)
        ]

    # 4. 构建训练日数据（新增project_type字段）
    training_day_data = {
        "training_day_id": training_day_id,
        "username": req.username,
        "project_type": project_type,  # 记录项目类型，用于后续校验
        "training_day_name": req.training_day_name,
        "project_list": [p.model_dump() for p in project_list],
        "total_duration": 0,
        "overall_score": 0,
        "overall_analysis": None,
        "created_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "finished_time": None,
        "is_finished": False
    }

    # 5. 按项目类型创建子目录并保存文件
    project_dir = os.path.join(TRAINING_DAY_DIR, project_type)
    os.makedirs(project_dir, exist_ok=True)  # 自动创建项目目录
    save_path = os.path.join(project_dir, f"{training_day_id}.json")
    
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(training_day_data, f, ensure_ascii=False, indent=4)
    
    print(f"✅ 训练日创建成功（{PROJECT_TYPE_MAP[project_type]}）：{save_path}")
    return training_day_data

def get_training_day(training_day_id: str, username: str) -> Optional[Dict]:
    """获取训练日详情（适配分目录，校验项目类型+用户权限）"""
    # 从ID中解析项目类型（格式：training_photoelectric_xxx → photoelectric）
    try:
        project_type = training_day_id.split("_")[1]
        if project_type not in PROJECT_TYPE_MAP:
            print(f"❌ 无效的训练日ID：{training_day_id}")
            return None
    except IndexError:
        print(f"❌ 训练日ID格式错误：{training_day_id}")
        return None
    
    # 拼接对应项目目录路径
    project_dir = os.path.join(TRAINING_DAY_DIR, project_type)
    file_path = os.path.join(project_dir, f"{training_day_id}.json")
    
    if not os.path.exists(file_path):
        print(f"❌ 训练日文件不存在：{file_path}")
        return None
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # 双重校验：用户权限+项目类型一致性
            if data.get("username") != username or data.get("project_type") != project_type:
                print(f"❌ 无权限访问训练日：{training_day_id}")
                return None
            return data
    except Exception as e:
        print(f"❌ 读取训练日失败：{str(e)}")
        return None

def save_training_day(training_day_data: Dict) -> bool:
    """保存训练日数据（适配分目录）"""
    project_type = training_day_data.get("project_type")
    training_day_id = training_day_data.get("training_day_id")
    
    if not project_type or not training_day_id:
        print(f"❌ 训练日数据缺失必填字段")
        return False
    
    # 拼接项目目录路径
    project_dir = os.path.join(TRAINING_DAY_DIR, project_type)
    os.makedirs(project_dir, exist_ok=True)
    save_path = os.path.join(project_dir, f"{training_day_id}.json")
    
    try:
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(training_day_data, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print(f"❌ 保存训练日失败：{str(e)}")
        return False

def get_user_training_day_list(username: str, project_type: Optional[str] = None) -> List[Dict]:
    """获取用户训练日列表（支持按项目类型过滤，核心适配前端）"""
    training_list = []
    
    # 遍历所有项目目录（或指定项目目录）
    target_dirs = []
    if project_type:
        # 只查询指定项目类型目录
        project_dir = os.path.join(TRAINING_DAY_DIR, project_type)
        if os.path.exists(project_dir):
            target_dirs.append((project_dir, project_type))
    else:
        # 查询所有项目类型目录
        for dir_name in os.listdir(TRAINING_DAY_DIR):
            dir_path = os.path.join(TRAINING_DAY_DIR, dir_name)
            if os.path.isdir(dir_path) and dir_name in PROJECT_TYPE_MAP:
                target_dirs.append((dir_path, dir_name))
    
    # 读取每个目录下的训练日
    for dir_path, dir_project_type in target_dirs:
        for file in os.listdir(dir_path):
            if file.endswith(".json") and file.startswith("training_"):
                try:
                    file_path = os.path.join(dir_path, file)
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        # 校验用户权限
                        if data.get("username") == username:
                            training_list.append({
                                "training_day_id": data["training_day_id"],
                                "training_day_name": data["training_day_name"],
                                "project_type": dir_project_type,
                                "project_type_cn": PROJECT_TYPE_MAP[dir_project_type],
                                "created_time": data["created_time"],
                                "is_finished": data["is_finished"],
                                "overall_score": data["overall_score"],
                                "project_count": len(data["project_list"]),
                                "finished_project_count": len([p for p in data["project_list"] if p.get("is_analyzed", False)])
                            })
                except Exception as e:
                    print(f"❌ 读取训练日列表失败：{file}，错误：{str(e)}")
    
    # 按创建时间倒序
    training_list.sort(key=lambda x: x["created_time"], reverse=True)
    return training_list

# ------------------- 保留原有辅助函数（无需修改） -------------------
def update_project_analysis(training_day_id: str, project_id: str, username: str, video_info: Dict, analysis_result: Dict) -> (bool, Dict):
    training_day = get_training_day(training_day_id, username)
    if not training_day:
        return False, "训练日不存在或无权限"
    
    # 更新项目分析结果
    for project in training_day["project_list"]:
        if project["project_id"] == project_id:
            project["video_filename"] = video_info["filename"]
            # 修复1：确保video_duration是数字（None转0）
            project["video_duration"] = video_info.get("duration", 0) or 0
            project["analysis_result"] = analysis_result
            project["is_analyzed"] = True
            project["upload_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            break
    
    # 修复2：计算总时长时，强制处理None值为0（核心修复！）
    training_day["total_duration"] = sum([
        # 步骤1：先取value，None则转0；步骤2：转float；步骤3：确保是数字
        float(p.get("video_duration", 0) or 0) 
        for p in training_day["project_list"]
    ])
    
    # 计算整体评分（示例逻辑，可按实际修改）
    analyzed_projects = [p for p in training_day["project_list"] if p.get("is_analyzed")]
    if analyzed_projects:
        training_day["overall_score"] = round(
            sum([p["analysis_result"].get("score", 0) for p in analyzed_projects]) / len(analyzed_projects), 
            2
        )
    else:
        training_day["overall_score"] = 0
    
    # 保存更新后的数据
    if save_training_day(training_day):
        return True, training_day
    else:
        return False, "保存训练日数据失败"

def update_training_day_summary(training_day_id: str, username: str, overall_analysis: Dict) -> (bool, Dict):
    training_day = get_training_day(training_day_id, username)
    if not training_day:
        return False, "训练日不存在或无权限"
    training_day["overall_score"] = overall_analysis.get("overall_score" , 0)
    #training_day["overall_score"] = overall_analysis.get("overall_score", training_day.get("overall_score", 0))
    training_day["overall_analysis"] = overall_analysis
    training_day["is_finished"] = True
    training_day["finished_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if save_training_day(training_day):
        return True, training_day
    else:
        return False, "保存汇总结果失败"