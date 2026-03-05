import os
import asyncio
import edge_tts
import json
import pandas as pd
import random
from datetime import datetime

# File paths
TEXT_DIR = r"D:\dataset\data\text"
AUDIO_DIR = r"D:\dataset\data\audio"
JSON_DIR = r"D:\dataset\data\json"
EXCEL_PATH = r"D:\dataset\data\files_list.xlsx"

# Create directories if they do not exist
os.makedirs(TEXT_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(JSON_DIR, exist_ok=True)

# Parameters
START_NUM = 7026  # Start task number
TOTAL_FILES = 25  # Number of files to generate

# Time, items, locations (random letter), and actions
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
items = [
    "叠片盒", "料盒", "托盘", "连接器", "公插针", "轴", "平行销", "定位销", "圆头螺母", "保险丝", "锤子",
    "垫片", "螺丝刀", "内六角圆柱螺钉", "内六角圆柱螺钉带平垫", "内六角平端紧定螺", "平头螺母", "轴承", "齿轮",
    "螺栓", "弹簧", "电池", "万向轮", "航插电源线", "航插网线", "航插适配器", "内六角螺母", "uku单极分线器",
    "紧固件", "平垫", "平垫圈", "杯头内六角", "内六角圆柱头螺钉"
]
letters = [chr(i) for i in range(ord('A'), ord('Z') + 1)]  # Letters A to Z
years = [2025, 2026, 2027]
locations = [f"{random.choice(letters)}{num:03d}" for num in range(1, 31)]
# ✅ 动作词 -> task_type 映射（并保证 5 类 task_type 各 1/5 概率出现）
TASK_TYPE_TO_ACTIONS = {
    "MATERIAL_HANDLING": ["运送到", "搬运到", "运输到"],
    "MATERIAL_GRASPING": ["抓取到", "夹取到", "夹持到"],
    "MATERIAL_TRANSFER": ["转运到"],
    "MATERIAL_SORTING": ["拣选到", "分拣到"],
    "MATERIAL_STACKING": ["码垛到", "叠放到"],
}
TASK_TYPES = list(TASK_TYPE_TO_ACTIONS.keys())

# Available voices (you can add more voices to this list)
voices = [
    "zh-CN-XiaoxiaoNeural", "zh-CN-XiaoyiNeural", "zh-CN-YunjianNeural", "zh-CN-YunxiNeural", "zh-CN-YunxiaNeural", "zh-CN-YunyangNeural", "zh-CN-XiaoxuanNeural"
]

# Generate text commands and save parameters
texts = []
text_params = []  # 存储每个文本对应的参数，用于后续生成json
for i in range(TOTAL_FILES):
    time_idx = random.choice(times)
    # 随机选择两个不同的物品
    item1, item2, item3 = random.sample(items, 3)
    # 随机生成两个数量（1-15之间）
    quantity1 = random.randint(1, 15)
    quantity2 = random.randint(1, 15)
    quantity3 = random.randint(1, 15)
    loc_idx = random.choice(locations)
    # ✅ 先等概率选 5 类 task_type（每类 1/5），再在该类里随机挑动作词
    task_type = random.choice(TASK_TYPES)
    action_idx = random.choice(TASK_TYPE_TO_ACTIONS[task_type])
    year = random.choice(years)
    month = random.randint(1, 12)
    date = random.randint(1, 31)

    # 生成txt内容（包含两个物品和两个数量）
    text = f"请在{year}年{month}月{date}日{time_idx}让{quantity1}个{item1},{quantity2}个{item2}和{quantity3}个{item3}到{loc_idx}点位"
    texts.append(text)
    
    # 保存当前文本对应的参数（包含两个物品和两个数量）
    text_params.append({
        "time_idx": time_idx,
        "item1": item1,
        "item2": item2,
        "item3": item3,
        "loc_idx": loc_idx,
        "action_idx": action_idx,
        "task_type": task_type,
        "quantity1": quantity1,
        "quantity2": quantity2,
        "quantity3": quantity3,
        "year": year,
        "month": month,
        "date": date
    })

# Generate audio for each text command
async def generate_audio(text, output_path):
    voice = random.choice(voices)  # Randomly select a voice
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)
    print(f"已生成: {output_path}")

