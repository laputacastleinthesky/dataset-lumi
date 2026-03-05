# Chinese Audio-Text Command Dataset Generator + LoRA Fine-tuning Pipeline

本仓库提供一套**中文语音-文本指令数据集**的自动化生成脚本，适用于“中文语音/文本指令 → 结构化 JSON 指令”类任务。

---

## 1. 功能概览

### 1.1 数据生成（edge-tts / pydub / excel 记录）
- 随机采样：机器人、物料/零件、数量、目标点位、日期时间等字段
- 生成：
  - `text/Txxxxx.txt`：指令文本
  - `audio/Txxxxx.wav`：TTS 语音
  - `json/Txxxxx.json`：结构化标注（如 task_type、deadline、target 等）
- 记录到 `files_list.xlsx`（便于统计与追溯）

主要脚本包含：
- `dialog24.py / dialog24s1.py / dialog33.py`：对话/订单式指令生成（含“紧急/常规”、订单号、货箱位置信息等变体）
- `fuzzy1.py / fuzzy2.py`：更“自然/模糊表达”风格的指令变体
- `multi.py / multi2.py`：多物品/多数量/多字段组合指令
- `specific.py / specific2.py / specific3.py / specific3s1.py / specific3s2.py`：更结构化/更复杂的“特定模板”指令

> 多数脚本内部包含 `TASK_TYPE_TO_ACTIONS` 映射，并且让 5 类 task_type（HANDLING/GRASPING/TRANSFER/SORTING/STACKING）按 1/5 均匀出现，然后在每类内随机选动作词。  

---

### 1.2 训练与评估（LoRA）
- `split.py`：按 ID 划分 train/test（输出 `train_ids.txt` / `test_ids.txt`）
- `train.py`：LoRA 微调训练（Trainer）
- `eval.py`：对 test_ids 推理与指标计算（并导出 CSV/XLSX + 图表）
- `loss.py`：从 `trainer_state.json` 解析并绘制 `Epoch vs Loss`
- `run.sh`：一键跑通 split → train → eval → report

---

## 2. 仓库结构

.
├── README.md
├── requirements.txt
│
├── scripts/
│ ├── dataset/
│ │ ├── dialog24.py
│ │ ├── dialog24s1.py
│ │ ├── dialog33.py
│ │ ├── fuzzy1.py
│ │ ├── fuzzy2.py
│ │ ├── multi.py
│ │ ├── multi2.py
│ │ ├── specific.py
│ │ ├── specific2.py
│ │ ├── specific3.py
│ │ ├── specific3s1.py
│ │ └── specific3s2.py

---

## 3. 数据集格式约定（ID 对齐）

所有流程都依赖 **ID 对齐**（例如 `T00001`）：

- `data/text/T00001.txt`
- `data/audio/T00001.wav`
- `data/json/T00001.json`

---

## 4. 环境依赖

### 4.1 Python 依赖（建议 Python 3.10+）
- edge-tts
- asyncio（标准库）
- pandas
- numpy
- matplotlib
- tqdm
- torch / transformers / peft（训练时）
- torchaudio（训练/音频特征时）
- openpyxl（导出 xlsx 时）

### 4.2 ffmpeg（仅部分数据生成脚本需要）
部分脚本用到了 `pydub.AudioSegment` 并且在脚本里**硬编码指定 ffmpeg.exe 路径**，使用时需要把它改成自己的路径：
- 例如：`AudioSegment.converter = r"F:\ffmpeg\...\ffmpeg.exe"`

---

## 5. 快速开始

### 5.1 生成数据（示例）
1) 打开某个生成脚本（如 `dialog24.py`）
2) 修改里面的输出目录：
   - TEXT_DIR / AUDIO_DIR / JSON_DIR / EXCEL_PATH
3) 修改生成数量：
   - START_NUM（起始 ID）
   - TOTAL_FILES（生成条数）
4) 运行：
```bash
python scripts/dataset/dialog24.py
