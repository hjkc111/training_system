"""
静态资源管理模块：统一管理资源查阅模块的静态文件（文档、视频、图片）
"""
import os
import mimetypes  # 新增：识别文件MIME类型
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware  # 跨域必备

# 初始化路由
static_router = APIRouter(prefix="/api/static", tags=["静态资源管理"])

# ------------------- 静态资源目录配置（强制跨平台路径兼容） -------------------
# 修复：获取当前文件所在目录（避免多层嵌套路径错误）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 资源根目录：backend/static/resources（确保目录结构：当前文件同级的static/resources）
STATIC_RESOURCE_ROOT = os.path.join(BASE_DIR, "static", "resources")

# 子目录划分（强制生成绝对路径）
OFFICIAL_DOCS_DIR = os.path.abspath(os.path.join(STATIC_RESOURCE_ROOT, "official_docs"))
STANDARD_TUTORIALS_DIR = os.path.abspath(os.path.join(STATIC_RESOURCE_ROOT, "standard_tutorials"))
PAST_CASES_DIR = os.path.abspath(os.path.join(STATIC_RESOURCE_ROOT, "past_cases"))

# 初始化目录（增强：递归创建+权限处理）
def init_static_dirs():
    for dir_path in [STATIC_RESOURCE_ROOT, OFFICIAL_DOCS_DIR, STANDARD_TUTORIALS_DIR, PAST_CASES_DIR]:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True, mode=0o755)  # 增加权限
            print(f"✅ 已创建静态资源目录：{dir_path}")
        else:
            print(f"✅ 静态资源目录已存在：{dir_path}")

init_static_dirs()

# ------------------- 修复静态资源挂载（关键！） -------------------
def mount_static_resources(app):
    """在 main.py 中调用，挂载静态资源目录"""
    # 1. 配置跨域（前端能访问静态资源的核心）
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 生产环境替换为前端域名，如["http://localhost:5173"]
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # 2. 挂载资源根目录（修复：使用绝对路径+确保前端URL和本地路径映射正确）
    app.mount(
        "/static/resources",
        StaticFiles(directory=STATIC_RESOURCE_ROOT, html=True),  # html=True支持目录访问（调试用）
        name="static_resources"
    )
    print(f"✅ 静态资源挂载成功：/static/resources -> {STATIC_RESOURCE_ROOT}")

# ------------------- 增强资源列表接口（修复文件类型+路径） -------------------
@static_router.get("/list")
async def get_static_resource_list(resource_type: str):
    """
    获取静态资源列表（修复：MIME类型+绝对路径+空列表处理）
    """
    type_to_dir = {
        "official_docs": OFFICIAL_DOCS_DIR,
        "standard_tutorials": STANDARD_TUTORIALS_DIR,
        "past_cases": PAST_CASES_DIR
    }
    target_dir = type_to_dir.get(resource_type)
    if not target_dir:
        raise HTTPException(status_code=400, detail="资源类型错误，仅支持 official_docs/standard_tutorials/past_cases")
    
    # 修复：目录不存在/无文件时返回空列表（避免报错）
    if not os.path.exists(target_dir):
        return {"code": 200, "resource_list": []}
    
    resource_list = []
    # 修复：按文件名排序，避免列表乱序
    for filename in sorted(os.listdir(target_dir)):
        file_path = os.path.join(target_dir, filename)
        if os.path.isfile(file_path):
            # 新增：识别文件MIME类型（前端判断预览方式）
            mime_type, _ = mimetypes.guess_type(file_path)
            if not mime_type:
                mime_type = "application/octet-stream"  # 默认二进制
            
            file_size = round(os.path.getsize(file_path) / 1024 / 1024, 2)
            # 修复：强制替换反斜杠（Windows路径问题）
            file_url = f"/static/resources/{resource_type}/{filename}".replace("\\", "/")
            
            resource_info = {
                "id": f"{resource_type}_{filename.split('.')[0]}",
                "title": parse_filename_to_title(filename),
                "filename": filename,
                "file_url": file_url,
                "size_mb": file_size,
                "type": resource_type,
                "desc": get_resource_desc(resource_type, filename),
                "mime_type": mime_type,  # 新增：传给前端判断预览类型
                "file_ext": os.path.splitext(filename)[1].lower()  # 新增：文件后缀（如.pdf/.jpg）
            }
            
            # 补充教程/案例字段（保持原有逻辑）
            if resource_type == "standard_tutorials":
                resource_info["cover_url"] = get_tutorial_cover(filename)
                resource_info["video_url"] = file_url if mime_type.startswith("video/") else ""
            elif resource_type == "past_cases":
                resource_info["cover_url"] = get_case_cover(filename)
                resource_info["video_url"] = file_url if mime_type.startswith("video/") else ""
                resource_info["year"] = get_case_year(filename)
                resource_info["category"] = get_case_category(filename)
            
            resource_list.append(resource_info)
    
    return {
        "code": 200,
        "msg": "success",  # 新增：前端判断成功标识
        "resource_list": resource_list
    }

