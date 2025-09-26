import os
import json
import time
import sqlite3
from datetime import datetime
import shutil
from config import DATA_DIR, DB_DIR, LOG_DIR

# 确保测试目录存在并清理旧文件
def prepare_test_environment():
    # 使用配置文件中的目录定义
    test_dirs = [DATA_DIR, DB_DIR, LOG_DIR]
    
    # 清理并创建目录
    for dir_path in test_dirs:
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)
        os.makedirs(dir_path, exist_ok=True)
    
    print("测试环境已准备就绪")

# 创建模拟的JSON数据
def create_mock_json_data(prefix, count=10):
    # 确保数据目录存在
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # 创建模拟数据
    mock_data = []
    current_time = datetime.now().isoformat()
    
    for i in range(count):
        message = {
            "id": i + 1,
            "sender": {
                "id": f"sender_{i % 3 + 1}",
                "company": f"Company_{prefix}",
                "realmId": i % 5 + 1,
                "moderatorSign": i % 2 == 0,
                "logo": f"logo_{i}.png",
                "certificates": i % 3,
                "supporter": i % 4 == 0,
                "contest_wins": i % 5,
                "note": f"Note for sender {i % 3 + 1}"
            },
            "chatroom": f"room_{prefix}",
            "chatroom_name": f"Chat Room {prefix}",
            "realms_shared": i % 2 == 0,
            "datetime": f"{current_time}_{i}",
            "body": f"这是 {prefix} 的测试消息 #{i + 1}",
            "chatroom_logo": f"room_logo_{prefix}.png",
            "ban_notification": False,
            "pinned": i % 5 == 0,
            "invisible": False,
            "retracted": False,
            "isHtml": False,
            "enc": ""
        }
        mock_data.append(message)
    
    # 保存到JSON文件
    file_path = os.path.join(DATA_DIR, f'{prefix}_data.json')
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(mock_data, f, ensure_ascii=False, indent=2)
    
    print(f"已创建模拟JSON数据: {file_path}")
    return file_path, mock_data

# 模拟download_and_append_json函数的调用
def simulate_json_to_db_conversion(prefix, mock_data):
    # 我们将直接导入修改后的json_download.py中的函数来测试
    try:
        # 导入修改后的模块
        import json_download
        
        # 创建模拟的session对象
        class MockSession:
            def get_dict(self):
                return {"test": "session"}
        
        mock_session = MockSession().get_dict()
        
        # 模拟下载和转换过程
        print(f"\n开始处理 {prefix} 的数据...")
        
        # 由于我们已经创建了模拟数据，这里直接调用导入函数处理现有数据
        # 实际使用时应该传入真实的session和url
        # 这里为了测试，我们直接调用import_json_to_db函数
        db_path = os.path.join(DB_DIR, f'{prefix}_chat.db')
        json_download.import_json_to_db(mock_data, db_path)
        
        return db_path
    except Exception as e:
        print(f"处理 {prefix} 数据时出错: {str(e)}")
        return None

# 验证数据库是否正确创建并包含数据
def verify_database(db_path, expected_count):
    if not os.path.exists(db_path):
        print(f"错误: 数据库文件 {db_path} 不存在")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查senders表
        cursor.execute('SELECT COUNT(*) FROM senders')
        sender_count = cursor.fetchone()[0]
        
        # 检查messages表
        cursor.execute('SELECT COUNT(*) FROM messages')
        message_count = cursor.fetchone()[0]
        
        # 检查tracking表
        cursor.execute('SELECT last_processed_id FROM tracking WHERE name = ?', ('last_message_id',))
        result = cursor.fetchone()
        last_id = result[0] if result else 0
        
        conn.close()
        
        print(f"数据库验证结果 ({db_path}):")
        print(f"- 发送者数量: {sender_count}")
        print(f"- 消息数量: {message_count}")
        print(f"- 最后处理ID: {last_id}")
        
        # 检查消息数量是否符合预期
        return message_count == expected_count
    except sqlite3.Error as e:
        print(f"验证数据库时出错: {str(e)}")
        return False

# 主测试函数
def main():
    print("=== JSON到SQLite数据库转换测试 ===")
    
    # 准备测试环境
    prepare_test_environment()
    
    # 定义4个测试前缀（代表4个JSON文件）
    prefixes = ['test1', 'test2', 'test3', 'test4']
    
    # 为每个前缀创建模拟数据并转换为数据库
    results = []
    for prefix in prefixes:
        # 创建模拟JSON数据
        file_path, mock_data = create_mock_json_data(prefix, count=8)  # 每个文件8条测试消息
        
        # 模拟转换过程
        db_path = simulate_json_to_db_conversion(prefix, mock_data)
        
        if db_path:
            # 验证数据库
            is_valid = verify_database(db_path, len(mock_data))
            results.append((prefix, is_valid))
        else:
            results.append((prefix, False))
        
        # 等待一小段时间，避免数据库锁定问题
        time.sleep(1)
    
    # 输出测试结果摘要
    print("\n=== 测试结果摘要 ===")
    all_success = True
    for prefix, success in results:
        status = "成功" if success else "失败"
        print(f"- {prefix}: {status}")
        if not success:
            all_success = False
    
    if all_success:
        print("\n恭喜！所有4个JSON文件都成功转换为对应的SQLite数据库。")
        print(f"您现在可以使用SQLite工具查看生成的数据库文件，它们位于 '{DB_DIR}' 目录下。")
    else:
        print("\n测试失败。请检查日志文件以获取更多详细信息。")

if __name__ == "__main__":
    main()