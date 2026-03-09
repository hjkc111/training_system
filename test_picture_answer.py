#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-
"""
调用Qwen3.5 Plus（通义千问）的多模态脚本
适配阿里云官方MultiModalConversation接口规范
"""
import os
import base64
import dashscope
from dashscope import MultiModalConversation

# ======================== 以下为用户需手动修改的配置项 ========================
# 1. 替换为你的阿里云百炼API Key
DASHSCOPE_API_KEY = "sk-972fac09f6f44833972b461e033bc2e5"
# 2. 替换为你的本地图片目录（视频帧所在路径）
LOCAL_IMAGE_DIR = r"D:\visualproject\training_system\backend\media_extracts\training_20260306151404180860_project_1\20260306151410_10_frames"
# 3. 单次调用最多加载的图片数量（建议8张以内，避免token超限）
MAX_IMAGES = 8
# ============================================================================

dashscope.base_http_api_url = "https://dashscope.aliyuncs.com/api/v1"

def print_welcome_info():
    print("="*60)
    print("          Qwen3.5 Plus 视频帧分析脚本")
    print("="*60)
    print("\n【操作步骤】")
    print("1. 输入你的问题，按回车提交；输入「exit/quit」可退出脚本")
    print("="*60 + "\n")

def load_images_to_base64(image_dir):
    if not os.path.exists(image_dir):
        raise FileNotFoundError(f"图片目录不存在：{image_dir}")
    
    supported_formats = ('.jpg', '.jpeg', '.png')
    image_base64_list = []
    
    for file_name in sorted(os.listdir(image_dir)):
        file_path = os.path.join(image_dir, file_name)
        if os.path.isfile(file_path) and file_name.lower().endswith(supported_formats):
            try:
                with open(file_path, 'rb') as f:
                    img_bytes = f.read()
                    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
                    
                    if file_name.lower().endswith(('.jpg', '.jpeg')):
                        img_data_url = f"data:image/jpeg;base64,{img_base64}"
                    elif file_name.lower().endswith('.png'):
                        img_data_url = f"data:image/png;base64,{img_base64}"
                    else:
                        img_data_url = f"data:image/jpeg;base64,{img_base64}"
                    
                    image_base64_list.append(img_data_url)
                    print(f"✅ 成功加载图片：{file_name}")
            except Exception as e:
                print(f"❌ 加载图片失败 {file_name}：{str(e)}，跳过该图片")
    
    if not image_base64_list:
        raise ValueError(f"图片目录 {image_dir} 中未找到支持的图片！")
    
    return image_base64_list[:MAX_IMAGES]

def call_qwen35_plus(image_base64_list, user_question):
    # 4. 可修改此提示词调整回答规则（比如增减分析维度、修改回答风格）
    system_prompt = """
你是专业的视频帧分析师，基于提供的图片分析并回答问题：
1. 重点描述视觉信息：人物动作、工具、场景、物体特征；
2. 回答仅基于图片内容，禁止编造；
3. 有可识别内容直接描述，无关则说明“未包含相关信息”。
    """
    
    full_prompt = f"{system_prompt}\n\n用户问题：{user_question}"
    
    messages = [
        {
            "role": "user",
            "content": [
                *[{"image": frame} for frame in image_base64_list],
                {"text": full_prompt}
            ]
        }
    ]
    
    try:
        print("🤖 正在调用Qwen3.5 Plus分析视频帧...")
        response = MultiModalConversation.call(
            api_key=DASHSCOPE_API_KEY,
            model='qwen3.5-plus',
            messages=messages,
            # 5. temperature：0-1，值越高回答越灵活，越低越精准（建议0.1-0.3）
            temperature=0.2,
            top_p=0.9,
            # 6. max_tokens：回答的最大长度（按需调整，建议1000-2000）
            max_tokens=2000
        )
        
        if response.status_code == 200:
            answer_text = response.output.choices[0].message.content[0]["text"]
            if hasattr(response, 'usage'):
                usage = response.usage
                print(f"Token消耗: 输入={usage.input_tokens}, 输出={usage.output_tokens}, 总计={usage.total_tokens}")
            return answer_text
        else:
            return f"❌ 调用接口失败：{response.message}"
    except Exception as e:
        return f"❌ 调用接口失败：{str(e)}"

def main():
    print_welcome_info()
    
    try:
        print("🔍 正在加载指定目录下的图片...")
        image_base64_list = load_images_to_base64(LOCAL_IMAGE_DIR)
        print(f"\n✅ 共成功加载 {len(image_base64_list)} 张图片（前{MAX_IMAGES}张），可开始提问！\n")
        
        while True:
            user_question = input("请输入你的问题（输入exit/quit退出）：").strip()
            if user_question.lower() in ['exit', 'quit']:
                print("👋 脚本已退出！")
                break
            if not user_question:
                print("⚠️  问题不能为空！")
                continue
            
            answer = call_qwen35_plus(image_base64_list, user_question)
            print("="*40 + " 回答 " + "="*40)
            print(answer)
            print("="*88 + "\n")
    
    except Exception as e:
        print(f"\n❌ 初始化失败：{str(e)}")
        print("💡 检查项：1.API-KEY 2.图片路径 3.图片格式（仅支持jpg/jpeg/png）")

if __name__ == "__main__":
    main()