import json
import base64
import re
from pathlib import Path
from urllib.parse import urlparse
from email.utils import parseaddr
from html.parser import HTMLParser
from datetime import datetime, timezone, timedelta, time

import socks
import httplib2
import google_auth_httplib2

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
]

BASE_DIR = Path(__file__).resolve().parent

TOKEN_FILE = BASE_DIR / "token.json"
PROXY_FILE = BASE_DIR / "proxy.txt"

HISTORY_FILE = BASE_DIR / "gmail_history.json"
OUTPUT_FILE = BASE_DIR / "gmail_output.json"


class HTMLTextExtractor(HTMLParser):
# HTML 转无图纯文本。
    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip = False

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()

        if tag in ("script", "style"):
            self.skip = True

        if tag in ("p", "div", "br", "tr", "li"):
            self.parts.append("\n")

    def handle_endtag(self, tag):
        tag = tag.lower()

        if tag in ("script", "style"):
            self.skip = False

        if tag in ("p", "div", "tr", "li"):
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)

    def get_text(self):
        text = "".join(self.parts)
        text = re.sub(r"\r\n", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]+", " ", text)
        return text.strip()


def html_to_text(html):
    parser = HTMLTextExtractor()
    parser.feed(html)
    return parser.get_text()


def decode_base64url(data):
    if not data:
        return ""

    padding = "=" * (-len(data) % 4)
    data += padding

    return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")


def get_header(headers, name):
    for h in headers:
        if h.get("name", "").lower() == name.lower():
            return h.get("value", "")
    return ""


def extract_email_address(from_header):
    _, email_addr = parseaddr(from_header)
    return email_addr or from_header


def extract_body_from_payload(payload):
#从 Gmail payload 中提取正文纯文本，跳过附件和图片。
    plain_parts = []
    html_parts = []

    def walk(part):
        mime_type = part.get("mimeType", "")
        filename = part.get("filename", "")
        body = part.get("body", {})
        data = body.get("data")

        # 有 filename 的一般视为附件，跳过
        if filename:
            return

        if data:
            decoded = decode_base64url(data)

            if mime_type == "text/plain":
                plain_parts.append(decoded)
            elif mime_type == "text/html":
                html_parts.append(decoded)

        for child in part.get("parts", []) or []:
            walk(child)

    walk(payload)

    if plain_parts:
        return "\n\n".join(
            part.strip()
            for part in plain_parts
            if part.strip()
        ).strip()

    if html_parts:
        html_text = "\n\n".join(html_parts)
        return html_to_text(html_text)

    return ""


