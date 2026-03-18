import json
import dashscope
import base64
from dashscope import Generation
from config import DASHSCOPE_API_KEY
import os
import cv2

def call_qwen35(video_text, key_frames_base64, username, is_audio_useful):
    """调用Qwen3.5-Plus分析视频，优先分析关键帧，优化评分逻辑"""
    # 核心优化：提示词强制优先分析关键帧画面，弱化无效音频的影响
    prompt = f"""
    你是一名专业的世界技能大赛技术动作分析师，严格按以下规则分析用户{username}的训练视频：
    【优先级】：优先分析视频关键帧画面内容，音频仅作为辅助参考！
    【分析步骤】：
    1. 逐帧分析关键帧画面：描述画面中能看到的人物动作、操作工具、操作对象、环境场景；
    2. 结合音频内容（仅作参考）：{video_text if is_audio_useful else '（音频无效，忽略）'}；
    3. 判定是否为世界技能大赛相关训练内容（如网络布线、焊接、电气装置、工业控制等）；
    4. 即使未识别到标准技能动作，也需基于画面内容给出基础评分（最低不低于20分）；
    
    【分析要求】：
    - 核心：必须基于关键帧画面内容输出分析结果，禁止仅因音频无效判定为"无效素材"；
    - 分析总结：200字以内，必须包含画面内容描述；
    - 技术动作规范性评分：0-100分，无明确错误至少给20分，有基础动作给40+分；
    - 改进建议：至少3条，基于画面内容给出具体建议（如"画面中操作工具握持不规范，建议调整手势"）；
    - 视频统计：duration填0（前端会自动填充），action_count统计画面中能识别的动作数量（至少填1）；
    - key_frame_analysis：简要描述关键帧整体内容（如"画面显示人物手持电工工具，在操作接线端子"）。
    
    【输出格式】：严格JSON字符串，字段如下：
    {{
        "analysis_summary": "分析总结",
        "action_norm_score": 评分（数字）,
        "improvement_suggestions": ["建议1", "建议2", "建议3"],
        "video_stats": {{"duration": 0, "action_count": 至少1}},
        "key_frame_analysis": "关键帧整体描述"
    }}
    """
    
    try:
        print("开始调用Qwen3.5-Plus...")
        # 优化：最多传递8帧（减少token消耗，提升分析准确性）
        valid_frames = key_frames_base64[:8]
        print(f"向大模型传递 {len(valid_frames)} 帧关键帧")
        
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    *[{"type": "image", "image": frame} for frame in valid_frames]
                ]
            }
        ]
        
        response = Generation.call(
            model="qwen-plus",
            api_key=DASHSCOPE_API_KEY,
            messages=messages,
            result_format="json",
            temperature=0.1,  # 降低随机性，提升结果稳定性
            top_p=0.9,
            max_tokens=2000  # 增加输出长度限制
        )
        
        # 输出token消耗
        if response.status_code == 200:
            usage = response.usage
            print(f"Qwen3.5-Plus Token消耗: 输入={usage.input_tokens}, 输出={usage.output_tokens}, 总计={usage.total_tokens}")
            
            try:
                analysis_result = json.loads(response.output.choices[0].message.content)
                
                # 兜底修正：确保评分和动作数符合要求
                if analysis_result.get("action_norm_score", 0) < 20:
                    analysis_result["action_norm_score"] = 20
                    print("兜底修正：评分低于20分，自动调整为20分")
                if analysis_result.get("video_stats", {}).get("action_count", 0) < 1:
                    analysis_result["video_stats"]["action_count"] = 1
                    print("兜底修正：动作数为0，自动调整为1")
                
                return analysis_result
            except json.JSONDecodeError as e:
                print(f"解析大模型结果失败：{str(e)}")
                # 兜底返回（基于画面的默认结果）
                return {
                    "analysis_summary": "关键帧画面识别到基础训练场景，但大模型返回格式异常，按基础标准评分",
                    "action_norm_score": 20,
                    "improvement_suggestions": [
                        "建议拍摄更清晰的训练视频，突出技术动作细节",
                        "建议在操作时同步口述操作步骤，便于精准分析",
                        "建议确保训练场景光线充足，关键动作完整入镜"
                    ],
                    "video_stats": {"duration": 0, "action_count": 1},
                    "key_frame_analysis": "关键帧显示基础训练场景，可识别到操作动作轮廓"
                }
        else:
            print(f"大模型调用失败：{response.message}")
            return {
                "analysis_summary": f"大模型调用失败，但已提取关键帧画面：{response.message}",
                "action_norm_score": 20,
                "improvement_suggestions": [
                    "检查网络连接后重新分析",
                    "确保视频画面清晰、动作完整",
                    "缩短视频时长后重新上传分析"
                ],
                "video_stats": {"duration": 0, "action_count": 1},
                "key_frame_analysis": "关键帧提取成功，大模型调用失败"
            }
    except Exception as e:
        print(f"调用Qwen3.5-Plus出错：{str(e)}")
        return {
            "analysis_summary": f"调用大模型出错，但关键帧已提取：{str(e)}",
            "action_norm_score": 20,
            "improvement_suggestions": [
                "重启后端服务后重新分析",
                "检查视频文件是否损坏",
                "确保FFmpeg和OpenCV环境正常"
            ],
            "video_stats": {"duration": 0, "action_count": 1},
            "key_frame_analysis": f"关键帧提取成功，调用出错：{str(e)[:50]}"
        }
    
