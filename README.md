# MeowMail-Digest

> もしも繁を簡にできたら

学校邮箱每天收到大量邮件，不读担心错过重要信息，全读太浪费时间……那就让AI来帮忙总结邮件，提取真正重要的信息吧！此存储库中包含所有必需文件的参考模板。

School email inboxes receive tons of messages every day. If you don’t read them, you might miss something important; if you read them all, it takes way too much time... Let AI help summarize emails and extract the truly important information! Reference templates for all required files are included in this repository.

<u>The English version is below. </u>

### 前期准备

1. 在学校邮箱设置自动转发/重定向至gmail。不直接从学校邮箱获取邮件，是考虑到学校管理员通常不会给学生邮箱授权。

2. 安装python以及`requirements.txt`中要求的包。

3. 找到一个可用的AI服务商的api，将信息填入`api.txt`。

4. 将不需要总结的广告发件邮箱填入`subs_list.txt`。

5. 根据你的需求，调整`prompt.txt`和`send2ds.py`末尾的提示词。

6. 由于脚本逻辑限制，在开始前，确保gmail收件箱至少有一封未读邮件。~~没有的话，你可以给自己发一封。~~

### 获取授权

1. 首先，从Google官方获取授权。进入[Google API Console](https://console.developers.google.com/)，在APIs & Services中找到并启用Gmail api，所需权限为`/auth/gmail.readonly`。

2. 在APIs & Services中找到OAuth授权，新建Desktop app，下载授权文件（下载后文件名以`client_secret_`开头）。将授权文件重命名为`credentials.json`并放在程序目录中。

3. 搜索OAuth consent screen，在test users中加入自己的邮箱地址。

4. 运行`token_get.py`。该脚本会通过`credentials.json`获取用于自动登陆邮箱的`token.json`，过程中会弹出浏览器，需要手动登录邮箱账号授权。授权完成后，脚本会测试网络能否连接api。

5. 如测试提示需要魔法，学会魔法后，将系统代理服务地址写入`proxy.txt`。如无需魔法，则将参考服务地址注释掉或直接删除该文件。

### 运行程序

1. 运行`run.py`，该统括脚本会自动检测所需文件是否完整，并运行以下3个脚本：
- `gmail_fetch.py`：从gmail获取未读邮件，生成包含邮件内容的`gmail_output.json`和记录获取历史的`gmail_history.json`。该脚本逻辑为，优先获取未读邮件，当所有未读邮件已经被获取过（历史记录），则获取所有**今天**的邮件。

- `gmail_filter.py`：根据`subs_list.txt`中记录的发件人邮箱，对`gmail_output.json`进行过滤，生成`gmail_filtered.json`。

- `send2ds.py`：将`prompt.txt`中的提示词和`gmail_filtered.json`发送给AI，获取回复，写入`summary_YYMMDD.md`（自动日期编号）。

- 阅读`summary_YYMMDD.md`，没有md阅览器用自带记事本即可。
2. 如果你的邮件过多，超过了AI一次能输入的上限，可使用`tool_split.py`对邮件文件进行拆分，手动重命名来分别进行AI总结。

```python
py tool_split.py -n 2 gmail_filtered.json   # -n 拆分的文件数
```

### 问答

**Q：Gmail可以换成别的邮箱吗？**

A：可以喵，不过不同邮箱获得授权的方法不同，需要自行调整。~~让我们问问神奇AI喵……~~

**Q：Deepseek可以换成别的AI吗？**

A：可以喵，只要兼容OpenAI Chat Completions 接口格式，修改`api.txt`即可。其他需要调整的地方取决于具体服务商的文档要求。不过DS便宜大碗，不考虑一下吗喵？

**Q：可以在服务器（linux)上用吗？**

A：大概……可以喵？没有测试过的说。初次获取token需要在浏览器登录邮箱账号，建议windows系统授权，之后把`token.json`传到服务器即可。~~如果已经在win装了python用来运行`token_get.py`，为什么不继续在win走完后面的流程喵……~~



=================================================================

## Preparation

1. Set up automatic forwarding/redirection from your school email to Gmail. Emails are not fetched directly from the school mailbox because school administrators usually do not grant authorization for student email accounts.

2. Install Python and the packages required in `requirements.txt`.

3. Find an available AI service provider API and fill in the information in `api.txt`.

4. Add advertising/subscription sender email addresses that do not need summarizing to `subs_list.txt`.

5. Adjust `prompt.txt` and the prompt at the end of `send2ds.py` according to your needs.

6. Due to limitations in the script logic, make sure your Gmail inbox has at least one unread email before starting. ~~If not, you can send one to yourself.~~

## Authorization

1. First, obtain authorization from Google. Go to the [Google API Console](https://console.developers.google.com/), find and enable the Gmail API under APIs & Services. The required scope is `/auth/gmail.readonly`.

2. In APIs & Services, find OAuth authorization, create a new Desktop app, and download the authorization file. The downloaded file name should start with `client_secret_`. Rename the file to `credentials.json` and place it in the program directory.

3. Search for OAuth consent screen, and add your own email address under test users.

4. Run `token_get.py`. This script uses `credentials.json` to obtain `token.json`, which is used for automatically logging into your mailbox. During the process, a browser window will pop up, and you need to manually log in to your email account and grant authorization. After authorization is complete, the script will test whether the network can connect to the API.

5. If the test indicates that “magic” is needed, learn some magic first, then write your system proxy service address into `proxy.txt`. If no magic is needed, comment out the reference service address or simply delete the file. ~~To be honest, if you are reading the English version of this guide, you probably don’t need magic...~~

## Running the Program

1. Run `run.py`. This master script will automatically check whether the required files are complete, and then run the following three scripts:
- `gmail_fetch.py`: Fetches unread emails from Gmail and generates `gmail_output.json`, which contains email content, and `gmail_history.json`, which records fetch history. The logic of this script is: it prioritizes unread emails; when all unread emails have already been fetched before according to the history records, it fetches all emails from **today**.

- `gmail_filter.py`: Filters `gmail_output.json` according to sender email addresses recorded in `subs_list.txt`, and generates `gmail_filtered.json`.

- `send2ds.py`: Sends the prompt in `prompt.txt` and `gmail_filtered.json` to the AI, obtains a response, and writes it into `summary_YYMMDD.md` with an automatically generated date-based filename.

- Read `summary_YYMMDD.md`. If you don’t have a Markdown viewer, the built-in Notepad will do just fine.
2. If you have too many emails and exceed the AI’s maximum input limit, you can use `tool_split.py` to split the email file, then manually rename the split files and summarize them separately with AI.

```python
py tool_split.py -n 2 gmail_filtered.json   # -n number of split files
```

## QA

**Q: Can Gmail be replaced with another email provider?**

A: Yes meow, but different email providers have different authorization methods, so you’ll need to adjust things yourself. ~~Let’s ask the magical AI meow...~~

**Q: Can DeepSeek be replaced with another AI?**

A: Yes meow, as long as it is compatible with the OpenAI Chat Completions interface format. Just modify `api.txt`. Other adjustments depend on the documentation requirements of the specific service provider. But DS is cheap and generous — won’t you consider it, meow?

**Q: Can this be used on a server/Linux?**

A: Probably... yes meow? Haven’t tested it though. The initial token acquisition requires logging into your email account in a browser, so it’s recommended to authorize on Windows first, then upload `token.json` to the server afterward. ~~But if you’ve already installed Python on Windows to run `token_get.py`, why not just finish the rest of the process on Windows too, meow...~~