# Generate JSON files (更新为包含两个物品)
def generate_json(task_id, quantity1, quantity2, quantity3, item1, item2, item3, target, action_idx, task_type, year, month, date, time_idx):
    time_mapping = {
        "上午五点前": "05:00:00", "上午六点前": "06:00:00", "上午七点前": "07:00:00", "上午八点前": "08:00:00",
        "上午九点前": "09:00:00", "上午十点前": "10:00:00", "上午十一点前": "11:00:00", "上午十二点前": "12:00:00",
        "下午一点前": "13:00:00", "下午两点前": "14:00:00", "下午三点前": "15:00:00", "下午四点前": "16:00:00",
        "下午五点前": "17:00:00", "下午六点前": "18:00:00", "下午七点前": "19:00:00", "晚上八点前": "20:00:00",
        "晚上九点前": "21:00:00", "晚上十点前": "22:00:00"
    }

    # 防御性：未知 task_type 时回退到 action_idx 推断
    task_type = None
    
    deadline = f"{year:04d}-{month:02d}-{date:02d}T{time_mapping[time_idx]}Z"


    json_data = {
        "task_id": f"T{task_id:05d}",
        "task_type": task_type,
        "deadline": deadline,
        "requirements": {
            "part_list": [
                {
                    "part_no": item1,
                    "quantity": quantity1,
                    "target": target
                },
                {
                    "part_no": item2,
                    "quantity": quantity2,
                    "target": target
                },
                {
                    "part_no": item3,
                    "quantity": quantity3,
                    "target": target
                }
            ]
        }
    }
    return json_data

# Process all files and generate outputs
async def process_files():
    tasks = []
    excel_data = []

    for i in range(TOTAL_FILES):
        task_id = START_NUM + i
        file_name = f"T{task_id:05d}.txt"
        audio_name = f"T{task_id:05d}.wav"
        json_name = f"T{task_id:05d}.json"

        text_path = os.path.join(TEXT_DIR, file_name)
        audio_path = os.path.join(AUDIO_DIR, audio_name)
        json_path = os.path.join(JSON_DIR, json_name)

        # 获取当前txt文件的内容和对应参数
        text_content = texts[i]
        params = text_params[i]

        # Write text file
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(text_content)

        # Generate audio asynchronously
        task = generate_audio(text_content, audio_path)
        tasks.append(task)

        # 复用text生成时的参数生成JSON（包含两个物品）
        json_data = generate_json(
            task_id,
            quantity1=params["quantity1"],
            quantity2=params["quantity2"],
            quantity3=params["quantity3"],
            item1=params["item1"],
            item2=params["item2"],
            item3=params["item3"],
            target=params["loc_idx"],
            action_idx=params["action_idx"],
            task_type=params["task_type"],
            year=params["year"],
            month=params["month"],
            date=params["date"],
            time_idx=params["time_idx"]
        )

        # Write JSON file
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)

        # 准备Excel数据
        excel_data.append([
            file_name,
            text_content,
            json.dumps(json_data, ensure_ascii=False, indent=4),
            audio_name
        ])

    # Wait for all audio tasks to complete
    await asyncio.gather(*tasks)

    # 处理Excel文件
    columns = ["Text File", "Text Content", "JSON File", "Audio File"]
    new_df = pd.DataFrame(excel_data, columns=columns)
    
    if os.path.exists(EXCEL_PATH):
        existing_df = pd.read_excel(EXCEL_PATH)
        if "Text Content" not in existing_df.columns:
            existing_df.insert(1, "Text Content", "")
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        combined_df.to_excel(EXCEL_PATH, index=False)
        print(f"已追加 {TOTAL_FILES} 条记录到Excel文件")
    else:
        new_df.to_excel(EXCEL_PATH, index=False)
        print("Excel文件创建成功")

if __name__ == "__main__":
    asyncio.run(process_files())