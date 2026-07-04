import os
import json
import requests
from datetime import datetime

def read_api_config(config_path):
    """
    读取 api.txt 配置文件。
    支持格式：
    api_url=https://api.deepseek.com
    api_key=sk-xxxx
    model=deepseek-chat
    """
    config = {}

    with open(config_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            if "=" in line:
                key, value = line.split("=", 1)
                config[key.strip()] = value.strip()

    required_keys = ["api_url", "api_key", "model"]
    for key in required_keys:
        if key not in config or not config[key]:
            raise ValueError(f"api.txt 中缺少配置项：{key}")

    return config


def build_chat_completions_url(api_url):
    api_url = api_url.rstrip("/")

    if api_url.endswith("/chat/completions"):
        return api_url

    return api_url + "/chat/completions"


def read_json_file_as_text(json_path, compact=True):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if compact:
        return json.dumps(data, ensure_ascii=False, separators=(",", ":"))

    return json.dumps(data, ensure_ascii=False, indent=2)


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    api_txt_path = os.path.join(base_dir, "api.txt")
    prompt_path = os.path.join(base_dir, "prompt.txt")
    gmail_json_path = os.path.join(base_dir, "gmail_filtered.json")
    date_str = datetime.now().strftime("%y%m%d")
    reply_path = os.path.join(base_dir, f"summary_{date_str}.md")

    config = read_api_config(api_txt_path)

    api_url = build_chat_completions_url(config["api_url"])
    api_key = config["api_key"]
    model = config["model"]

    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt_content = f.read().strip()

    gmail_json_content = read_json_file_as_text(gmail_json_path, compact=True)

    user_content = f"""
你将收到两部分内容：

第一部分是【任务说明】，来自 prompt.txt。
第二部分是【邮件数据】，来自 gmail_output.json。

请严格根据【任务说明】分析【邮件数据】，不要编造邮件中不存在的信息。

【任务说明】
{prompt_content}

【邮件数据】
下面是 gmail_output.json 的完整内容。

JSON_DATA_BEGIN
{gmail_json_content}
JSON_DATA_END
""".strip()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": user_content
            }
        ],
        "temperature": 0.1
    }

    try:
        response = requests.post(
            api_url,
            headers=headers,
            json=payload,
            timeout=120
        )

        response.raise_for_status()

        data = response.json()

        reply = data["choices"][0]["message"]["content"]

        with open(reply_path, "w", encoding="utf-8") as f:
            f.write(reply)

        print(f"DeepSeek回复已保存到 {os.path.basename(reply_path)}")

    except requests.exceptions.RequestException as e:
        print("请求 DeepSeek API 失败：")
        print(e)

        if hasattr(e, "response") and e.response is not None:
            print("服务器返回：")
            print(e.response.text)

    except Exception as e:
        print("程序运行出错：")
        print(e)


if __name__ == "__main__":
    main()