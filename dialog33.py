# dialog_generate.py
import os
import asyncio
import edge_tts
import json
import pandas as pd
import random
from datetime import datetime
from pydub import AudioSegment
import tempfile
import shutil
from pydub import AudioSegment
import os

# 强制指定 ffmpeg 路径（关键！）
AudioSegment.converter = r"F:\ffmpeg\ffmpeg-8.0.1-essentials_build\bin\ffmpeg.exe"  # 替换为你的 ffmpeg.exe 路径

# -------------------------
# Configuration (请按需修改)
# -------------------------
TEXT_DIR = r"F:\command_dataset\dataset\metadata\text"
AUDIO_DIR = r"F:\command_dataset\dataset\metadata\audio"
JSON_DIR = r"F:\command_dataset\dataset\metadata\json"
EXCEL_PATH = r"F:\command_dataset\dataset\metadata\files_list.xlsx"

os.makedirs(TEXT_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(JSON_DIR, exist_ok=True)

START_NUM = 5501      # 起始编号
TOTAL_FILES = 100     # 生成数量（按需修改）

# 语料池（保留或按需扩展）
robots = [
    "1号移动机器人","1号复合机器人","2号移动机器人","2号复合机器人","3号移动机器人","3号复合机器人",
    "4号移动机器人","4号复合机器人","5号移动机器人","5号复合机器人","6号移动机器人","6号复合机器人"
]
places = [
    "1号货架","2号货架","3号货架","4号货架","5号货架","6号货架","7号货架",
    "1号货箱","2号货箱","3号货箱","4号货箱","5号货箱","6号货箱","7号货箱",
    "1号仓库","2号仓库","3号仓库","4号仓库","5号仓库","6号仓库","7号仓库"
]
times = [
    "上午五点前", "上午六点前", "上午七点前", "上午八点前", "上午九点前", "上午十点前", "上午十一点前",
    "上午十二点前", "下午一点前", "下午两点前", "下午三点前", "下午四点前", "下午五点前", "下午六点前",
    "下午七点前", "晚上八点前", "晚上九点前", "晚上十点前"
]
# 常用物品（示例，已包含大量项）
items = [
    "叠片盒", "料盒", "托盘", "连接器", "公插针", "轴", "平行销", "定位销", "圆头螺母", "保险丝", "锤子",
    "垫片", "螺丝刀", "内六角圆柱螺钉", "内六角圆柱螺钉带平垫", "内六角平端紧定螺", "平头螺母", "轴承", "齿轮",
    "螺栓", "弹簧", "电池", "万向轮", "航插电源线", "航插网线"
]
letters = [chr(i) for i in range(ord('A'), ord('Z') + 1)]
locations = [f"{random.choice(letters)}{num:03d}" for num in range(1, 31)]
actions = ["运送至", "抓取至", "搬运至", "输送至"]

# 可用声线（示例，按 edge-tts 可用语音填写）
voices = [
    "zh-CN-XiaoxiaoNeural", "zh-CN-XiaoyiNeural", "zh-CN-YunjianNeural", "zh-CN-YunxiNeural", "zh-CN-YunxiaNeural", "zh-CN-YunyangNeural", "zh-CN-XiaoxuanNeural"
]

# -------------------------
# 辅助函数
# -------------------------
def generate_dialog_text(params):
    """返回 a_text, b_text, c_text, full_dialog"""
    loc_idx = params["loc_idx"]
    quantity1 = params["quantity1"]
    quantity2 = params["quantity2"]
    quantity3 = params["quantity3"]
    item1 = params["item1"]
    item2 = params["item2"]
    item3 = params["item3"]
    robot_idx = params["robot_idx"]
    month = params["month"]
    date = params["date"]
    time_idx = params["time_idx"]
    action_idx = params["action_idx"]

    a_text = f"我在{loc_idx}点位,需要{quantity1}个{item1}和{quantity2}个{item2}"
    b_text = f"我也在{loc_idx}点位,需要{quantity3}个{item3}"
    c_text = f"请{robot_idx}在2025年{month}月{date}日{time_idx}将目标物品{action_idx}目标点位"
    full_dialog = f"A: {a_text}\nB: {b_text}\nC: {c_text}"
    return a_text, b_text, c_text, full_dialog

def make_json(task_id, params):
    """生成 JSON 数据结构"""
    time_mapping = {
        "上午五点前": "05:00:00", "上午六点前": "06:00:00", "上午七点前": "07:00:00", "上午八点前": "08:00:00",
        "上午九点前": "09:00:00", "上午十点前": "10:00:00", "上午十一点前": "11:00:00", "上午十二点前": "12:00:00",
        "下午一点前": "13:00:00", "下午两点前": "14:00:00", "下午三点前": "15:00:00", "下午四点前": "16:00:00",
        "下午五点前": "17:00:00", "下午六点前": "18:00:00", "下午七点前": "19:00:00", "晚上八点前": "20:00:00",
        "晚上九点前": "21:00:00", "晚上十点前": "22:00:00"
    }
    action_idx = params["action_idx"]
    task_type = "MATERIAL_HANDLING" if action_idx in ["运送至", "搬运至", "输送至"] else "MATERIAL_GRASPING"
    month = params["month"]
    date = params["date"]
    time_idx = params["time_idx"]
    deadline = f"2025-{month:02d}-{date:02d}T{time_mapping[time_idx]}Z"

    json_data = {
        "task_id": f"T{task_id:05d}",
        "task_type": task_type,
        "deadline": deadline,
        "requirements": {
            "part_list": [
                {"part_no": params["item1"], "quantity": params["quantity1"], "target": params["loc_idx"]},
                {"part_no": params["item2"], "quantity": params["quantity2"], "target": params["loc_idx"]},
                {"part_no": params["item3"], "quantity": params["quantity3"], "target": params["loc_idx"]}
            ]
        }
    }
    return json_data

async def synthesize_to_file(text, voice, out_path):
    """
    使用 edge-tts 合成到文件（异步）。
    out_path: 可带任何扩展，pydub 会根据文件内容自动识别。
    """
    # edge-tts 使用 Communicate(text, voice=...)
    communicate = edge_tts.Communicate(text, voice=voice)
    await communicate.save(out_path)
    # save() 完成后文件应存在
    return out_path

def concat_audio_files(file_list, out_wav_path):
    """
    使用 pydub 将多个音频片段拼接并导出为 WAV（采样率/通道由 pydub/ffmpeg 处理）。
    file_list: 按顺序的文件路径列表
    """
    if not file_list:
        raise ValueError("file_list 为空")
    # 读取第一个并逐一 append
    combined = AudioSegment.from_file(file_list[0])
    for f in file_list[1:]:
        seg = AudioSegment.from_file(f)
        combined += seg
    # 导出为 wav
    combined.export(out_wav_path, format="wav")
    return out_wav_path

# -------------------------
# 主流程
# -------------------------
async def process_all():
    # 先构造所有文本参数（与原文件逻辑相同）
    dialogs_params = []
    for i in range(TOTAL_FILES):
        robot_idx = random.choice(robots)
        time_idx = random.choice(times)
        item1, item2, item3 = random.sample(items, 3)
        quantity1 = random.randint(1, 15)
        quantity2 = random.randint(1, 15)
        quantity3 = random.randint(1, 15)
        loc_idx = random.choice(locations)
        action_idx = random.choice(actions)
        month = random.randint(1, 12)
        date = random.randint(1, 28)  # 为了避免2月/31日问题，取1-28
        params = {
            "robot_idx": robot_idx,
            "time_idx": time_idx,
            "item1": item1,
            "item2": item2,
            "item3": item3,
            "loc_idx": loc_idx,
            "action_idx": action_idx,
            "quantity1": quantity1,
            "quantity2": quantity2,
            "quantity3": quantity3,
            "month": month,
            "date": date
        }
        dialogs_params.append(params)

    # Excel 准备
    excel_data = []
    # 临时目录，用于存放中间段文件
    tmp_root = tempfile.mkdtemp(prefix="dialog_tts_tmp_")

    try:
        for i, params in enumerate(dialogs_params):
            task_id = START_NUM + i
            file_base = f"T{task_id:05d}"
            txt_path = os.path.join(TEXT_DIR, f"{file_base}.txt")
            json_path = os.path.join(JSON_DIR, f"{file_base}.json")
            wav_path = os.path.join(AUDIO_DIR, f"{file_base}.wav")

            a_text, b_text, c_text, full_dialog = generate_dialog_text(params)
            # 写入 txt（对话文本）
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(full_dialog)

            # 生成 json 数据并写文件
            json_data = make_json(task_id, params)
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(json_data, f, ensure_ascii=False, indent=4)

            # 随机选择三个**不同**的声线
            if len(voices) < 3:
                raise ValueError("voices 列表需要至少两个不同的声线")
            voice_a, voice_b, voice_c = random.sample(voices, 3)

            # 合成两个片段到临时文件
            tmp_a = os.path.join(tmp_root, f"{file_base}_A.mp3")
            tmp_b = os.path.join(tmp_root, f"{file_base}_B.mp3")
            tmp_c = os.path.join(tmp_root, f"{file_base}_C.mp3")
            # 使用 edge-tts 合成（异步）
            await synthesize_to_file(a_text, voice_a, tmp_a)
            await synthesize_to_file(b_text, voice_b, tmp_b)
            await synthesize_to_file(c_text, voice_c, tmp_c)

            # 拼接并导出为 wav
            concat_audio_files([tmp_a, tmp_b, tmp_c], wav_path)

            # 删除临时片段（可选）
            try:
                os.remove(tmp_a)
                os.remove(tmp_b)
                os.remove(tmp_c)
            except OSError:
                pass

            # 收集 Excel 一行：保持原始顺序（Text Path, JSON Path, Audio Path, timestamp）
            excel_data.append({
                "Text File": f"{file_base}.txt",
                "Text Content": full_dialog,
                "JSON File": json.dumps(json_data, ensure_ascii=False, indent=4),
                "Audio File": f"{file_base}.wav"
            })

            print(f"[{i+1}/{TOTAL_FILES}] 生成完成: {file_base} (wav/json/txt)")

        # 写入 Excel（追加或创建）
        df_new = pd.DataFrame(excel_data, columns=["Text File", "Text Content", "JSON File", "Audio File"])

        if os.path.exists(EXCEL_PATH):
            try:
                df_exist = pd.read_excel(EXCEL_PATH)
            except Exception:
                # 如果读取失败，直接保存新表
                df_new.to_excel(EXCEL_PATH, index=False)
            else:
                # 保持原有列并追加新行
                df_combined = pd.concat([df_exist, df_new], ignore_index=True)
                df_combined.to_excel(EXCEL_PATH, index=False)
            print(f"已将 {len(df_new)} 条记录写入（追加到）Excel: {EXCEL_PATH}")
        else:
            df_new.to_excel(EXCEL_PATH, index=False)
            print(f"已创建 Excel 并写入 {len(df_new)} 条记录: {EXCEL_PATH}")
    finally:
        # 清理临时目录
        shutil.rmtree(tmp_root, ignore_errors=True)


if __name__ == "__main__":
    asyncio.run(process_all())
