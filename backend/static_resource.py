"""
静态资源管理模块：统一管理资源查阅模块的静态文件（文档、视频、图片）
"""
import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# 初始化路由
static_router = APIRouter(prefix="/api/static", tags=["静态资源管理"])

# ------------------- 静态资源目录配置（和你的项目结构对齐） -------------------
# 资源根目录：backend/static/resources（需手动创建）
STATIC_RESOURCE_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "resources")

# 子目录划分（和前端资源分类对应）
OFFICIAL_DOCS_DIR = os.path.join(STATIC_RESOURCE_ROOT, "official_docs")  # 官方文档
STANDARD_TUTORIALS_DIR = os.path.join(STATIC_RESOURCE_ROOT, "standard_tutorials")  # 标准教程
PAST_CASES_DIR = os.path.join(STATIC_RESOURCE_ROOT, "past_cases")  # 往届案例

# 初始化目录（自动创建不存在的文件夹）
def init_static_dirs():
    for dir_path in [STATIC_RESOURCE_ROOT, OFFICIAL_DOCS_DIR, STANDARD_TUTORIALS_DIR, PAST_CASES_DIR]:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            print(f"已创建静态资源目录：{dir_path}")

# 执行目录初始化
init_static_dirs()

# ------------------- 静态资源挂载（让前端能直接访问文件） -------------------
def mount_static_resources(app):
    """在 main.py 中调用，挂载静态资源目录"""
    # 挂载资源根目录：前端可通过 /static/resources/xxx 访问文件
    app.mount(
        "/static/resources",
        StaticFiles(directory=STATIC_RESOURCE_ROOT),
        name="static_resources"
    )
    print("静态资源目录挂载成功：/static/resources ->", STATIC_RESOURCE_ROOT)

# ------------------- 资源访问接口（前端通过接口获取资源列表/下载） -------------------
@static_router.get("/list")
async def get_static_resource_list(resource_type: str):
    """
    获取静态资源列表
    resource_type: official_docs（官方文档）/ standard_tutorials（标准教程）/ past_cases（往届案例）
    """
    # 映射资源类型到目录
    type_to_dir = {
        "official_docs": OFFICIAL_DOCS_DIR,
        "standard_tutorials": STANDARD_TUTORIALS_DIR,
        "past_cases": PAST_CASES_DIR
    }
    target_dir = type_to_dir.get(resource_type)
    if not target_dir:
        raise HTTPException(status_code=400, detail="资源类型错误，仅支持 official_docs/standard_tutorials/past_cases")
    
    # 遍历目录下的文件，生成资源列表
    resource_list = []
    for filename in os.listdir(target_dir):
        file_path = os.path.join(target_dir, filename)
        if os.path.isfile(file_path):
            # 获取文件大小（MB）
            file_size = round(os.path.getsize(file_path) / 1024 / 1024, 2)
            # 生成访问URL（和前端一致）
            file_url = f"/static/resources/{resource_type}/{filename}".replace("\\", "/")
            
            # 补充资源详情（根据文件名解析，实际可存JSON配置）
            resource_info = {
                "id": f"{resource_type}_{filename.split('.')[0]}",
                "title": parse_filename_to_title(filename),
                "filename": filename,
                "file_url": file_url,
                "size_mb": file_size,
                "type": resource_type,
                "desc": get_resource_desc(resource_type, filename)
            }
            
            # 教程/案例补充封面图和视频URL
            if resource_type == "standard_tutorials":
                resource_info["cover_url"] = get_tutorial_cover(filename)
                resource_info["video_url"] = file_url if filename.endswith((".mp4", ".mov")) else ""
            elif resource_type == "past_cases":
                resource_info["cover_url"] = get_case_cover(filename)
                resource_info["video_url"] = file_url if filename.endswith((".mp4", ".mov")) else ""
                resource_info["year"] = get_case_year(filename)
                resource_info["category"] = get_case_category(filename)
            
            resource_list.append(resource_info)
    
    return {
        "code": 200,
        "resource_list": resource_list
    }

@static_router.get("/download")
async def download_static_resource(file_url: str):
    """下载静态资源"""
    # 转换URL为本地路径
    local_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_url.lstrip("/"))
    if not os.path.exists(local_path):
        raise HTTPException(status_code=404, detail="资源文件不存在")
    
    # 返回文件下载响应
    filename = os.path.basename(local_path)
    return FileResponse(
        path=local_path,
        filename=filename,
        media_type="application/octet-stream"
    )

# ------------------- 辅助函数（解析资源信息，可根据实际文件调整） -------------------
def parse_filename_to_title(filename: str) -> str:
    """从文件名解析资源标题（示例逻辑，可自定义）"""
    filename = filename.replace("_", " ").replace("-", " ").split(".")[0]
    # 大写首字母
    return filename.title()

def get_resource_desc(resource_type: str, filename: str) -> str:
    """获取资源描述"""
    desc_map = {
        "official_docs": "世界技能大赛官方发布的规则、标准或指导文档，权威可靠",
        "standard_tutorials": "符合大赛标准的技术动作教程，包含详细操作步骤和规范",
        "past_cases": "往届大赛获奖选手的实操案例，含完整操作流程和评分解析"
    }
    base_desc = desc_map.get(resource_type, "优质训练资源")
    # 补充文件名相关描述
    if "水晶头" in filename:
        base_desc += "，重点讲解水晶头端接的标准动作和易错点"
    elif "光纤" in filename:
        base_desc += "，详细演示光纤熔接的完整流程和质量控制"
    elif "布线" in filename:
        base_desc += "，涵盖网络布线的规范布局和链路测试方法"
    return base_desc

def get_tutorial_cover(filename: str) -> str:
    """获取教程封面图（使用示例图片，可替换为本地图片路径）"""
    cover_map = {
        "水晶头": "https://picsum.photos/seed/crystal/300/200",
        "光纤": "https://picsum.photos/seed/fiber/300/200",
        "布线": "https://picsum.photos/seed/wiring/300/200",
        "测试": "https://picsum.photos/seed/test/300/200"
    }
    for key, url in cover_map.items():
        if key in filename:
            return url
    return "https://picsum.photos/seed/tutorial/300/200"

def get_case_cover(filename: str) -> str:
    """获取案例封面图"""
    return f"https://picsum.photos/seed/case{hash(filename)%100}/300/200"

def get_case_year(filename: str) -> str:
    """获取案例年份"""
    if "2023" in filename:
        return "2023"
    elif "2022" in filename:
        return "2022"
    elif "2021" in filename:
        return "2021"
    return "2023"

def get_case_category(filename: str) -> str:
    """获取案例类别"""
    if "网络布线" in filename:
        return "网络布线"
    elif "电气装置" in filename:
        return "电气装置"
    elif "工业控制" in filename:
        return "工业控制"
    return "网络布线"