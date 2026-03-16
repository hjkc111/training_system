"""
系统数据模型定义
包含登录、视频分析、训练日相关的请求/响应数据模型
"""
from pydantic import BaseModel, Field

# 终极兼容写法：同时支持Python3.8+所有版本，彻底解决导入报错
try:
    # Python3.9+ 优先用内置类型
    from typing import List, Optional, Dict, Any
except ImportError:
    # 兜底兼容
    from typing_extensions import List, Optional,   Dict, Any

# ------------------- 原有模型（完全保留，不影响原有功能） -------------------
class LoginRequest(BaseModel):
    """登录请求参数"""
    username: str
    password: str
    role: str

class AnalysisRequest(BaseModel):
    """单视频分析请求参数"""
    filename: str
    username: str

class HistoryRequest(BaseModel):
    """历史记录查询参数"""
    username: str

# ------------------- 新增：训练日相关模型 -------------------
class TrainingProject(BaseModel):
    """单个训练项目模型"""
    project_id: str
    project_name: str
    project_desc: str
    project_order: int
    evaluation_type: Optional[str] = "video_analysis"  # 评测方式，默认为视频分析
    video_filename: Optional[str] = None
    video_duration: Optional[float] = None
    analysis_result: Optional[dict] = None
    upload_time: Optional[str] = None
    is_analyzed: bool = False
    standard_image_url: Optional[str] = ""  # ✅ 新增：标准图URL（仅图片对比项目使用）

class CreateTrainingDayRequest(BaseModel):
    """创建训练日请求参数"""
    username: str
    training_day_name: str
    custom_projects: Optional[List[TrainingProject]] = None
    project_type: Optional[str] = "general"  # ✅ 新增：标记项目类型（general/photoelectric）

class ProjectAnalyzeRequest(BaseModel):
    """单项目分析请求参数"""
    training_day_id: str
    project_id: str
    filename: str
    username: str

class TrainingDaySummaryRequest(BaseModel):
    """训练日汇总请求参数"""
    training_day_id: str
    username: str

class TrainingDayIdRequest(BaseModel):
    """训练日详情查询参数"""
    training_day_id: str
    username: str


class TrainingPlanGenerateRequest(BaseModel):
    """生成训练计划请求模型"""
    username: str = Field(..., description="用户名")
    training_day_id: str = Field(..., description="训练日ID")
    training_day_data: Dict[str, Any] = Field(..., description="训练日详细数据")

class TrainingPlanExportRequest(BaseModel):
    """导出训练计划请求模型"""
    username: str = Field(..., description="用户名")
    plan_data: Dict[str, Any] = Field(..., description="已生成的训练计划数据")