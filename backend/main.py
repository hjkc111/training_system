import uvicorn
from core.app import app  # 导入全局FastAPI实例
from api.auth import router as auth_router
from static_resource import static_router, mount_static_resources  # ✅ 新增：导入挂载函数
from api.network import router as network_router  # 网络布线路由
from api.photoelectric import router as photoelectric_router  # 光电路由
from api.trainingplan import router as trainingplan_router  # 训练日管理路由

# ✅ 关键修复：调用静态资源挂载函数（必须在注册路由前/后执行）
mount_static_resources(app)

# 注册公共路由
app.include_router(auth_router)
app.include_router(static_router)

# 注册各业务项目路由
app.include_router(network_router)
app.include_router(photoelectric_router)
app.include_router(trainingplan_router)

# 启动服务
if __name__ == "__main__":
    uvicorn.run("main:app", reload=True, host="0.0.0.0", port=8000)