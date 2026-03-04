安装好虚拟环境之后，用的是3.11版本的python，前端框架采用vue和Element Plus，后端采用fastapi
使用之前安装node.js，然后编写好package.json里面的内容之后,执行
npm install
下载所需要的东西
然后先启动后端
进入到backend文件夹内执行命令
python main.py
然后新开一个终端再启动前端开发服务执行
npm run dev
账号密码身份在这
FAKE_USERS = 
{
    "player1": {"password": "123456", "role": "player"},
    "coach1": {"password": "123456", "role": "coach"}
}
一定要账号密码选手身份全部对应好才能登录
因为剪切视频使用ffmpeg,所以这个也必须下载好,并且配置到环境变量中
D:
cd visualproject/training_system
