import os
import json
import cv2
from datetime import datetime
from config import ANALYSIS_DIR

def save_analysis_record(username, filename, video_path, analysis_result):
    """保存分析记录到JSON文件"""
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    video_duration = round(total_frames / fps, 2) if fps and total_frames else 0
    cap.release()
    
    record = {
        "id": f"analysis_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
        "username": username,
        "video_filename": filename,
        "video_path": video_path.replace("\\", "/"),
        "video_duration": video_duration,
        "analysis_result": analysis_result,
        "analysis_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    record_file = os.path.join(ANALYSIS_DIR, f"{record['id']}.json")
    with open(record_file, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=4)
    
    return record

def get_analysis_history(username):
    """获取指定用户的分析历史记录"""
    records = []
    for file in os.listdir(ANALYSIS_DIR): 
        if file.endswith(".json"):
            try:
                with open(os.path.join(ANALYSIS_DIR, file), "r", encoding="utf-8") as f:
                    record = json.load(f)
                    if record.get("username") == username:
                        records.append(record)
            except Exception as e:
                print(f"读取分析记录失败：{file}，错误：{str(e)}")
    
    records.sort(key=lambda x: x["analysis_time"], reverse=True)
    return records