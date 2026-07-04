import sys
import subprocess
from pathlib import Path
from datetime import datetime


BASE_DIR = Path(__file__).resolve().parent

# 必须存在的脚本文件
REQUIRED_SCRIPT_FILES = [
    "gmail_fetch.py",
    "gmail_filter.py",
    "send2ds.py",
]

# 必须存在的配置 / 输入文件
# gmail_history.json 不在这里，因为它是可生成文件
REQUIRED_CONFIG_FILES = [
    "token.json",
    "api.txt",
    "prompt.txt",
]

# 可选文件，不存在不阻止运行
OPTIONAL_FILES = [
    "proxy.txt",
    "subs_list.txt",
]

# 每一步运行后应该生成的文件
EXPECTED_OUTPUTS = {
    "gmail_fetch.py": "gmail_output.json",
    "gmail_filter.py": "gmail_filtered.json",
}


def print_header(title):
    print()
    print("=" * 60)
    print(title)
    print("=" * 60)


def check_required_files():

    missing_files = []

    for filename in REQUIRED_SCRIPT_FILES + REQUIRED_CONFIG_FILES:
        path = BASE_DIR / filename
        if not path.exists():
            missing_files.append(filename)

    if missing_files:
        print("发现缺失的必要文件：")
        for filename in missing_files:
            print(f"  - {filename}")

        print()
        return False

    print("检查可选文件：")
    for filename in OPTIONAL_FILES:
        path = BASE_DIR / filename
        if path.exists():
            print(f"  - {filename}：存在")
        else:
            print(f"  - {filename}：不存在，跳过")

    return True


def run_python_script(script_name):

    script_path = BASE_DIR / script_name

    print_header(f"运行 {script_name}")

    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(BASE_DIR),
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    if result.returncode != 0:
        print()
        print(f"{script_name} 运行失败。")
        print(f"退出码：{result.returncode}")
        return False

    print()
    return True


def check_output_file(script_name):
    expected_filename = EXPECTED_OUTPUTS.get(script_name)

    if not expected_filename:
        return True

    expected_path = BASE_DIR / expected_filename

    if not expected_path.exists():
        print()
        print(f"错误：{script_name} 运行后未发现预期输出文件：{expected_filename}")
        return False

    return True


def find_today_summary_file():
    date_str = datetime.now().strftime("%y%m%d")
    summary_path = BASE_DIR / f"summary_{date_str}.md"

    if summary_path.exists():
        return summary_path

    return None


def main():
    print_header("AI邮件总结系统，运行中...")

    if not check_required_files():
        sys.exit(1)

    workflow = [
        "gmail_fetch.py",
        "gmail_filter.py",
        "send2ds.py",
    ]

    for script_name in workflow:
        success = run_python_script(script_name)

        if not success:
            print()
            print("运行已中止。")
            sys.exit(1)

        output_ok = check_output_file(script_name)

        if not output_ok:
            print()
            print("运行已中止。")
            sys.exit(1)

    summary_path = find_today_summary_file()

    if summary_path:
        print_header(f"运行完成，总结文件已生成：{summary_path}")
    else:
        print("运行完成，summary文件未生成？")

if __name__ == "__main__":
    main()