# ===== B站配置 =====
# 从浏览器Cookie中复制这三个值（获取方法见README）
SESSDATA = ""          # 必填
BILI_JCT = ""          # 必填（也叫 bili_jct）
BUVID3 = ""            # 必填

# 主人列表：填你和女朋友的B站UID（数字），用逗号隔开
# 在个人主页URL里可以看到，比如 https://space.bilibili.com/123456789 中的 123456789
OWNER_UIDS = [
    123456789,   # 你的大号
    # 987654321, # 其他UID，取消注释并填入
]

# ===== AI配置 =====
AI_BASE_URL = "https://api.anthropic.com"  # AI接口地址
AI_MODEL = "claude-3-5-sonnet-20241022"     # AI模型名称
AI_API_KEY = ""                              # AI API密钥

# ===== Bot配置 =====
POLL_INTERVAL = 30     # 轮询间隔（秒）
REPLY_INTERVAL = 30    # 回复间隔（秒），避免被B站风控
