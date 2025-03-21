FROM python:3.10-slim

WORKDIR /app

# Cài đặt các phụ thuộc hệ thống
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Sao chép file yêu cầu
COPY requirements.txt .

# Cài đặt các phụ thuộc Python
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép các file ứng dụng
COPY . .

# Tạo thư mục templates nếu chưa tồn tại
RUN mkdir -p templates

# Mở cổng
EXPOSE 5000

# Chạy ứng dụng
CMD ["python", "app.py"]