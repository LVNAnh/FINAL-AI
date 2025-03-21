# Product Analysis Platform

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/TensorFlow-2.13.0-orange.svg" alt="TensorFlow Version">
  <img src="https://img.shields.io/badge/Flask-2.3.3-lightgrey.svg" alt="Flask Version">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
</p>

Nền tảng phân tích sản phẩm E-commerce tích hợp AI cho phép:

- Phân loại hình ảnh sản phẩm sử dụng mô hình MobileNetV2
- Phân tích tình cảm đánh giá khách hàng sử dụng Hugging Face API
- Tìm kiếm và gợi ý sản phẩm từ các nền tảng thương mại điện tử phổ biến (Đang phát triển)

## Tính năng

- **Phân loại hình ảnh sản phẩm**: Sử dụng mô hình TensorFlow MobileNetV2 để nhận dạng sản phẩm từ hình ảnh người dùng tải lên.
- **Phân tích đánh giá**: Phân tích tình cảm đánh giá khách hàng (tích cực, tiêu cực, trung tính) sử dụng Hugging Face API.
- **Tìm kiếm sản phẩm tương tự**: Dựa trên kết quả phân loại hình ảnh, tìm kiếm sản phẩm tương tự trên các nền tảng thương mại điện tử. (Đang phát triển)
- **API Docs**: API documentation được tích hợp sẵn tại `/api/docs`.

## Yêu cầu

- Python 3.10+
- Docker (tùy chọn, nếu muốn chạy ứng dụng trong container)

## Cài đặt

### Phương pháp 1: Sử dụng Python

1. Clone dự án:

```bash
git clone https://github.com/LVNAnh/FINAL-AI.git
cd FINAL-AI
```

2. Cài đặt các dependencies:

```bash
pip install -r requirements.txt
```

3. Thiết lập token Hugging Face:

```bash
export HUGGING_FACE_TOKEN=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
```

4. Chạy ứng dụng:

```bash
python app.py
```

Ứng dụng sẽ chạy tại địa chỉ: http://localhost:5000

### Phương pháp 2: Sử dụng Docker

1. Clone dự án:

```bash
git clone https://github.com/LVNAnh/FINAL-AI.git
cd FINAL-AI
```

2. Build và chạy container với Docker Compose:

```bash
docker-compose up --build
```

Hoặc sử dụng Docker trực tiếp:

```bash
docker build -t final-api .
docker run -p 5000:5000 -e HUGGING_FACE_TOKEN=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 final-api
```

Ứng dụng sẽ chạy tại địa chỉ: http://localhost:5000

## Sử dụng

### Giao diện web

1. Truy cập vào http://localhost:5000
2. Tải lên hình ảnh sản phẩm trong phần "Phân loại sản phẩm"
3. Nhập đánh giá khách hàng trong phần "Phân tích cảm xúc khách hàng"

### API Endpoints

#### Phân loại hình ảnh

```http
POST /classify
```

**Request:**

- Form data với trường `file` chứa hình ảnh cần phân loại

**Response:**

```json
{
  "success": true,
  "predictions": [
    {
      "class_name": "Tên lớp",
      "class_id": "n07753592",
      "confidence": 95.42
    }
  ]
}
```

#### Phân tích đánh giá

```http
POST /analyze-sentiment
```

**Request:**

```json
{
  "text": "This product is amazing!"
}
```

**Response:**

```json
{
  "success": true,
  "overall_sentiment": "Positive",
  "details": [
    {
      "sentiment": "Positive",
      "confidence": 98.45
    }
  ],
  "text": "This product is amazing!"
}
```

#### Kiểm tra trạng thái

```http
GET /health
```

**Response:**

```json
{
  "status": "healthy",
  "services": {
    "image_classification": true,
    "sentiment_analysis": true,
    "labels_loaded": true
  },
  "version": "1.0.0"
}
```

## Cấu trúc dự án

```
.
├── app.py                 # Ứng dụng Flask chính
├── Dockerfile             # Cấu hình Docker
├── docker-compose.yml     # Cấu hình Docker Compose
├── image_service.py       # Dịch vụ phân loại hình ảnh
├── requirements.txt       # Dependencies Python
├── sentiment_service.py   # Dịch vụ phân tích tình cảm
└── templates/
    └── index.html         # Giao diện người dùng
```

## Triển khai lên Render

1. Fork hoặc clone repository này và đẩy lên GitHub của bạn.

2. Đăng ký tài khoản tại [Render](https://render.com/).

3. Trong Render Dashboard, chọn "New" > "Web Service".

4. Kết nối với repository GitHub của bạn.

5. Cấu hình dịch vụ:

   - **Name**: FINAL-API
   - **Environment**: Docker
   - **Region**: Chọn khu vực phù hợp
   - Thiết lập biến môi trường:
     - `HUGGING_FACE_TOKEN`: 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
     - `PORT`: 5000

6. Click "Create Web Service".

```

Link Web Service đã Deploy lên Render (Đã bao gồm giao diện cho Client):[Link](https://e-commerce-e8m2.onrender.com/)
```
