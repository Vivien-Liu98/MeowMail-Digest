import argparse
import json
from pathlib import Path
from copy import deepcopy
from datetime import datetime, timezone

# py tool_split.py -n 2 gmail_filtered.json

def split_evenly(items, n):
 #尽量均匀地把 items 拆成 n 份。
    total = len(items)

    base_size = total // n
    remainder = total % n

    chunks = []
    start = 0

    for i in range(n):
        # 前 remainder 份多分一个
        size = base_size + (1 if i < remainder else 0)

        end = start + size
        chunks.append(items[start:end])
        start = end

    return chunks


def build_output_filename(input_file, index):
#根据输入文件名生成输出文件名。
    return input_file.with_name(
        f"{input_file.stem}_{index}{input_file.suffix}"
    )


def main():
    parser = argparse.ArgumentParser(
        description="将 gmail_filtered.json 按指定份数拆分成多个 JSON 文件。"
    )

    parser.add_argument(
        "-n",
        "--num",
        type=int,
        required=True,
        help="拆分后文件数，例如 -n 2"
    )

    parser.add_argument(
        "input_file",
        type=str,
        help="要拆分的 JSON 文件，例如 gmail_filtered.json"
    )

    args = parser.parse_args()

    split_count = args.num
    input_file = Path(args.input_file).resolve()

    if split_count <= 0:
        raise ValueError("拆分数量必须大于 0。")

    if not input_file.exists():
        raise FileNotFoundError(f"找不到输入文件：{input_file}")

    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    messages = data.get("messages")

    if not isinstance(messages, list):
        raise ValueError("输入 JSON 中没有找到 messages 数组。")

    total_count = len(messages)

    if total_count == 0:
        print("输入文件中没有邮件，生成空拆分文件。")

    chunks = split_evenly(messages, split_count)

    for index, chunk in enumerate(chunks, start=1):
        output_data = deepcopy(data)

        output_data["messages"] = chunk
        output_data["count"] = len(chunk)

        # 如果原文件里有 filtered_count，也同步修正
        if "filtered_count" in output_data:
            output_data["filtered_count"] = len(chunk)

        # 保留原始统计信息，同时加入拆分信息
        output_data["split_info"] = {
            "source_file": input_file.name,
            "split_generated_at": datetime.now(timezone.utc).isoformat(),
            "split_index": index,
            "split_total": split_count,
            "source_message_count": total_count,
            "current_message_count": len(chunk),
        }

        output_file = build_output_filename(input_file, index)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print(f"已生成：{output_file}，邮件数：{len(chunk)}")

    print("拆分完成。")


if __name__ == "__main__":
    main()