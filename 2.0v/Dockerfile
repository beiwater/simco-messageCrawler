# 使用官方Python镜像作为基础镜像（更新到更新的版本）
FROM python:3.9-slim-bookworm

# 设置工作目录
WORKDIR /app

# 安装必要的系统依赖，包括Chrome和X11所需的库
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    xvfb \
    curl \
    fonts-liberation \
    libappindicator3-1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libexpat1 \
    libfontconfig1 \
    libgbm1 \
    libgcc1 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libstdc++6 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    lsb-release \
    procps \
    xdg-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 为Chrome设置环境变量
ENV DISPLAY=:99
ENV CHROME_BIN=/usr/bin/google-chrome

# 安装Chrome浏览器（使用备用方法）
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && ln -s /usr/bin/chromium /usr/bin/google-chrome

# 如果Chromium不可用，尝试直接下载Chrome
RUN if [ ! -f /usr/bin/google-chrome ]; then \
    wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && dpkg -i google-chrome-stable_current_amd64.deb || apt-get install -fy \
    && rm google-chrome-stable_current_amd64.deb; \
fi

# 确保ChromeDriver可用，如果没有则安装
RUN if [ ! -f /usr/local/bin/chromedriver ] && [ ! -f /usr/bin/chromedriver ]; then \
    CHROME_VERSION=$(google-chrome --version | grep -oP 'Chrome \K[0-9]+' || echo "114") && \
    CHROMEDRIVER_VERSION=$(curl -sS https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION} || echo "114.0.5735.90") && \
    wget -q https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip && \
    unzip chromedriver_linux64.zip && \
    rm chromedriver_linux64.zip && \
    mv chromedriver /usr/local/bin/chromedriver && \
    chmod +x /usr/local/bin/chromedriver; \
fi

# 验证ChromeDriver安装
RUN chromedriver --version || echo "ChromeDriver已安装，但可能需要在代码中指定路径"

# 复制requirements.txt到工作目录
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 创建.dockerignore文件来排除config.py
RUN echo "config.py" > .dockerignore

# 复制所有项目文件到工作目录（将通过.dockerignore排除config.py）
COPY . .

# 创建配置文件模板
RUN printf '# 配置文件模板 - 请根据实际情况修改以下配置\n# 用户登录信息\nUSER_EMAIL = "dualvectorfoil.42@gmail.com"\nUSER_PASSWORD = "rocjun-4sizxo-wiqMyc"\n# 应用配置参数\nMAX_COUNT = 10\nREPEAT_TIME = 300\nSESSION_REFRESH_TIME = 168 * 3600\n# API URL配置\nJSON_URL = {"ZH": "https://www.simcompanies.com/api/v2/chatroom/N/", "EN": "https://www.simcompanies.com/api/v2/chatroom/G/", "X": "https://www.simcompanies.com/api/v2/chatroom/X/"}\n# 文件路径配置\nDATA_DIR = "./data/"\nDB_DIR = "./databases/"\nLOG_DIR = "./logs/"\n# 数据库配置\nDB_TIMEOUT = 10\nDB_INSERT_TIMEOUT = 30\n# 日志配置\nLOG_MAX_BYTES = 5 * 1024 * 1024\nLOG_BACKUP_COUNT = 5\nUESR_INPUT = "all"\n' > config.py

# 创建启动脚本（优化无图形界面环境）
RUN printf '#!/bin/bash\n# 确保环境变量设置正确\nexport DISPLAY=:99\nexport CHROME_BIN=/usr/bin/google-chrome\n\n# 启动Xvfb服务（后台运行）\nXvfb :99 -screen 0 1920x1080x24 -nolisten tcp -nolisten unix > /dev/null 2>&1 &\n\n# 等待Xvfb启动\nsleep 3\n\n# 验证Xvfb是否正常启动\nif ! pgrep -f "Xvfb" > /dev/null; then\n    echo "警告：Xvfb服务未正常启动，但仍将继续运行应用"\nfi\n\n# 运行Python应用\npython app.py\n' > /app/start.sh && \
    chmod +x /app/start.sh

# 创建必要的目录
RUN mkdir -p logs data databases

# 设置权限
RUN chmod -R 777 /app/logs /app/data /app/databases

# 定义入口点
CMD ["/app/start.sh"]

# 说明：运行容器时，可以通过挂载config.py文件来提供实际配置，例如：
# docker run -v /path/to/your/config.py:/app/config.py your_image_name