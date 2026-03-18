# training_system
世界技能大赛网络布线项目训练管理平台，用于存放网络布线项目训练数据、分析训练过程指标、管理训练计划与成果


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

### 网络布线项目核心功能说明
1. 训练数据管理：记录布线实操的耗时、正确率、耗材使用量等指标
2. 训练计划制定：教练端可创建分阶段的布线技能训练计划（如模块端接、链路测试、机柜布线等）
3. 成绩分析：自动统计选手多次训练的成绩趋势，对比世赛标准评分细则
4. 视频复盘：支持上传/播放布线实操视频，标注关键操作节点


后期打算
把关键性的动作截图显示出来，表明得分项和扣分项，如果可以的话放上正确演示的照片
加入一些比赛的扣分细则，动作规范等官方文档作为学习资料，有官方演示视频的话也可以放上去
可以让教练给同学指定每日训练要求，或者让大模型来分析数据之后给出意见和训练的要求，然后让学生按时提交内容并打分
但是大模型的数据分析并不完全可信，必要时需要教练介入，并给出针对性指导意见