def load_proxy_info():
# 从同目录 proxy.txt 读取代理配置。
# proxy.txt 不存在、空、或内容以 # 注释时，不使用代理。
    if not PROXY_FILE.exists():
        print("未找到 proxy.txt，不使用代理。")
        return None

    proxy_url = ""

    with open(PROXY_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            proxy_url = line
            break

    if not proxy_url:
        print("proxy.txt 中没有启用的代理配置，不使用代理。")
        return None

    parsed = urlparse(proxy_url)

    scheme = parsed.scheme.lower()
    host = parsed.hostname
    port = parsed.port

    if not scheme or not host or not port:
        raise ValueError(
            f"proxy.txt 中的代理格式不正确：{proxy_url}\n"
            "请使用类似：http://127.0.0.1:0000 或 socks5://127.0.0.1:0000"
        )

    if scheme in ("http", "https"):
        proxy_type = socks.PROXY_TYPE_HTTP
    elif scheme in ("socks5", "socks"):
        proxy_type = socks.PROXY_TYPE_SOCKS5
    elif scheme == "socks4":
        proxy_type = socks.PROXY_TYPE_SOCKS4
    else:
        raise ValueError(
            f"不支持的代理协议：{scheme}\n"
            "目前支持：http、https、socks5、socks4"
        )

    print(f"使用代理：{scheme}://{host}:{port}")

    return httplib2.ProxyInfo(
        proxy_type=proxy_type,
        proxy_host=host,
        proxy_port=port,
    )


def load_credentials():
    if not TOKEN_FILE.exists():
        raise FileNotFoundError(f"找不到 token.json：{TOKEN_FILE}")

    creds = Credentials.from_authorized_user_file(
        str(TOKEN_FILE),
        SCOPES,
    )

    if creds.expired and creds.refresh_token:
        print("token 已过期，正在刷新...")
        creds.refresh(Request())

        with open(TOKEN_FILE, "w", encoding="utf-8") as f:
            f.write(creds.to_json())

    if not creds.valid:
        raise RuntimeError("token.json 无效，请重新生成 token。")

    return creds


def build_gmail_service(creds):
    proxy_info = load_proxy_info()

    if proxy_info:
        http = httplib2.Http(
            proxy_info=proxy_info,
            timeout=60,
        )

        authed_http = google_auth_httplib2.AuthorizedHttp(
            creds,
            http=http,
        )

        return build(
            "gmail",
            "v1",
            http=authed_http,
            cache_discovery=False,
        )

    return build(
        "gmail",
        "v1",
        credentials=creds,
        cache_discovery=False,
    )


def load_history():
# 读取历史记录。
    if not HISTORY_FILE.exists():
        return None

    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        last_internal_date = int(data.get("last_unread_internal_date") or 0)

        if last_internal_date <= 0:
            return None

        return {
            "last_unread_message_id": data.get("last_unread_message_id"),
            "last_unread_internal_date": last_internal_date,
            "updated_at": data.get("updated_at"),
        }

    except Exception:
        print("历史记录文件读取失败，将视为没有历史记录。")
        return None


def save_history(last_message_id, last_internal_date):
    data = {
        "last_unread_message_id": last_message_id,
        "last_unread_internal_date": int(last_internal_date),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"历史记录已更新：{HISTORY_FILE}")


def list_all_unread_message_ids(service):
# 获取所有未读邮件 ID。
    message_ids = []
    page_token = None

    while True:
        kwargs = {
            "userId": "me",
            "labelIds": ["UNREAD"],
            "maxResults": 500,
        }

        if page_token:
            kwargs["pageToken"] = page_token

        result = service.users().messages().list(**kwargs).execute()

        for msg in result.get("messages", []):
            message_ids.append(msg["id"])

        page_token = result.get("nextPageToken")

        if not page_token:
            break

    return message_ids


def get_message_full(service, message_id):
    return service.users().messages().get(
        userId="me",
        id=message_id,
        format="full",
    ).execute()


def message_to_record(message):
# 输出到 gmail_output.json 的精简结构。
    payload = message.get("payload", {})
    headers = payload.get("headers", [])

    from_header = get_header(headers, "From")
    sender_email = extract_email_address(from_header)

    subject = get_header(headers, "Subject")
    date = get_header(headers, "Date")
    body = extract_body_from_payload(payload)

    return {
        "id": message.get("id"),
        "subject": subject,
        "from": sender_email,
        "date": date,
        "body": body,
    }


def save_output(mode, records):
    data = {
        "mode": mode,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(records),
        "messages": records,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"邮件数据已写入：{OUTPUT_FILE}")


def get_local_day_bounds_from_internal_date(internal_date_ms):
# 根据历史记录中的 internalDate 计算本地日期的起止时间。
    local_tz = datetime.now().astimezone().tzinfo

    history_dt = datetime.fromtimestamp(
        internal_date_ms / 1000,
        tz=local_tz,
    )

    target_date = history_dt.date()

    start_dt = datetime.combine(
        target_date,
        time.min,
        tzinfo=local_tz,
    )

    end_dt = start_dt + timedelta(days=1)

    start_ms = int(start_dt.timestamp() * 1000)
    end_ms = int(end_dt.timestamp() * 1000)

    return target_date, start_ms, end_ms


def list_messages_on_history_date(service, history):
# 读取历史记录中 last_unread_internal_date 所在日期的所有邮件。
    last_internal_date = int(history["last_unread_internal_date"])

    target_date, start_ms, end_ms = get_local_day_bounds_from_internal_date(
        last_internal_date,
    )

    print(f"历史记录日期：{target_date}")

    # 放宽 Gmail 查询范围，避免 Gmail 搜索日期边界和本地时区不一致
    query_after_date = target_date - timedelta(days=1)
    query_before_date = target_date + timedelta(days=2)

    after_str = query_after_date.strftime("%Y/%m/%d")
    before_str = query_before_date.strftime("%Y/%m/%d")

    query = f"after:{after_str} before:{before_str}"

    candidate_ids = []
    page_token = None

    while True:
        kwargs = {
            "userId": "me",
            "q": query,
            "maxResults": 500,
        }

        if page_token:
            kwargs["pageToken"] = page_token

        result = service.users().messages().list(**kwargs).execute()

        for msg in result.get("messages", []):
            candidate_ids.append(msg["id"])

        page_token = result.get("nextPageToken")

        if not page_token:
            break

    matched_messages = []

    for message_id in candidate_ids:
        msg = get_message_full(service, message_id)
        internal_date = int(msg.get("internalDate", 0))

        if start_ms <= internal_date < end_ms:
            matched_messages.append(msg)

    matched_messages.sort(
        key=lambda m: int(m.get("internalDate", 0))
    )

    return matched_messages


def main():
    creds = load_credentials()
    service = build_gmail_service(creds)

    history = load_history()

    if history is None:
        print("未发现历史记录。当前所有未读邮件都将视为新邮件。")
        last_internal_date = 0
    else:
        last_internal_date = int(history["last_unread_internal_date"])
        print(f"发现历史记录。")

    print("正在检查所有未读邮件...")

    unread_ids = list_all_unread_message_ids(service)

    unread_messages = []

    for message_id in unread_ids:
        msg = get_message_full(service, message_id)
        internal_date = int(msg.get("internalDate", 0))

        if internal_date > last_internal_date:
            unread_messages.append(msg)

    unread_messages.sort(
        key=lambda m: int(m.get("internalDate", 0))
    )

    # 情况 1：无历史记录，且有未读邮件
    # 情况 2：有历史记录，且有新的未读邮件
    if unread_messages:
        print(f"发现新未读邮件：{len(unread_messages)} 封。")

        records = [
            message_to_record(msg)
            for msg in unread_messages
        ]

        save_output(
            mode="new_unread",
            records=records,
        )

        latest_msg = max(
            unread_messages,
            key=lambda m: int(m.get("internalDate", 0)),
        )

        save_history(
            last_message_id=latest_msg.get("id"),
            last_internal_date=int(latest_msg.get("internalDate", 0)),
        )

        return

    # 情况 1 的特殊子情况：无历史记录，且没有未读邮件
    if history is None:
        print("没有历史记录和未读邮件，请稍后再试。")

        save_output(
            mode="no_history_no_unread",
            records=[],
        )

        return

    # 情况 3：有历史记录，但没有新的未读邮件
    print("没有新未读邮件，将读取今天所有邮件。")

    history_date_messages = list_messages_on_history_date(
        service,
        history,
    )

    records = [
        message_to_record(msg)
        for msg in history_date_messages
    ]

    save_output(
        mode="fallback_history_date",
        records=records,
    )

    print("未更新历史记录。")


if __name__ == "__main__":
    main()