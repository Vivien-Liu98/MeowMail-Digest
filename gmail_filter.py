import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

INPUT_FILE = BASE_DIR / "gmail_output.json"
SUBS_FILE = BASE_DIR / "subs_list.txt"
OUTPUT_FILE = BASE_DIR / "gmail_filtered.json"


def normalize_email(email):
    return (email or "").strip().lower()


def load_subs_list():
 # 读取 subs_list.txt。
    if not SUBS_FILE.exists():
        print(f"未找到订阅列表文件：{SUBS_FILE}")
        print("将视为没有需要过滤的发件人。")
        return set()

    subs = set()

    with open(SUBS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            if line.startswith("#"):
                continue

            subs.add(normalize_email(line))

    return subs


def load_gmail_output():
  #读取 gmail_output.json。
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"找不到输入文件：{INPUT_FILE}")

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_filtered_output(original_data, filtered_messages, removed_messages):
  # 保存过滤后的结果到 gmail_filtered.json。
    output_data = {
        "source_file": INPUT_FILE.name,
        "mode": original_data.get("mode"),
        "generated_at": original_data.get("generated_at"),
        "original_count": len(original_data.get("messages", [])),
        "filtered_count": len(filtered_messages),
        "removed_count": len(removed_messages),
        "messages": filtered_messages,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"过滤完成，结果已写入：{OUTPUT_FILE}")
    print(f"原始邮件数：{output_data['original_count']}")
    print(f"过滤后邮件数：{output_data['filtered_count']}")
    print(f"移除邮件数：{output_data['removed_count']}")


def main():
    subs = load_subs_list()
    data = load_gmail_output()

    messages = data.get("messages", [])

    filtered_messages = []
    removed_messages = []

    for msg in messages:
        sender = normalize_email(msg.get("from"))

        if sender in subs:
            removed_messages.append(msg)
        else:
            filtered_messages.append(msg)

    save_filtered_output(
        original_data=data,
        filtered_messages=filtered_messages,
        removed_messages=removed_messages,
    )


if __name__ == "__main__":
    main()