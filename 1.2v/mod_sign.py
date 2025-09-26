from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
#pip install webdriver-manager
from webdriver_manager.chrome import ChromeDriverManager
import time
import logging
import os
import platform
import psutil

def login_sim_companies(email, password):
    """使用Selenium模拟登录Sim Companies网站"""
    driver = None
    try:
        chrome_options = Options()
        # 为无图形界面Linux环境优化Chrome选项
        chrome_options.add_argument("--headless")  # 强制无头模式
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")  # 解决Docker容器中权限问题
        chrome_options.add_argument("--disable-dev-shm-usage")  # 解决资源限制问题
        chrome_options.add_argument("--disable-extensions")  # 禁用扩展以减少资源使用
        chrome_options.add_argument("--disable-background-networking")  # 减少后台网络请求
        chrome_options.add_argument("--window-size=1920,1080")  # 设置窗口大小
        chrome_options.add_argument("--ignore-certificate-errors")  # 忽略证书错误
        chrome_options.add_argument("--allow-insecure-localhost")  # 允许不安全的本地主机
        
        # 为Linux无图形界面环境添加的特殊选项
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")  # 禁用可视化合成器
        chrome_options.add_argument("--disable-setuid-sandbox")  # 禁用setuid沙盒
        chrome_options.add_argument("--disable-xss-auditor")  # 禁用XSS审计器以提高性能
        
        # 设置Chrome二进制文件路径（适配Docker环境中的chromium）
        for chrome_bin_path in ["/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser"]:
            if os.path.exists(chrome_bin_path):
                chrome_options.binary_location = chrome_bin_path
                logging.info(f"设置Chrome二进制文件路径: {chrome_bin_path}")
                break
        
        # 优化ChromeDriver的管理和使用方式
        driver = None
        
        # 方法1: 直接在Docker环境中使用系统安装的ChromeDriver（优先）
        system_chromedriver_paths = [
            "/usr/local/bin/chromedriver",
            "/usr/bin/chromedriver",
            "/usr/lib/chromium-browser/chromedriver",
            "/usr/lib/chromium/chromedriver"  # Debian/Ubuntu上Chromium-driver的常见路径
        ]
        
        for chromedriver_path in system_chromedriver_paths:
            if os.path.exists(chromedriver_path):
                try:
                    # 确保文件有执行权限
                    try:
                        os.chmod(chromedriver_path, 0o755)
                    except Exception as perm_error:
                        logging.warning(f"无法设置执行权限: {perm_error}")
                        # 继续尝试使用，可能已经有权限
                    
                    logging.info(f"尝试使用系统ChromeDriver: {chromedriver_path}")
                    try:
                        # 创建Service对象并设置日志级别
                        service = Service(
                            chromedriver_path,
                            log_output=os.devnull,  # 禁用ChromeDriver日志输出
                            service_args=['--verbose'] if logging.getLogger().level == logging.DEBUG else []
                        )
                        driver = webdriver.Chrome(service=service, options=chrome_options)
                        logging.info("系统ChromeDriver启动成功")
                        break
                    except Exception as e:
                        logging.warning(f"系统ChromeDriver启动失败: {e}")
                        continue
                except Exception as e:
                    logging.warning(f"系统ChromeDriver启动失败: {e}")
        
        # 方法2: 如果系统ChromeDriver不可用，使用webdriver-manager并指定与Chrome兼容的版本
        if driver is None:
            try:
                # 获取Chrome浏览器版本并安装匹配的ChromeDriver
                import subprocess
                
                # 尝试多种方式获取Chrome版本
                chrome_version = None
                for bin_name in ["google-chrome", "chromium", "chromium-browser"]:
                    try:
                        chrome_version = subprocess.check_output([bin_name, "--version"], stderr=subprocess.STDOUT).decode('utf-8').strip()
                        if chrome_version:
                            break
                    except:
                        continue
                
                if chrome_version:
                    # 提取主版本号（适配各种浏览器输出格式）
                    version_parts = chrome_version.split()
                    major_version = None
                    for part in version_parts:
                        if part.replace('.', '').isdigit():
                            major_version = part.split('.')[0]
                            break
                    
                    if major_version:
                        logging.info(f"检测到浏览器版本: {chrome_version}")
                        logging.info(f"尝试安装ChromeDriver {major_version} 版本")
                        try:
                            # 安装匹配版本的ChromeDriver
                            driver = webdriver.Chrome(
                                service=Service(
                                    ChromeDriverManager(driver_version=major_version).install(),
                                    log_output=os.devnull
                                ), 
                                options=chrome_options
                            )
                        except Exception as version_error:
                            logging.warning(f"指定版本安装失败，尝试默认安装: {version_error}")
                            # 回退到默认安装
                            driver = webdriver.Chrome(
                                service=Service(ChromeDriverManager().install(), log_output=os.devnull), 
                                options=chrome_options
                            )
                    else:
                        logging.warning("无法提取浏览器主版本号，使用默认ChromeDriver")
                        driver = webdriver.Chrome(
                            service=Service(ChromeDriverManager().install(), log_output=os.devnull), 
                            options=chrome_options
                        )
                else:
                    # 如果无法获取Chrome版本，使用默认安装
                    logging.info("无法检测浏览器版本，使用默认ChromeDriver")
                    driver = webdriver.Chrome(
                        service=Service(ChromeDriverManager().install(), log_output=os.devnull), 
                        options=chrome_options
                    )
                
                logging.info("ChromeDriverManager安装的ChromeDriver启动成功")
            except Exception as driver_error:
                logging.error(f"ChromeDriverManager安装失败: {driver_error}")
                raise
        
        logging.info("正在访问登录页面...")
        try:
            # 添加超时设置
            driver.set_page_load_timeout(60)
            driver.get("https://www.simcompanies.com/signin/")
            # 增加页面加载等待时间
            time.sleep(10)  # 等待页面完全加载
            wait = WebDriverWait(driver, 60)  # 增加等待时间到60秒
        except Exception as page_error:
            logging.error(f"页面加载失败: {page_error}")
            # 尝试再次加载
            driver.get("https://www.simcompanies.com/signin/")
            time.sleep(10)
            wait = WebDriverWait(driver, 60)

        logging.info("查找登录表单元素...")
        try:
            # 尝试查找登录表单元素，增加重试逻辑
            email_field = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@name="email"]')))
            password_field = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@name="password"]')))
            
            logging.info("输入登录凭证...")
            email_field.send_keys(email)
            password_field.send_keys(password)
            password_field.send_keys(Keys.RETURN)
            
            logging.info("等待登录完成...")
            # 使用显式等待替代固定等待时间
            wait.until(lambda d: d.current_url != "https://www.simcompanies.com/signin/")
            logging.info(f"登录后URL: {driver.current_url}")
        except Exception as form_error:
            logging.error(f"登录表单操作失败: {form_error}")
            # 尝试获取页面截图用于调试（在无头模式下可能不可用）
            try:
                if hasattr(driver, 'save_screenshot'):
                    screenshot_path = "/tmp/login_error.png"
                    driver.save_screenshot(screenshot_path)
                    logging.info(f"已保存错误截图到: {screenshot_path}")
            except:
                pass
            # 继续使用固定等待作为备选
            time.sleep(10)

        # 增强的登录验证和cookies获取
        try:
            # 等待页面完全加载和会话建立
            time.sleep(5)
            
            # 获取所有cookies
            cookies = driver.get_cookies()
            session_cookies = {cookie['name']: cookie['value'] for cookie in cookies}
            
            # 增强的cookies验证
            if session_cookies:
                logging.info(f"成功获取{cookies.__len__()}个cookies")
                # 记录关键cookie信息（不记录敏感值）
                cookie_names = list(session_cookies.keys())
                logging.info(f"Cookie名称列表: {cookie_names}")
                print("登录成功，已获取cookies！")
                return session_cookies
            else:
                logging.error("未获取到任何cookies，登录可能失败")
                print("未获取到任何cookies，登录可能失败")
                # 检查是否有错误消息或验证码
                try:
                    error_elements = driver.find_elements(By.XPATH, '//div[contains(@class, "error") or contains(text(), "error")]')
                    for element in error_elements:
                        logging.warning(f"页面错误信息: {element.text}")
                except:
                    pass
                return None
        except Exception as cookies_error:
            logging.error(f"获取cookies时出错: {cookies_error}")
            return None
    except Exception as e:
        logging.error(f"登录时出现问题: {str(e)}")
        print(f"登录时出现问题: {str(e)}")
        
        # 增强的错误诊断信息收集
        if driver:
            try:
                # 获取页面标题
                page_title = driver.title
                logging.error(f"页面标题: {page_title}")
                print(f"页面标题: {page_title}")
                
                # 获取当前URL
                current_url = driver.current_url
                logging.error(f"当前URL: {current_url}")
                print(f"当前URL: {current_url}")
                
                # 查找页面上可能的错误消息
                try:
                    error_messages = []
                    # 查找各种可能的错误消息元素
                    selectors = [
                        '//div[contains(@class, "error")]',
                        '//div[contains(@class, "alert-danger")]',
                        '//div[contains(@class, "warning")]',
                        '//span[contains(@class, "error")]',
                        '//p[contains(text(), "error") or contains(text(), "Error")]'
                    ]
                    
                    for selector in selectors:
                        error_elements = driver.find_elements(By.XPATH, selector)
                        for element in error_elements:
                            if element.text.strip():
                                error_messages.append(element.text.strip())
                    
                    if error_messages:
                        for msg in error_messages:
                            logging.error(f"页面错误消息: {msg}")
                            print(f"页面错误消息: {msg}")
                except Exception as msg_error:
                    logging.warning(f"无法提取错误消息: {msg_error}")
                
                # 只记录页面源码的前1000个字符用于调试
                try:
                    page_source = driver.page_source[:1000]
                    logging.debug(f"页面源码预览: {page_source}...")
                except:
                    logging.error("无法获取页面源码")
                    
            except Exception as diag_error:
                logging.error(f"错误诊断失败: {diag_error}")
        
        # 打印系统环境信息用于调试
        logging.debug(f"操作系统: {os.name}")
        logging.debug(f"Python版本: {platform.python_version() if 'platform' in globals() else 'unknown'}")
        
        return None
    finally:
        # 增强的资源清理逻辑
        if driver:
            try:
                # 尝试关闭所有窗口
                try:
                    for window_handle in driver.window_handles:
                        try:
                            driver.switch_to.window(window_handle)
                            driver.close()
                        except:
                            pass
                except:
                    pass
                
                # 强制退出WebDriver
                driver.quit()
                logging.info("ChromeDriver已成功关闭")
            except Exception as quit_error:
                logging.error(f"关闭ChromeDriver时出错: {quit_error}")
                # 尝试使用更强制的方式清理资源
                try:
                    import signal
                    import subprocess
                    import psutil
                    # 获取WebDriver进程并终止
                    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                        try:
                            if 'chromedriver' in ' '.join(proc.info['cmdline']):
                                proc.kill()
                                logging.info(f"已强制终止ChromeDriver进程: {proc.info['pid']}")
                        except:
                            pass
                except:
                    logging.error("强制清理资源失败")
                    
        logging.info("登录函数执行完毕")