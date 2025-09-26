import requests
import json
import sqlite3
import os
import time
import logging
from datetime import datetime, timezone
import urllib3
from logging.handlers import RotatingFileHandler
from config import DATA_DIR, DB_DIR, LOG_DIR, DB_TIMEOUT, DB_INSERT_TIMEOUT, LOG_MAX_BYTES, LOG_BACKUP_COUNT

# 设置日志系统
def setup_logger():
    # 创建logs目录（如果不存在）
    os.makedirs(LOG_DIR, exist_ok=True)
    
    # 设置日志级别
    logging.basicConfig(level=logging.DEBUG)
    
    # 创建logger实例
    logger = logging.getLogger('json_downloader')
    logger.setLevel(logging.DEBUG)
    
    # 避免重复添加处理器
    if logger.handlers:
        logger.handlers.clear()
    
    # 创建控制台处理器（输出INFO及以上级别）
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    
    # 创建文件处理器（输出DEBUG及以上级别，带轮转）
    file_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, 'json_download.log'),
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    
    # 添加处理器到logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

# 获取logger实例
logger = setup_logger()

# 忽略SSL警告
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 初始化数据库
def init_database(db_path):
    try:
        # 确保数据库目录存在
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
            
        conn = sqlite3.connect(db_path, timeout=DB_TIMEOUT)
        cursor = conn.cursor()
        
        # 创建senders表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS senders (
            id TEXT PRIMARY KEY,
            company TEXT,
            realmId INTEGER DEFAULT 0,
            moderatorSign INTEGER DEFAULT 0,
            logo TEXT,
            certificates INTEGER DEFAULT 0,
            supporter INTEGER DEFAULT 0,
            contest_wins INTEGER DEFAULT 0,
            note TEXT
        )
        ''')
        
        # 创建messages表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY,
            sender_id TEXT,
            chatroom TEXT,
            chatroom_name TEXT,
            realms_shared INTEGER DEFAULT 0,
            datetime TEXT,
            body TEXT,
            chatroom_logo TEXT,
            ban_notification INTEGER DEFAULT 0,
            pinned INTEGER DEFAULT 0,
            invisible INTEGER DEFAULT 0,
            retracted INTEGER DEFAULT 0,
            isHtml INTEGER DEFAULT 0,
            enc TEXT,
            FOREIGN KEY (sender_id) REFERENCES senders (id)
        )
        ''')
        
        # 创建tracking表用于跟踪最后处理的消息ID
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tracking (
            name TEXT PRIMARY KEY,
            last_processed_id INTEGER DEFAULT 0
        )
        ''')
        
        # 初始化跟踪记录（如果不存在）
        cursor.execute('SELECT * FROM tracking WHERE name = ?', ('last_message_id',))
        if not cursor.fetchone():
            cursor.execute('INSERT INTO tracking VALUES (?, ?)', ('last_message_id', 0))
            logger.info(f"初始化 {db_path} 跟踪表")
        
        conn.commit()
        logger.info(f"数据库 {db_path} 初始化成功")
    except sqlite3.Error as e:
        logger.error(f"初始化数据库 {db_path} 时出错: {str(e)}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

# 获取最后处理的消息ID
def get_last_processed_id(db_path):
    try:
        conn = sqlite3.connect(db_path, timeout=DB_TIMEOUT)
        cursor = conn.cursor()
        cursor.execute('SELECT last_processed_id FROM tracking WHERE name = ?', ('last_message_id',))
        result = cursor.fetchone()
        return result[0] if result else 0
    except sqlite3.Error as e:
        logger.error(f"获取 {db_path} 最后处理ID时出错: {str(e)}")
        return 0
    finally:
        if 'conn' in locals() and conn:
            conn.close()

# 更新最后处理的消息ID
def update_last_processed_id(db_path, message_id):
    try:
        conn = sqlite3.connect(db_path, timeout=DB_TIMEOUT)
        cursor = conn.cursor()
        cursor.execute('UPDATE tracking SET last_processed_id = ? WHERE name = ?', (message_id, 'last_message_id'))
        conn.commit()
        logger.info(f"更新 {db_path} 最后处理ID为: {message_id}")
    except sqlite3.Error as e:
        logger.error(f"更新 {db_path} 最后处理ID时出错: {str(e)}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

# 将消息和发送者数据插入数据库
def insert_data(db_path, messages):
    if not messages:
        return
    
    try:
        conn = sqlite3.connect(db_path, timeout=DB_INSERT_TIMEOUT)
        cursor = conn.cursor()
        
        # 获取现有发送者ID集合
        cursor.execute('SELECT id FROM senders')
        existing_sender_ids = {row[0] for row in cursor.fetchall()}
        
        last_message_id = 0
        
        # 按消息ID排序，确保按时间顺序处理
        messages_sorted = sorted(messages, key=lambda x: x['id'])
        
        for message in messages_sorted:
            # 插入发送者数据，使用INSERT OR IGNORE避免UNIQUE约束错误
            sender = message['sender']
            if sender['id'] not in existing_sender_ids:
                cursor.execute('''
                INSERT OR IGNORE INTO senders (id, company, realmId, moderatorSign, logo, certificates, supporter, contest_wins, note)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    sender['id'],
                    sender.get('company', ''),
                    sender.get('realmId', 0),
                    1 if sender.get('moderatorSign', False) else 0,
                    sender.get('logo', ''),
                    sender.get('certificates', 0),
                    1 if sender.get('supporter', False) else 0,
                    sender.get('contest_wins', 0),
                    sender.get('note', None)
                ))
                existing_sender_ids.add(sender['id'])
            
            # 插入消息数据
            cursor.execute('''
            INSERT OR IGNORE INTO messages 
            (id, sender_id, chatroom, chatroom_name, realms_shared, datetime, body, chatroom_logo, ban_notification, pinned, invisible, retracted, isHtml, enc)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                message['id'],
                sender['id'],
                message.get('chatroom', ''),
                message.get('chatroom_name', ''),
                1 if message.get('realms_shared', False) else 0,
                message.get('datetime', ''),
                message.get('body', ''),
                message.get('chatroom_logo', ''),
                1 if message.get('ban_notification', False) else 0,
                1 if message.get('pinned', False) else 0,
                1 if message.get('invisible', False) else 0,
                1 if message.get('retracted', False) else 0,
                1 if message.get('isHtml', False) else 0,
                message.get('enc', '')
            ))
            
            # 更新最后处理的消息ID
            if message['id'] > last_message_id:
                last_message_id = message['id']
        
        conn.commit()
        logger.info(f"成功向 {db_path} 插入 {len(messages_sorted)} 条消息")
        
        # 在提交后单独更新最后处理的ID，避免事务问题
        if last_message_id > 0:
            update_last_processed_id(db_path, last_message_id)
        
    except sqlite3.Error as e:
        logger.error(f"向 {db_path} 插入数据时出错: {str(e)}")
        # 如果出现错误，尝试回滚
        if 'conn' in locals() and conn:
            try:
                conn.rollback()
            except:
                pass
    finally:
        if 'conn' in locals() and conn:
            conn.close()

# 将JSON数据导入数据库
def import_json_to_db(json_data, db_path):
    if not json_data:
        logger.warning(f"没有数据导入到 {db_path}")
        return
    
    # 初始化数据库
    init_database(db_path)
    
    # 获取最后处理的消息ID
    last_id = get_last_processed_id(db_path)
    logger.info(f"当前 {db_path} 最后处理的消息ID: {last_id}")
    
    # 筛选出未处理的新消息
    new_messages = [msg for msg in json_data if msg['id'] > last_id]
    
    if new_messages:
        logger.info(f"发现 {len(new_messages)} 条新消息，正在导入到 {db_path}...")
        insert_data(db_path, new_messages)
        logger.info(f"导入到 {db_path} 完成")
    else:
        logger.info(f"没有发现新消息需要导入到 {db_path}")

def download_and_append_json(session, json_url, prefix):
    if session is None:
        logger.error("Session is None, cannot download JSON.")
        return None

    try:
        # Make the request using the session
        response = requests.get(json_url, cookies=session, verify=False)
        if response.status_code == 200:
            new_json_data = response.json()
            logger.info(f"成功下载 {prefix} JSON数据")

            # Define path for saving file
            filename = f"{prefix}_data.json"
            file_path = os.path.join(DATA_DIR, filename)
            
            # 定义数据库路径
            db_filename = f"{prefix}_chat.db"
            db_path = os.path.join(DB_DIR, db_filename)

            # Ensure the directories exist
            os.makedirs(DATA_DIR, exist_ok=True)
            os.makedirs(DB_DIR, exist_ok=True)

            # Load existing data if the file exists
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as file:
                    existing_data = json.load(file)
            else:
                existing_data = []

            # Use a set to track combined keys for uniqueness
            existing_keys = {(entry["sender"]["company"], entry["datetime"]) for entry in existing_data}

            # Add new entries if they are not already in the existing set
            for entry in new_json_data:
                key = (entry["sender"]["company"], entry["datetime"])
                if key not in existing_keys:
                    existing_data.append(entry)
                    existing_keys.add(key)

            # Write the updated data back to the file
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(existing_data, file, ensure_ascii=False, indent=4)

            # 将更新后的JSON数据导入数据库
            import_json_to_db(existing_data, db_path)

            logger.info(f"{prefix}_已保存")
            current_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
            logger.info(current_time)
            print(f"{prefix}_已保存")
            print(current_time)
            return existing_data
        else:
            logger.error(f"下载失败，状态码: {response.status_code}")
            print(f"下载失败，状态码: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"下载和处理 {prefix} 数据时出错: {str(e)}")
        print(f"下载和处理 {prefix} 数据时出错: {str(e)}")
        return None

# 主函数示例（根据实际需要调用）
if __name__ == "__main__":
    try:
        # 这里可以根据实际情况添加调用download_and_append_json的代码
        # 例如:
        # session = ... # 获取session
        # json_url = "https://example.com/api/data"
        # download_and_append_json(session, json_url, "example")
        logger.info("程序已启动")
        print("请根据实际需要调用download_and_append_json函数")
    except Exception as e:
        logger.error(f"程序执行出错: {str(e)}")
        print(f"程序执行出错: {str(e)}")