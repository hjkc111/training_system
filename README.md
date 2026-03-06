# training_system
学生训练管理平台，用于存放训练数据和分析训练数据

## 环境配置与启动步骤
1. Python 版本：3.11（需先安装虚拟环境）
2. 前端技术栈：Vue + Element Plus（需先安装 Node.js）
3. 后端技术栈：FastAPI

### 安装依赖
- 前端：编写好 package.json 后，执行 `npm install` 下载依赖
- 视频处理：需安装 ffmpeg 并配置到系统环境变量中


### 启动流程
1. 启动后端：进入 backend 文件夹，执行 `python main.py`
conda activate training_system
D:
cd visualproject
cd training_system
cd backend
python main.py
2. 启动前端：新开终端，执行 `npm run dev`
conda activate training_system
D:
cd visualproject
cd training_system
cd frontend
npm run dev

### 登录账号信息
FAKE_USERS = {
    "player1": {"password": "123456", "role": "player"},
    "coach1": {"password": "123456", "role": "coach"}
}
⚠️ 注意：账号、密码、身份需完全对应才能登录