# ------------------- 新增：预览专用接口（可选，前端也可直接访问static URL） -------------------
@static_router.get("/preview")
async def preview_static_resource(file_url: str):
    """预览静态资源（直接返回文件流，支持浏览器预览）"""
    # 修复：URL转本地路径（兼容Windows/Linux）
    local_path = os.path.abspath(os.path.join(BASE_DIR, file_url.lstrip("/")))
    if not os.path.exists(local_path):
        raise HTTPException(status_code=404, detail="资源文件不存在")
    
    # 自动识别MIME类型（关键：让浏览器正确预览）
    mime_type, _ = mimetypes.guess_type(local_path)
    if not mime_type:
        mime_type = "application/octet-stream"
    
    return FileResponse(
        path=local_path,
        media_type=mime_type,
        filename=os.path.basename(local_path)
    )

# ------------------- 原有下载接口（小幅修复） -------------------
@static_router.get("/download")
async def download_static_resource(file_url: str):
    local_path = os.path.abspath(os.path.join(BASE_DIR, file_url.lstrip("/")))
    if not os.path.exists(local_path):
        raise HTTPException(status_code=404, detail="资源文件不存在")
    
    filename = os.path.basename(local_path)
    return FileResponse(
        path=local_path,
        filename=filename,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"  # 强制下载
        }
    )

# ------------------- 辅助函数（保持原有，补充缺失的实现） -------------------
def parse_filename_to_title(filename: str) -> str:
    filename = filename.replace("_", " ").replace("-", " ").split(".")[0]
    return filename.title()

def get_resource_desc(resource_type: str, filename: str) -> str:
    desc_map = {
        "official_docs": "世界技能大赛官方发布的规则、标准或指导文档，权威可靠",
        "standard_tutorials": "符合大赛标准的技术动作教程，包含详细操作步骤和规范",
        "past_cases": "往届大赛获奖选手的实操案例，含完整操作流程和评分解析"
    }
    base_desc = desc_map.get(resource_type, "优质训练资源")
    if "水晶头" in filename:
        base_desc += "，重点讲解水晶头端接的标准动作和易错点"
    elif "光纤" in filename:
        base_desc += "，详细演示光纤熔接的完整流程和质量控制"
    elif "布线" in filename:
        base_desc += "，涵盖网络布线的规范布局和链路测试方法"
    return base_desc

def get_tutorial_cover(filename: str) -> str:
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
    return f"https://picsum.photos/seed/case{hash(filename)%100}/300/200"

def get_case_year(filename: str) -> str:
    if "2023" in filename:
        return "2023"
    elif "2022" in filename:
        return "2022"
    elif "2021" in filename:
        return "2021"
    return "2023"

def get_case_category(filename: str) -> str:
    if "网络布线" in filename:
        return "网络布线"
    elif "电气装置" in filename:
        return "电气装置"
    elif "工业控制" in filename:
        return "工业控制"
    return "网络布线"