# ------------------- 新增：单项目专项分析（适配比赛项目）网络布线 -------------------
def call_qwen_project_analysis_network(project_name: str, project_desc: str, video_text: str, key_frames_base64: list, username: str, is_audio_useful: bool):
    """针对单个比赛项目的专项AI分析（修复List嵌套JSON的解析错误）"""
    prompt = f"""
    你是世界技能大赛官方认证的技术裁判，现在针对【{project_name}】项目，分析选手{username}的训练视频，严格遵循该项目的行业标准和大赛评分规则。
    【项目标准说明】：{project_desc}
    【分析优先级】：优先分析关键帧画面内容，音频仅作为辅助参考！
    【音频内容】：{video_text if is_audio_useful else '（音频无效，忽略）'}

    【分析要求】：
    1. 严格基于项目标准，分析视频中的操作流程、动作规范性、工具使用是否符合大赛要求；
    2. 精准统计：操作总时长、关键步骤完成数量、错误步骤数量；
    3. 量化评分：项目总分100分，按大赛标准扣分，给出最终得分；
    4. 详细列出：扣分项（含扣分原因、扣分值）、正确完成项、操作用时分析；
    5. 给出可落地的改进建议，至少3条，贴合大赛评分标准。
    6.尽量多的尽可能精确的描述内容，并给出标准化的操作步骤应该是怎么样的，字数稍微多一些
    【输出格式】：严格返回纯JSON字符串，仅返回JSON，不要任何额外文字、注释、换行、反引号、列表包裹！字段如下：
    {{
        "project_name": "{project_name}",
        "project_score": 最终得分（数字0-100）,
        "operation_duration": 操作时长（秒，数字）,
        "step_completed_count": 完成步骤数（数字）,
        "step_error_count": 错误步骤数（数字）,
        "deduction_items": [{{"reason": "扣分原因", "deduction_score": 扣分值}}],
        "correct_items": ["正确完成的操作1", "正确完成的操作2"],
        "time_analysis": "用时分析（是偏快/偏慢/符合标准，原因）",
        "action_norm_analysis": "动作规范性分析",
        "improvement_suggestions": ["建议1", "建议2", "建议3"]
    }}
    """
    
    try:
        print(f"开始调用Qwen3.5-Plus进行【{project_name}】专项分析...")
        valid_frames = key_frames_base64[:8]
        print(f"向Qwen3.5-Plus传递 {len(valid_frames)} 帧关键帧")
        
        # 构建messages（和你能跑的代码结构一致）
        messages = [
            {
                "role": "user",
                "content": [{"image": b64} for b64 in valid_frames] + [{"text": prompt}]
            }
        ]
        
        # 调用Qwen3.5-Plus
        response = dashscope.MultiModalConversation.call(
            api_key=DASHSCOPE_API_KEY,
            model='qwen3.5-plus',
            messages=messages
        )
        
        if response.status_code == 200:
            print(f"Qwen3.5-Plus调用成功，开始解析结果")
            
            try:
                # 第一步：获取原始返回内容并打印（完整日志）
                raw_content = response.output.choices[0].message.content
                print(f"大模型原始返回内容：{str(raw_content)[:500]}...")
                
                # 第二步：处理List类型返回（核心修复）
                analysis_result_str = ""
                if isinstance(raw_content, list):
                    print(f"返回内容是List类型，长度：{len(raw_content)}，开始提取嵌套的JSON字符串")
                    # 遍历List，找到包含text字段的字典
                    for item in raw_content:
                        if isinstance(item, dict) and "text" in item:
                            # 提取text字段里的内容（这才是真正的JSON字符串）
                            analysis_result_str = item["text"].strip()
                            print(f"从List中提取到JSON字符串（前200字符）：{analysis_result_str[:200]}...")
                            break
                    # 如果List里没找到text字段，取第一个元素转为字符串
                    if not analysis_result_str and len(raw_content) > 0:
                        analysis_result_str = str(raw_content[0]).strip()
                elif isinstance(raw_content, dict):
                    print(f"返回内容是Dict类型，提取text字段")
                    analysis_result_str = raw_content.get("text", "").strip()
                elif isinstance(raw_content, (str, bytes, bytearray)):
                    print(f"返回内容是字符串类型，直接使用")
                    analysis_result_str = str(raw_content).strip()
                else:
                    raise Exception(f"不支持的返回类型：{type(raw_content)}")
                
                # 第三步：清理JSON字符串（移除多余字符）
                if not analysis_result_str:
                    raise Exception("提取到的JSON字符串为空")
                
                # 移除markdown反引号、换行、空格
                analysis_result_str = analysis_result_str.replace("```json", "").replace("```", "").replace("\n", "").replace("\r", "").strip()
                print(f"清理后的JSON字符串（前200字符）：{analysis_result_str[:200]}...")
                
                # 第四步：解析为字典
                analysis_result = json.loads(analysis_result_str)
                
                # 第五步：校验是否为字典（防止解析后还是List）
                if not isinstance(analysis_result, dict):
                    raise Exception(f"解析后不是字典类型，而是：{type(analysis_result)}")
                
                # 兜底校验：确保得分在0-100之间
                analysis_result["project_score"] = max(0, min(100, analysis_result.get("project_score", 0)))
                print(f"✅ 解析成功，项目得分：{analysis_result['project_score']}")
                return analysis_result
            
            except json.JSONDecodeError as e:
                print(f"解析大模型结果失败（JSON格式错误）：{str(e)}")
                print(f"失败的内容：{analysis_result_str[:500]}")
                # 兜底返回值
                return {
                    "project_name": project_name,
                    "project_score": 20,
                    "operation_duration": 0,
                    "step_completed_count": 0,
                    "step_error_count": 0,
                    "deduction_items": [{"reason": f"JSON解析失败：{str(e)}", "deduction_score": 0}],
                    "correct_items": ["无"],
                    "time_analysis": "无法分析",
                    "action_norm_analysis": "解析失败",
                    "improvement_suggestions": ["重新上传清晰视频", "确保操作完整入镜", "同步口述操作步骤"]
                }
            except Exception as e:
                print(f"解析结果时发生错误：{str(e)}")
                # 兜底返回值
                return {
                    "project_name": project_name,
                    "project_score": 20,
                    "operation_duration": 0,
                    "step_completed_count": 0,
                    "step_error_count": 0,
                    "deduction_items": [{"reason": f"解析错误：{str(e)}", "deduction_score": 0}],
                    "correct_items": ["无"],
                    "time_analysis": "无法分析",
                    "action_norm_analysis": "解析出错",
                    "improvement_suggestions": ["重启后端服务", "检查视频文件", "确保FFmpeg环境正常"]
                }
        else:
            print(f"Qwen3.5-Plus调用失败：{response.code} - {response.message}")
            # 兜底返回值
            return {
                "project_name": project_name,
                "project_score": 20,
                "operation_duration": 0,
                "step_completed_count": 0,
                "step_error_count": 0,
                "deduction_items": [{"reason": f"大模型调用失败：{response.code}-{response.message}", "deduction_score": 0}],
                "correct_items": ["无"],
                "time_analysis": "无法分析",
                "action_norm_analysis": "调用失败",
                "improvement_suggestions": ["检查网络后重试", "缩短视频时长", "确保视频格式正确"]
            }
    except Exception as e:
        print(f"调用Qwen3.5-Plus出错：{str(e)}")
        # 兜底返回值
        return {
            "project_name": project_name,
            "project_score": 20,
            "operation_duration": 0,
            "step_completed_count": 0,
            "step_error_count": 0,
            "deduction_items": [{"reason": f"调用出错：{str(e)}", "deduction_score": 0}],
            "correct_items": ["无"],
            "time_analysis": "无法分析",
            "action_norm_analysis": "调用出错",
            "improvement_suggestions": ["重启后端服务", "检查视频文件", "确保FFmpeg环境正常"]
        }
