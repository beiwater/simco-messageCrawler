# 配置文件 - 存储敏感信息和配置参数

# 用户登录信息
USER_EMAIL = 'dualvectorfoil.42@gmail.com'  # 替换为你的邮箱
USER_PASSWORD = 'rocjun-4sizxo-wiqMyc'  # 替换为你的密码

# 应用配置参数
MAX_COUNT = 10  # 最大循环次数
REPEAT_TIME = 300  # 重复间隔时间（秒）
SESSION_REFRESH_TIME = 168 * 3600  # 会话刷新时间（168小时）

# API URL配置
JSON_URL = {
    "ZH": "https://www.simcompanies.com/api/v2/chatroom/N/",
    "EN": "https://www.simcompanies.com/api/v2/chatroom/G/",
    "X": "https://www.simcompanies.com/api/v2/chatroom/X/",
}

# 文件路径配置
DATA_DIR = './data/'  # JSON数据保存目录
DB_DIR = './databases/'  # 数据库保存目录
LOG_DIR = './logs/'  # 日志保存目录

# 数据库配置
DB_TIMEOUT = 10  # 数据库连接超时时间（秒）
DB_INSERT_TIMEOUT = 30  # 数据库插入操作超时时间（秒）

# 日志配置
LOG_MAX_BYTES = 5 * 1024 * 1024  # 日志文件最大大小（5MB）
LOG_BACKUP_COUNT = 5  # 保留的日志文件数量
UESR_INPUT = 'all'  # 用户输入选择（默认选择所有API）
