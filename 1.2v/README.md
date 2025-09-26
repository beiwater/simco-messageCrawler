# JSON到SQLite数据库转换器

## 功能介绍

此脚本将原有的JSON下载功能扩展，不仅能够下载并保存JSON数据，还能将每个JSON文件自动转换为独立的SQLite数据库。特别针对用户需求，支持将4个不同的JSON文件分别转换为4个独立的数据库文件，每个数据库包含完整的消息和发送者信息。

## 主要改进

1. **数据库支持**：为每个JSON文件创建对应的SQLite数据库
2. **增强的日志系统**：同时输出到控制台和文件，支持日志轮转
3. **数据去重**：使用消息ID跟踪，避免重复导入数据
4. **错误处理**：全面的异常捕获和处理机制
5. **自动创建目录**：自动创建data、databases和logs目录
6. **数据库连接优化**：设置连接超时，避免数据库锁定问题

## 数据结构

每个数据库包含三个表：

### senders表（发送者信息）
- `id`：发送者ID（主键）
- `company`：公司名称
- `realmId`：领域ID
- `moderatorSign`：是否为管理员
- `logo`：Logo图片
- `certificates`：证书数量
- `supporter`：是否为支持者
- `contest_wins`：比赛获胜次数
- `note`：备注信息

### messages表（消息信息）
- `id`：消息ID（主键）
- `sender_id`：发送者ID（外键）
- `chatroom`：聊天室ID
- `chatroom_name`：聊天室名称
- `realms_shared`：是否共享领域
- `datetime`：消息时间
- `body`：消息内容
- `chatroom_logo`：聊天室Logo
- `ban_notification`：是否为封禁通知
- `pinned`：是否置顶
- `invisible`：是否不可见
- `retracted`：是否撤回
- `isHtml`：是否为HTML内容
- `enc`：加密信息

### tracking表（跟踪信息）
- `name`：跟踪项名称（主键）
- `last_processed_id`：最后处理的消息ID

## 使用方法

### 基本使用

1. 确保已安装所需依赖：
   ```bash
   pip install requests
   ```

2. 调用`download_and_append_json`函数下载JSON数据并自动转换为数据库：
   ```python
   import json_download
   
   # 准备session（包含登录信息）
   session = {'session_key': 'session_value'}  # 实际使用时替换为真实的session数据
   
   # 为每个JSON文件调用一次函数，使用不同的prefix
   json_download.download_and_append_json(session, 'https://example.com/api/data1', 'prefix1')
   json_download.download_and_append_json(session, 'https://example.com/api/data2', 'prefix2')
   json_download.download_and_append_json(session, 'https://example.com/api/data3', 'prefix3')
   json_download.download_and_append_json(session, 'https://example.com/api/data4', 'prefix4')
   ```

### 输出位置

- JSON文件：保存在`./data/`目录下，命名格式为`{prefix}_data.json`
- 数据库文件：保存在`./databases/`目录下，命名格式为`{prefix}_chat.db`
- 日志文件：保存在`./logs/`目录下，文件名为`json_download.log`

## 测试方法

使用提供的`test_json_to_db.py`脚本可以快速测试功能是否正常工作：

1. 运行测试脚本：
   ```bash
   python test_json_to_db.py
   ```

2. 测试脚本会自动：
   - 创建测试环境（清理并创建必要目录）
   - 生成4个模拟的JSON文件
   - 将每个JSON文件转换为对应的数据库
   - 验证数据库是否正确创建并包含预期数据

3. 查看测试结果：
   - 控制台会输出每个数据库的验证结果
   - 检查`./databases/`目录下是否生成了4个数据库文件
   - 检查`./logs/`目录下的日志文件获取详细信息

## 日志系统

脚本包含增强的日志系统，具有以下特点：

- **多目标输出**：同时输出到控制台和日志文件
- **分级日志**：控制台显示INFO及以上级别，文件记录DEBUG及以上级别
- **自动轮转**：日志文件达到5MB时自动轮转，保留5个备份
- **结构化格式**：包含时间戳、日志级别和消息内容

## 注意事项

1. 确保运行脚本的用户对目标目录有读写权限
2. 处理大量数据时，可能需要调整SQLite连接超时参数
3. 数据库文件可能会随着数据量增长而变大，请注意磁盘空间
4. 如遇到"database is locked"错误，请检查是否有其他进程正在访问相同的数据库文件
5. 测试脚本会清理现有的data、databases和logs目录，请在运行前备份重要数据

## 自定义配置

您可以根据需要修改以下配置参数：

- **数据库路径**：修改`db_save_path`变量来自定义数据库保存位置
- **日志设置**：调整`setup_logger`函数中的日志级别、文件大小限制和备份数量
- **SQLite连接超时**：修改数据库连接时的`timeout`参数

## 故障排除

- **下载失败**：检查网络连接和session是否有效
- **数据库锁定**：确保没有其他程序同时访问同一数据库文件，或增加超时时间
- **导入数据不完整**：检查JSON数据格式是否正确，查看日志文件获取详细错误信息