#针对光电项目的qwen3.5-plus实验
def call_qwen_project_analysis_photoelectric(project_name: str, project_desc: str, video_text: str, key_frames_base64: list, username: str, is_audio_useful: bool):
    """针对单个比赛项目的专项AI分析（修复List嵌套JSON的解析错误）"""
    prompt = f"""
    你是世界技能大赛官方认证的技术裁判，现在针对【{project_name}】项目，分析选手{username}的训练视频，严格遵循该项目的行业标准和大赛评分规则。
    【项目标准说明】：{project_desc}
    【分析优先级】：优先分析关键帧画面内容，音频仅作为辅助参考！
    【音频内容】：{video_text if is_audio_useful else '（音频无效，忽略）'}

    【分析要求】：
    1. 严格基于项目标准，分析视频中的操作流程、动作规范性、工具使用是否符合大赛要求；
    2. 精准统计：操作总时长、关键步骤完成数量、错误步骤数量；
    3. 量化评分：项目总分100分，按大赛标准扣分，给出最终得分；
    4. 详细列出：扣分项（含扣分原因、扣分值）、正确完成项、操作用时分析；
    5. 给出可落地的改进建议，至少3条，贴合大赛评分标准。
    6.尽量多的尽可能精确的描述内容，并给出标准化的操作步骤应该是怎么样的，字数稍微多一些
    【输出格式】：严格返回纯JSON字符串，仅返回JSON，不要任何额外文字、注释、换行、反引号、列表包裹！字段如下：
    {{
        "project_name": "{project_name}",
        "project_score": 最终得分（数字0-100）,
        "operation_duration": 操作时长（秒，数字）,
        "step_completed_count": 完成步骤数（数字）,
        "step_error_count": 错误步骤数（数字）,
        "deduction_items": [{{"reason": "扣分原因", "deduction_score": 扣分值}}],
        "correct_items": ["正确完成的操作1", "正确完成的操作2"],
        "time_analysis": "用时分析（是偏快/偏慢/符合标准，原因）",
        "action_norm_analysis": "动作规范性分析",
        "improvement_suggestions": ["建议1", "建议2", "建议3"]
    }}
    """
    
    try:
        print(f"开始调用Qwen3.5-Plus进行【{project_name}】专项分析...")
        valid_frames = key_frames_base64[:8]
        print(f"向Qwen3.5-Plus传递 {len(valid_frames)} 帧关键帧")
        
        # 构建messages（和你能跑的代码结构一致）
        messages = [
            {
                "role": "user",
                "content": [{"image": b64} for b64 in valid_frames] + [{"text": prompt}]
            }
        ]
        
        # 调用Qwen3.5-Plus
        response = dashscope.MultiModalConversation.call(
            api_key=DASHSCOPE_API_KEY,
            model='qwen3.5-plus',
            messages=messages
        )
        
        if response.status_code == 200:
            print(f"Qwen3.5-Plus调用成功，开始解析结果")
            
            try:
                # 第一步：获取原始返回内容并打印（完整日志）
                raw_content = response.output.choices[0].message.content
                print(f"大模型原始返回内容：{str(raw_content)[:500]}...")
                
                # 第二步：处理List类型返回（核心修复）
                analysis_result_str = ""
                if isinstance(raw_content, list):
                    print(f"返回内容是List类型，长度：{len(raw_content)}，开始提取嵌套的JSON字符串")
                    # 遍历List，找到包含text字段的字典
                    for item in raw_content:
                        if isinstance(item, dict) and "text" in item:
                            # 提取text字段里的内容（这才是真正的JSON字符串）
                            analysis_result_str = item["text"].strip()
                            print(f"从List中提取到JSON字符串（前200字符）：{analysis_result_str[:200]}...")
                            break
                    # 如果List里没找到text字段，取第一个元素转为字符串
                    if not analysis_result_str and len(raw_content) > 0:
                        analysis_result_str = str(raw_content[0]).strip()
                elif isinstance(raw_content, dict):
                    print(f"返回内容是Dict类型，提取text字段")
                    analysis_result_str = raw_content.get("text", "").strip()
                elif isinstance(raw_content, (str, bytes, bytearray)):
                    print(f"返回内容是字符串类型，直接使用")
                    analysis_result_str = str(raw_content).strip()
                else:
                    raise Exception(f"不支持的返回类型：{type(raw_content)}")
                
                # 第三步：清理JSON字符串（移除多余字符）
                if not analysis_result_str:
                    raise Exception("提取到的JSON字符串为空")
                
                # 移除markdown反引号、换行、空格
                analysis_result_str = analysis_result_str.replace("```json", "").replace("```", "").replace("\n", "").replace("\r", "").strip()
                print(f"清理后的JSON字符串（前200字符）：{analysis_result_str[:200]}...")
                
                # 第四步：解析为字典
                analysis_result = json.loads(analysis_result_str)
                
                # 第五步：校验是否为字典（防止解析后还是List）
                if not isinstance(analysis_result, dict):
                    raise Exception(f"解析后不是字典类型，而是：{type(analysis_result)}")
                
                # 兜底校验：确保得分在0-100之间
                analysis_result["project_score"] = max(0, min(100, analysis_result.get("project_score", 0)))
                print(f"✅ 解析成功，项目得分：{analysis_result['project_score']}")
                return analysis_result
            
            except json.JSONDecodeError as e:
                print(f"解析大模型结果失败（JSON格式错误）：{str(e)}")
                print(f"失败的内容：{analysis_result_str[:500]}")
                # 兜底返回值
                return {
                    "project_name": project_name,
                    "project_score": 20,
                    "operation_duration": 0,
                    "step_completed_count": 0,
                    "step_error_count": 0,
                    "deduction_items": [{"reason": f"JSON解析失败：{str(e)}", "deduction_score": 0}],
                    "correct_items": ["无"],
                    "time_analysis": "无法分析",
                    "action_norm_analysis": "解析失败",
                    "improvement_suggestions": ["重新上传清晰视频", "确保操作完整入镜", "同步口述操作步骤"]
                }
            except Exception as e:
                print(f"解析结果时发生错误：{str(e)}")
                # 兜底返回值
                return {
                    "project_name": project_name,
                    "project_score": 20,
                    "operation_duration": 0,
                    "step_completed_count": 0,
                    "step_error_count": 0,
                    "deduction_items": [{"reason": f"解析错误：{str(e)}", "deduction_score": 0}],
                    "correct_items": ["无"],
                    "time_analysis": "无法分析",
                    "action_norm_analysis": "解析出错",
                    "improvement_suggestions": ["重启后端服务", "检查视频文件", "确保FFmpeg环境正常"]
                }
        else:
            print(f"Qwen3.5-Plus调用失败：{response.code} - {response.message}")
            # 兜底返回值
            return {
                "project_name": project_name,
                "project_score": 20,
                "operation_duration": 0,
                "step_completed_count": 0,
                "step_error_count": 0,
                "deduction_items": [{"reason": f"大模型调用失败：{response.code}-{response.message}", "deduction_score": 0}],
                "correct_items": ["无"],
                "time_analysis": "无法分析",
                "action_norm_analysis": "调用失败",
                "improvement_suggestions": ["检查网络后重试", "缩短视频时长", "确保视频格式正确"]
            }
    except Exception as e:
        print(f"调用Qwen3.5-Plus出错：{str(e)}")
        # 兜底返回值
        return {
            "project_name": project_name,
            "project_score": 20,
            "operation_duration": 0,
            "step_completed_count": 0,
            "step_error_count": 0,
            "deduction_items": [{"reason": f"调用出错：{str(e)}", "deduction_score": 0}],
            "correct_items": ["无"],
            "time_analysis": "无法分析",
            "action_norm_analysis": "调用出错",
            "improvement_suggestions": ["重启后端服务", "检查视频文件", "确保FFmpeg环境正常"]
        }
