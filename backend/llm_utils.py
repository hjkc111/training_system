import json
import dashscope
import base64
from dashscope import Generation
from config import DASHSCOPE_API_KEY

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
    
# ------------------- 新增：单项目专项分析（适配比赛项目） -------------------
def call_qwen_project_analysis(project_name: str, project_desc: str, video_text: str, key_frames_base64: list, username: str, is_audio_useful: bool):
    """针对单个比赛项目的专项AI分析，适配世界技能大赛标准"""
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

    【输出格式】：严格JSON字符串，字段如下：
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
        print(f"开始调用Qwen进行【{project_name}】专项分析...")
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
            temperature=0.1,
            top_p=0.9,
            max_tokens=2000
        )
        
        if response.status_code == 200:
            usage = response.usage
            print(f"Qwen Token消耗: 输入={usage.input_tokens}, 输出={usage.output_tokens}, 总计={usage.total_tokens}")
            
            try:
                analysis_result = json.loads(response.output.choices[0].message.content)
                # 兜底校验
                if analysis_result.get("project_score", 0) < 0:
                    analysis_result["project_score"] = 0
                return analysis_result
            except json.JSONDecodeError as e:
                print(f"解析大模型结果失败：{str(e)}")
                return {
                    "project_name": project_name,
                    "project_score": 20,
                    "operation_duration": 0,
                    "step_completed_count": 0,
                    "step_error_count": 0,
                    "deduction_items": [{"reason": "解析结果失败", "deduction_score": 0}],
                    "correct_items": ["无"],
                    "time_analysis": "无法分析",
                    "action_norm_analysis": "解析失败",
                    "improvement_suggestions": ["重新上传清晰视频", "确保操作完整入镜", "同步口述操作步骤"]
                }
        else:
            print(f"大模型调用失败：{response.message}")
            return {
                "project_name": project_name,
                "project_score": 20,
                "operation_duration": 0,
                "step_completed_count": 0,
                "step_error_count": 0,
                "deduction_items": [{"reason": "大模型调用失败", "deduction_score": 0}],
                "correct_items": ["无"],
                "time_analysis": "无法分析",
                "action_norm_analysis": "调用失败",
                "improvement_suggestions": ["检查网络后重试", "缩短视频时长", "确保视频格式正确"]
            }
    except Exception as e:
        print(f"调用Qwen出错：{str(e)}")
        return {
            "project_name": project_name,
            "project_score": 20,
            "operation_duration": 0,
            "step_completed_count": 0,
            "step_error_count": 0,
            "deduction_items": [{"reason": "调用出错", "deduction_score": 0}],
            "correct_items": ["无"],
            "time_analysis": "无法分析",
            "action_norm_analysis": "调用出错",
            "improvement_suggestions": ["重启后端服务", "检查视频文件", "确保FFmpeg环境正常"]
        }

# ------------------- 新增：训练日整体汇总分析 -------------------
def call_qwen_training_summary(training_day_data: dict, username: str):
    """基于训练日所有项目的分析结果，生成整体汇总报告"""
    project_list = training_day_data["project_list"]
    project_count = len(project_list)
    finished_projects = [p for p in project_list if p["is_analyzed"]]
    total_duration = training_day_data["total_duration"]

    # 整理所有项目的核心数据
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
    2. 汇总所有项目的扣分项，找出高频错误、核心短板；
    3. 用时分析：总时长是否符合大赛标准，各项目用时是否合理，哪些项目偏快/偏慢，原因是什么；
    4. 优势分析：本次训练中表现好的地方；
    5. 整体改进建议：针对核心短板给出可落地的训练计划，至少3条；
    6. 输出严格JSON格式，禁止额外内容。

    【输出格式】：严格JSON字符串，字段如下：
    {{
        "overall_score": 整体评分（数字0-100）,
        "high_freq_deductions": ["高频扣分项1", "高频扣分项2"],
        "core_shortcomings": ["核心短板1", "核心短板2"],
        "time_overall_analysis": "整体用时分析",
        "advantage_analysis": "优势分析",
        "overall_improvement_suggestions": ["整体改进建议1", "整体改进建议2", "整体改进建议3"],
        "project_rank": [{{"project_name": "项目名", "score": 得分, "rank": 排名}}]
    }}
    """
    
    try:
        print("开始调用Qwen生成训练日整体汇总...")
        response = Generation.call(
            model="qwen-plus",
            api_key=DASHSCOPE_API_KEY,
            messages=[{"role": "user", "content": prompt}],
            result_format="json",
            temperature=0.1,
            top_p=0.9,
            max_tokens=2000
        )
        
        if response.status_code == 200:
            usage = response.usage
            print(f"汇总分析Token消耗: 输入={usage.input_tokens}, 输出={usage.output_tokens}, 总计={usage.total_tokens}")
            
            try:
                summary_result = json.loads(response.output.choices[0].message.content)
                if summary_result.get("overall_score", 0) < 0:
                    summary_result["overall_score"] = avg_score
                return summary_result
            except json.JSONDecodeError as e:
                print(f"解析汇总结果失败：{str(e)}")
                return {
                    "overall_score": avg_score,
                    "high_freq_deductions": ["解析失败，无数据"],
                    "core_shortcomings": ["解析失败，无数据"],
                    "time_overall_analysis": "无法分析",
                    "advantage_analysis": "解析失败",
                    "overall_improvement_suggestions": ["重新生成汇总报告", "检查项目分析数据"],
                    "project_rank": []
                }
        else:
            print(f"大模型调用失败：{response.message}")
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
        print(f"调用Qwen汇总分析出错：{str(e)}")
        return {
            "overall_score": avg_score,
            "high_freq_deductions": ["调用出错，无数据"],
            "core_shortcomings": ["调用出错，无数据"],
            "time_overall_analysis": "无法分析",
            "advantage_analysis": "调用出错",
            "overall_improvement_suggestions": ["重启后端服务后重试"],
            "project_rank": []
        }