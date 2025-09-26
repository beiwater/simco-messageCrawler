
import mod_sign
import json_download
import time
import logging
import os
from config import USER_EMAIL, USER_PASSWORD, MAX_COUNT, REPEAT_TIME, SESSION_REFRESH_TIME, JSON_URL, LOG_DIR

# Ensure the logs directory exists
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Configure the logging
logging.basicConfig(filename=os.path.join(LOG_DIR, 'app.log'), filemode='a', level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def login_with_retry(email, password, retries=3, delay=60):
    """Attempts to log in, retrying on failure."""
    attempt = 0
    while attempt < retries:
        session = mod_sign.login_sim_companies(email, password)
        if session:
            return session
        else:
            logging.warning("Login failed, retrying in %s seconds...", delay)
            time.sleep(delay)
            attempt += 1
    logging.error("Failed to create session after %s retries.", retries)
    return None

def get_user_selection():
    '''
    # Display API options and allow user selection
    print("请选择要提取数据的API（用逗号分隔多个选项，或输入'all'选择全部）：")
    for key in JSON_URL.keys():
        print(f"{key}: {JSON_URL[key]}")
    #user_input = input("输入你的选择: ").strip()
    #user_input = UESR_INPUT
    #if user_input.lower() == 'all':
    #    return list(JSON_URL.keys())
    #else:
    #    return [key.strip() for key in user_input.split(',') if key.strip() in JSON_URL]
    '''
    return list(JSON_URL.keys())


def main():
    email = USER_EMAIL
    password = USER_PASSWORD
    
    # Get initial user selection only once
    selected_api_keys = get_user_selection()
    logging.info("User selected API keys: %s", selected_api_keys)

    session = login_with_retry(email, password)
    logging.debug('Session acquired: %s', session)
    count_number = 0
    start_time = time.time()
    
    if session:
        # while count_number < MAX_COUNT:
        while True:
            logging.info('开始循环')
            print('开始循环')
            
            # Refresh session if 168 hours have passed
            if time.time() - start_time > SESSION_REFRESH_TIME:
                logging.info("Refreshing session after 168 hours.")
                session = login_with_retry(email, password)
                start_time = time.time()
            
            for api_key in selected_api_keys:
                url = JSON_URL[api_key]
                logging.info('Processing API key: %s with URL: %s', api_key, url)

                # Pass the api_key as the prefix to the download_json function
                json_data = json_download.download_and_append_json(session, url, api_key)
                
                # Add logic to process json_data if needed
                if json_data:
                    logging.info("数据检索成功: %s", api_key)
                    print("数据检索成功")
                else:
                    logging.warning("请求失败，1分钟后重试...")
                    print("请求失败，1分钟后重试...")
                    time.sleep(60) # 等待一分钟后重试
            
            count_number += 1
            time.sleep(REPEAT_TIME)
    else:
        logging.error('Session creation failed with provided email and password.')

if __name__ == "__main__":
    main()
