import os
import base64
import dashscope
from backend.config import DASHSCOPE_API_KEY

def get_local_images_base64(folder_path):
    """
    读取本地文件夹内的所有图片，转为带前缀的base64编码列表
    :param folder_path: 本地图片文件夹路径（绝对/相对路径）
    :return: 图片base64编码列表（带data:image前缀）
    """
    # 支持的图片格式（可根据需要扩展）
    valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')
    base64_list = []
    
    # 检查文件夹是否存在
    if not os.path.exists(folder_path):
        print(f"错误：文件夹 {folder_path} 不存在！")
        return base64_list
    
    # 遍历文件夹内所有文件
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        # 跳过文件夹，只处理图片文件
        if os.path.isfile(file_path) and filename.lower().endswith(valid_extensions):
            try:
                # 读取图片并转为base64
                with open(file_path, 'rb') as f:
                    img_bytes = f.read()
                    # 生成带前缀的base64（接口必须的格式，避免被误判为URL）
                    img_ext = filename.split('.')[-1].lower()
                    base64_str = f"data:image/{img_ext};base64,{base64.b64encode(img_bytes).decode('utf-8')}"
                    base64_list.append(base64_str)
                    print(f"成功读取并转换图片：{filename}")
            except Exception as e:
                print(f"处理图片 {filename} 失败：{e}")
    
    if not base64_list:
        print(f"警告：文件夹 {folder_path} 内无有效图片文件（支持格式：{valid_extensions}）")
    return base64_list

# ------------------- 核心配置 -------------------
# 替换为你的本地图片文件夹路径（绝对/相对路径都可以）
LOCAL_IMAGE_FOLDER = "D:\\visualproject\\training_system\\backend\\media_extracts\\training_20260310154046066945_project_5\\20260310172533__frames"  # 示例：当前目录下的local_images文件夹
# 提问文本
question = '''
请分析以上图片的内容，图中内容为世界技能大赛的真实比赛录像，请分析出是哪个项目的比赛，并且告诉我哪些图片是有用的
请按照以下格式输出
比赛项目名称：
有用图片序号：
有用图片的内容描述：
'''

# ------------------- 读取本地图片并调用接口 -------------------
# 1. 获取文件夹内所有图片的base64列表
local_images_base64 = get_local_images_base64(LOCAL_IMAGE_FOLDER)

# 2. 无有效图片时直接退出
if not local_images_base64:
    exit(1)

# 3. 构建messages（和原来的结构一致，只是把URL换成base64）
messages = [
    {
        "role": "user",
        "content": [{"image": b64} for b64 in local_images_base64] + [{"text": question}]
    }
]

# 4. 调用通义千问接口
try:
    response = dashscope.MultiModalConversation.call(
        api_key=DASHSCOPE_API_KEY,  # 改用配置文件中的API Key（更规范）
        model='qwen3.5-plus',
        messages=messages
    )
    if response.status_code == 200:
        print("==== 分析结果 ====")
        print(response.output.choices[0].message.content)
    else:
        print(f"接口调用错误：{response.code} - {response.message}")
except Exception as e:
    print(f"调用失败：{e}")