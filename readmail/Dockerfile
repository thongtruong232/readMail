# Sử dụng Python 3.8 làm base image
FROM python:3.8-slim

# Thiết lập thư mục làm việc
WORKDIR /app

# Cài đặt các dependencies hệ thống
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt và cài đặt các Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ dự án vào container
COPY . .

# Expose port 8002 cho Daphne
EXPOSE 8002

# Thiết lập biến môi trường
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=readmailweb.settings
ENV REDIS_HOST=redis
ENV REDIS_PORT=6379

# Command để chạy Daphne
CMD ["daphne", "-b", "0.0.0.0", "-p", "8002", "readmailweb.asgi:application"] 