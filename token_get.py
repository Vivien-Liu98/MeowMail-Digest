import sys
import subprocess
from pathlib import Path


# 你需要的 Gmail API 权限
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly"
]


BASE_DIR = Path(__file__).resolve().parent
CREDENTIALS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "token.json"


def install_required_packages():
    """
    安装/更新 Gmail API 相关 Python 包。
    """
    packages = [
        "google-api-python-client",
        "google-auth-httplib2",
        "google-auth-oauthlib",
    ]

    print("正在安装/更新 Gmail API 相关 Python 包...")
    subprocess.check_call([
        sys.executable,
        "-m",
        "pip",
        "install",
        "--upgrade",
        *packages
    ])
    print("依赖安装完成。")


def token_has_required_scopes(creds):
    """
    检查现有 token.json 是否包含当前需要的全部 scopes。
    如果你之前用较少权限生成过 token.json，后来增加权限，需要重新授权。
    """
    existing_scopes = set(creds.scopes or [])
    required_scopes = set(SCOPES)
    return required_scopes.issubset(existing_scopes)


def get_credentials():
    """
    读取 credentials.json，并通过浏览器完成 OAuth 授权，生成 token.json。
    """
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    if not CREDENTIALS_FILE.exists():
        raise FileNotFoundError(
            f"找不到 {CREDENTIALS_FILE}\n"
            "请把从 Google Cloud Console 下载的 OAuth 客户端 JSON 文件重命名为 credentials.json，"
            "并放到本脚本同一目录。"
        )

    creds = None

    if TOKEN_FILE.exists():
        print(f"发现已有 token 文件：{TOKEN_FILE}")
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

        if not token_has_required_scopes(creds):
            print("现有 token.json 不包含当前要求的全部权限，需要重新授权。")
            creds = None

    if creds and creds.valid:
        print("现有 token.json 有效，无需重新授权。")
        return creds

    if creds and creds.expired and creds.refresh_token:
        print("token 已过期，正在刷新 access token...")
        creds.refresh(Request())
    else:
        print("需要进行首次授权，将打开浏览器。")

        flow = InstalledAppFlow.from_client_secrets_file(
            str(CREDENTIALS_FILE),
            SCOPES
        )

        creds = flow.run_local_server(
            host="localhost",
            port=0,
            open_browser=True,
            prompt="consent",
            access_type="offline"
        )

    with open(TOKEN_FILE, "w", encoding="utf-8") as token_file:
        token_file.write(creds.to_json())

    print(f"授权完成，token 已保存到：{TOKEN_FILE}")

    return creds


def test_gmail_access(creds):
    """
    简单测试 Gmail API 是否可用。
    如果无法连接 Google API，则提示网络有问题或需要代理。
    """
    import socket
    import ssl
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from google.auth.exceptions import TransportError, RefreshError

    print("正在测试 Gmail API 访问权限...")

    try:
        service = build(
            "gmail",
            "v1",
            credentials=creds,
            cache_discovery=False
        )

        profile = service.users().getProfile(userId="me").execute()

        print("Gmail API 访问成功。")
        print("当前邮箱：", profile.get("emailAddress"))
        print("总邮件数：", profile.get("messagesTotal"))
        print("总会话数：", profile.get("threadsTotal"))

        return True

    except HttpError as e:
        status_code = getattr(e.resp, "status", None)

        print("Gmail API 请求失败。")

        if status_code in (401, 403):
            print("可能原因：token 无效、权限不足，或 Gmail API 未启用。")
            print("建议：删除 token.json 后重新运行脚本授权。")
        elif status_code in (429, 500, 502, 503, 504):
            print("可能原因：Google API 暂时不可用，或网络访问不稳定。")
            print("建议：稍后重试，或检查代理设置。")
        else:
            print(f"HTTP 状态码：{status_code}")

        print("详细错误：")
        print(e)

        return False

    except (
        TransportError,
        RefreshError,
        socket.timeout,
        TimeoutError,
        ConnectionError,
        ConnectionResetError,
        ConnectionRefusedError,
        ssl.SSLError,
        OSError,
    ) as e:
        print("无法连接 Gmail API。")
        print("可能原因：网络有问题，或需要魔（代）法（理）。")
        print("建议：是时候变身魔法少女了喵（）")
        print("详细错误：")
        print(repr(e))

        return False

    except Exception as e:
        print("测试 Gmail API 时发生未知错误。")
        print("可能原因：不知道喵...")
        print()
        print("详细错误：")
        print(repr(e))

        return False


def main():
    print("脚本目录：", BASE_DIR)

    install_required_packages()

    creds = get_credentials()

    if not test_gmail_access(creds):
        print()
        print("Gmail API 连接测试未通过。")
        sys.exit(1)

    print()
    print("获取token完成。")


if __name__ == "__main__":
    main()