# ------------------- 新增：训练日整体汇总分析 -------------------
def call_qwen_training_summary(training_day_data: dict, username: str):
    """基于训练日所有项目的分析结果，生成整体汇总报告（适配Qwen3.5-Plus调用，修复解析逻辑）"""
    project_list = training_day_data["project_list"]
    project_count = len(project_list)
    finished_projects = [p for p in project_list if p["is_analyzed"]]
    total_duration = training_day_data["total_duration"]

    # 整理所有项目的核心数据（原有逻辑完全保留）
    project_summary = []
    total_score = 0
    total_deduction = 0
    for p in finished_projects:
        score = p["analysis_result"].get("project_score", 0)
        total_score += score
        deductions = p["analysis_result"].get("deduction_items", [])
        project_deduction = sum([d.get("deduction_score", 0) for d in deductions])
        total_deduction += project_deduction
        project_summary.append({
            "project_name": p["project_name"],
            "score": score,
            "duration": p["video_duration"],
            "deduction_score": project_deduction,
            "error_count": p["analysis_result"].get("step_error_count", 0)
        })

    avg_score = round(total_score / len(finished_projects), 2) if finished_projects else 0

    # Prompt保留原有逻辑，新增详细度要求（和你之前要求的"多内容、多字数"一致）
    prompt = f"""
    你是世界技能大赛总教练，现在针对选手{username}的训练日【{training_day_data['training_day_name']}】生成整体训练分析报告。
    【训练日基础数据】：
    - 训练项目总数：{project_count}个
    - 已完成项目数：{len(finished_projects)}个
    - 训练总时长：{total_duration}秒（{round(total_duration/60, 2)}分钟）
    - 各项目得分情况：{json.dumps(project_summary, ensure_ascii=False)}
    - 项目平均得分：{avg_score}分
    - 总扣分值：{total_deduction}分

    【分析要求】：
    1. 给出整体训练评分（0-100分），基于各项目平均分、完成度、扣分情况综合评定；
    2. 汇总所有项目的扣分项，找出高频错误、核心短板（详细描述，至少列出3个高频错误）；
    3. 用时分析：总时长是否符合大赛标准，各项目用时是否合理，哪些项目偏快/偏慢，原因是什么（详细分析）；
    4. 优势分析：本次训练中表现好的地方（至少列出2点，详细描述）；
    5. 整体改进建议：针对核心短板给出可落地的训练计划，至少3条，每条建议需包含具体训练方法、频次、验收标准；
    6. 项目排名：按得分从高到低排序，列出所有完成项目的排名、得分、差距分析；
    7. 尽量多的尽可能精确的描述内容，字数尽量多，分析维度尽量全面，禁止精简内容；
    8. 输出严格JSON格式，禁止额外内容、注释、换行、反引号、列表包裹。

    【输出格式】：严格返回纯JSON字符串，仅返回JSON，字段如下：
    {{
        "overall_score": 整体评分（数字0-100）,
        "high_freq_deductions": ["高频扣分项1", "高频扣分项2", "高频扣分项3"],
        "core_shortcomings": ["核心短板1", "核心短板2", "核心短板3"],
        "time_overall_analysis": "整体用时分析（详细描述，不少于50字）",
        "advantage_analysis": "优势分析（详细描述，不少于50字）",
        "overall_improvement_suggestions": ["整体改进建议1（详细）", "整体改进建议2（详细）", "整体改进建议3（详细）"],
        "project_rank": [{{"project_name": "项目名", "score": 得分, "rank": 排名, "gap_analysis": "与最高分的差距分析"}}]
    }}
    """
    
    try:
        print("开始调用Qwen3.5-Plus生成训练日整体汇总报告...")
        
        # 构建messages（适配Qwen3.5-Plus的调用格式）
        messages = [
            {
                "role": "user",
                "content": [{"text": prompt}]  # 纯文本请求，无需图片
            }
        ]
        
        # 核心修改：调用Qwen3.5-Plus（替换原Generation.call）
        response = dashscope.MultiModalConversation.call(
            api_key=DASHSCOPE_API_KEY,
            model='qwen3.5-plus',  # 改为qwen3.5-plus
            messages=messages
        )
        
        if response.status_code == 200:
            print(f"Qwen3.5-Plus调用成功，开始解析汇总结果")
            
            try:
                # 第一步：获取原始返回内容并打印日志
                raw_content = response.output.choices[0].message.content
                print(f"汇总报告原始返回内容（前500字符）：{str(raw_content)[:500]}...")
                
                # 第二步：处理不同类型的返回内容（核心修复逻辑，和photoelectric函数一致）
                summary_result_str = ""
                if isinstance(raw_content, list):
                    print(f"返回内容是List类型，长度：{len(raw_content)}，开始提取嵌套的JSON字符串")
                    # 遍历List，提取text字段中的JSON字符串
                    for item in raw_content:
                        if isinstance(item, dict) and "text" in item:
                            summary_result_str = item["text"].strip()
                            print(f"从List中提取到JSON字符串（前200字符）：{summary_result_str[:200]}...")
                            break
                    # 兜底：取List第一个元素转为字符串
                    if not summary_result_str and len(raw_content) > 0:
                        summary_result_str = str(raw_content[0]).strip()
                elif isinstance(raw_content, dict):
                    print(f"返回内容是Dict类型，提取text字段")
                    summary_result_str = raw_content.get("text", "").strip()
                elif isinstance(raw_content, (str, bytes, bytearray)):
                    print(f"返回内容是字符串类型，直接使用")
                    summary_result_str = str(raw_content).strip()
                else:
                    raise Exception(f"不支持的返回类型：{type(raw_content)}")
                
                # 第三步：清理JSON字符串（移除反引号、换行、空格）
                if not summary_result_str:
                    raise Exception("提取到的汇总JSON字符串为空")
                
                summary_result_str = summary_result_str.replace("```json", "").replace("```", "").replace("\n", "").replace("\r", "").strip()
                print(f"清理后的汇总JSON字符串（前200字符）：{summary_result_str[:200]}...")
                
                # 第四步：解析为字典并校验类型
                summary_result = json.loads(summary_result_str)
                if not isinstance(summary_result, dict):
                    raise Exception(f"解析后不是字典类型，而是：{type(summary_result)}")
                
                # 兜底校验：确保整体评分在0-100之间
                summary_result["overall_score"] = max(0, min(100, summary_result.get("overall_score", avg_score)))
                print(f"✅ 汇总报告解析成功，整体评分：{summary_result['overall_score']}")
                return summary_result
            
            except json.JSONDecodeError as e:
                print(f"解析汇总结果失败（JSON格式错误）：{str(e)}")
                print(f"失败的内容：{summary_result_str[:500]}")
                # 原有兜底返回值保留
                return {
                    "overall_score": avg_score,
                    "high_freq_deductions": ["解析失败，无数据"],
                    "core_shortcomings": ["解析失败，无数据"],
                    "time_overall_analysis": "无法分析",
                    "advantage_analysis": "解析失败",
                    "overall_improvement_suggestions": ["重新生成汇总报告", "检查项目分析数据"],
                    "project_rank": []
                }
            except Exception as e:
                print(f"解析汇总结果时发生错误：{str(e)}")
                # 原有兜底返回值保留
                return {
                    "overall_score": avg_score,
                    "high_freq_deductions": ["解析错误，无数据"],
                    "core_shortcomings": ["解析错误，无数据"],
                    "time_overall_analysis": "无法分析",
                    "advantage_analysis": "解析出错",
                    "overall_improvement_suggestions": ["重启后端服务", "检查项目分析数据完整性"],
                    "project_rank": []
                }
        else:
            print(f"Qwen3.5-Plus调用失败：{response.code} - {response.message}")
            # 原有兜底返回值保留
            return {
                "overall_score": avg_score,
                "high_freq_deductions": ["调用失败，无数据"],
                "core_shortcomings": ["调用失败，无数据"],
                "time_overall_analysis": "无法分析",
                "advantage_analysis": "调用失败",
                "overall_improvement_suggestions": ["检查网络后重试"],
                "project_rank": []
            }
    except Exception as e:
        print(f"调用Qwen3.5-Plus生成汇总报告出错：{str(e)}")
        # 原有兜底返回值保留
        return {
            "overall_score": avg_score,
            "high_freq_deductions": ["调用出错，无数据"],
            "core_shortcomings": ["调用出错，无数据"],
            "time_overall_analysis": "无法分析",
            "advantage_analysis": "调用出错",
            "overall_improvement_suggestions": ["重启后端服务后重试"],
            "project_rank": []
        }
    


