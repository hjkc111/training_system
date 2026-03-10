import os
import dashscope
from backend.config import DASHSCOPE_API_KEY
# 你的图片URL列表（数量任意）
image_urls = [
    "https://dashscope.oss-cn-beijing.aliyuncs.com/images/dog_and_girl.jpeg",
    "https://dashscope.oss-cn-beijing.aliyuncs.com/images/tiger.png",
    "https://dashscope.oss-cn-beijing.aliyuncs.com/images/rabbit.png"
]
# 提问文本
question = "这些是什么?"

# 核心：用列表推导式直接生成content，内嵌在messages里
messages = [
    {
        "role": "user",
        "content": [{"image": url} for url in image_urls] + [{"text": question}]
    }
]

# 调用接口（保留基础错误处理，不冗余）
try:
    response = dashscope.MultiModalConversation.call(
        api_key="sk-972fac09f6f44833972b461e033bc2e5",
        model='qwen3.5-plus',
        messages=messages
    )
    if response.status_code == 200:
        print(response.output.choices[0].message.content)
    else:
        print(f"错误：{response.code} - {response.message}")
except Exception as e:
    print(f"调用失败：{e}")