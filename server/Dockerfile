# 使用轻量级的 Python 3.9 基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 先复制依赖文件并安装，利用 Docker 缓存加速构建
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.tencent.com/pypi/simple/

# 复制你所有的后端代码到镜像里
COPY . .

# 暴露你的 WebSocket 端口 (3100)
EXPOSE 3100

# 启动命令 (请确保你的主入口文件叫 main.py，如果不是请替换)
CMD ["python", "main.py"]