def call_qwen_training_plan(training_day_data: dict, username: str):
    """基于训练日分析数据生成个性化训练计划（适配Qwen3.5-Plus调用，复用解析逻辑）"""
    # 1. 提取训练日核心数据（和示例代码结构一致）
    training_day_name = training_day_data["training_day_name"]
    overall_score = training_day_data.get("overall_score", 0)
    project_list = training_day_data["project_list"]
    finished_projects = [p for p in project_list if p["is_analyzed"]]
    # 提取薄弱项目（得分<80分）核心信息
    weak_projects = []
    for p in finished_projects:
        score = p["analysis_result"].get("project_score", 0)
        if score < 80:
            weak_projects.append({
                "project_name": p["project_name"],
                "score": score,
                "main_problem": p["analysis_result"].get("action_norm_analysis", ""),
                "deduction_items": p["analysis_result"].get("deduction_items", []),
                "error_count": p["analysis_result"].get("step_error_count", 0)
            })
    # 提取优势项目（得分≥80分）
    advantage_projects = [p for p in finished_projects if p["analysis_result"].get("project_score", 0) >= 80]

    # 2. 构造精准Prompt（严格要求JSON格式，和示例代码的prompt风格一致）
    prompt = f"""
    你是世界技能大赛光电项目专属教练，现在针对选手{username}的训练日【{training_day_name}】生成个性化训练计划。
    【训练日核心数据】：
    - 训练日名称：{training_day_name}
    - 整体评分：{overall_score}分
    - 已完成项目数：{len(finished_projects)}个
    - 薄弱项目（<80分）：{json.dumps(weak_projects, ensure_ascii=False)}
    - 优势项目（≥80分）：{[p['project_name'] for p in advantage_projects]}

    【训练计划生成要求】：
    1. 计划需聚焦薄弱项目整改，严格对标世界技能大赛考核标准；
    2. 训练周期建议14天，分天计划需包含每日主题、目标、具体训练内容、方法、验收标准；
    3. 内容要求：尽量多的精确描述，字数尽可能多，分析维度全面，禁止精简内容；
    4. 输出严格JSON格式（仅返回JSON，无任何额外内容、注释、换行、反引号），字段如下：
    {{
        "plan_title": "训练计划标题（含选手名+训练日+专项）",
        "plan_desc": "计划描述（≥100字，说明训练背景、目标、周期）",
        "plan_days": 训练天数（数字，建议14）,
        "core_goal": "核心目标（≥100字，明确各薄弱项整改目标）",
        "daily_plans": [
            {{
                "theme": "当日训练主题",
                "daily_goal": "当日目标（≥50字）",
                "project_plans": [
                    {{
                        "project_name": "项目名称",
                        "training_content": "训练内容（≥100字）",
                        "training_methods": ["训练方法1", "训练方法2"],
                        "acceptance_criteria": "验收标准（≥50字）",
                        "notes": "注意事项（≥50字）"
                    }}
                ],
                "daily_summary": "当日总结（≥50字）",
                "next_day_tips": "次日预习提示（最后一天为空字符串）"
            }}
        ],
        "plan_summary": "计划总结（≥200字，总结整体训练逻辑、预期效果）",
        "execution_suggestion": "执行建议（≥100字，含训练频次、监督方式、验收标准）"
    }}
    """
    
    try:
        print("开始调用Qwen3.5-Plus生成个性化训练计划...")
        
        # 3. 调用Qwen3.5-Plus（完全复用示例代码的调用逻辑）
        messages = [
            {
                "role": "user",
                "content": [{"text": prompt}]  # 纯文本请求，和示例代码一致
            }
        ]
        
        response = dashscope.MultiModalConversation.call(
            api_key=DASHSCOPE_API_KEY,
            model='qwen3.5-plus',  # 统一使用qwen3.5-plus
            messages=messages
        )
        
        if response.status_code == 200:
            print(f"Qwen3.5-Plus调用成功，开始解析训练计划结果")
            
            try:
                # 4. 解析返回结果（完全复用示例代码的核心修复逻辑）
                raw_content = response.output.choices[0].message.content
                print(f"训练计划原始返回内容（前500字符）：{str(raw_content)[:500]}...")
                
                # 处理不同类型的返回内容
                plan_result_str = ""
                if isinstance(raw_content, list):
                    print(f"返回内容是List类型，长度：{len(raw_content)}，开始提取嵌套的JSON字符串")
                    for item in raw_content:
                        if isinstance(item, dict) and "text" in item:
                            plan_result_str = item["text"].strip()
                            print(f"从List中提取到JSON字符串（前200字符）：{plan_result_str[:200]}...")
                            break
                    if not plan_result_str and len(raw_content) > 0:
                        plan_result_str = str(raw_content[0]).strip()
                elif isinstance(raw_content, dict):
                    print(f"返回内容是Dict类型，提取text字段")
                    plan_result_str = raw_content.get("text", "").strip()
                elif isinstance(raw_content, (str, bytes, bytearray)):
                    print(f"返回内容是字符串类型，直接使用")
                    plan_result_str = str(raw_content).strip()
                else:
                    raise Exception(f"不支持的返回类型：{type(raw_content)}")
                
                # 清理JSON字符串（移除干扰字符）
                if not plan_result_str:
                    raise Exception("提取到的训练计划JSON字符串为空")
                
                plan_result_str = plan_result_str.replace("```json", "").replace("```", "").replace("\n", "").replace("\r", "").strip()
                print(f"清理后的训练计划JSON字符串（前200字符）：{plan_result_str[:200]}...")
                
                # 解析为字典并校验
                plan_result = json.loads(plan_result_str)
                if not isinstance(plan_result, dict):
                    raise Exception(f"解析后不是字典类型，而是：{type(plan_result)}")
                
                print(f"✅ 训练计划解析成功，计划标题：{plan_result.get('plan_title', '未知')}")
                return plan_result
            
            except json.JSONDecodeError as e:
                print(f"解析训练计划失败（JSON格式错误）：{str(e)}")
                print(f"失败的内容：{plan_result_str[:500]}")
                # 兜底返回（保证前端能正常接收）
                return {
                    "plan_title": f"{username} 光电项目训练计划",
                    "plan_desc": "训练计划生成失败（JSON解析错误）",
                    "plan_days": 14,
                    "core_goal": "解析失败，无核心目标",
                    "daily_plans": [],
                    "plan_summary": "解析失败，无计划总结",
                    "execution_suggestion": "请重新生成训练计划"
                }
            except Exception as e:
                print(f"解析训练计划时发生错误：{str(e)}")
                return {
                    "plan_title": f"{username} 光电项目训练计划",
                    "plan_desc": "训练计划生成失败（解析异常）",
                    "plan_days": 14,
                    "core_goal": "解析异常，无核心目标",
                    "daily_plans": [],
                    "plan_summary": "解析异常，无计划总结",
                    "execution_suggestion": "重启后端服务后重新生成"
                }
        else:
            print(f"Qwen3.5-Plus调用失败：{response.code} - {response.message}")
            return {
                "plan_title": f"{username} 光电项目训练计划",
                "plan_desc": "训练计划生成失败（调用接口失败）",
                "plan_days": 14,
                "core_goal": "接口调用失败，无核心目标",
                "daily_plans": [],
                "plan_summary": "接口调用失败，无计划总结",
                "execution_suggestion": "检查API密钥和网络后重试"
            }
    except Exception as e:
        print(f"调用Qwen3.5-Plus生成训练计划出错：{str(e)}")
        return {
            "plan_title": f"{username} 光电项目训练计划",
            "plan_desc": "训练计划生成失败（系统异常）",
            "plan_days": 14,
            "core_goal": "系统异常，无核心目标",
            "daily_plans": [],
            "plan_summary": "系统异常，无计划总结",
            "execution_suggestion": "联系管理员排查后端服务"
        }