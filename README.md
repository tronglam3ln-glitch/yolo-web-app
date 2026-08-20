# YOLO Object Detection Web Application

## Project Goal

This project is an image and video object-detection web application built using Python (FastAPI), React (Vite), and Ultralytics YOLO. It allows users to upload images and short video clips to analyze and detect objects in real time.

## Team Members

- **Nguyen Thao Nguyen**
- **Nguyen Trong Lam**
- **Ta Truong Son**

## Branch Rules & Team Workflow

To maintain a clean and reliable repository, our team follows these mandatory workflow rules:

1. **No Direct Commits to `main`:** The `main` branch is protected. All new code must be developed on separate feature or fix branches.
2. **Branch Naming Conventions:**
   - Features: `feature/<feature-name>` (e.g., `feature/backend-image-detection`)
   - Bug fixes: `fix/<issue-name>` (e.g., `fix/video-upload-error`)
3. **Pull Request (PR) & Code Review:**
   - Every branch must be submitted via a Pull Request into `main`.
   - PRs must be reviewed and approved by a teammate before merging.
4. **Clean Commit History:**
   - Write descriptive commit messages (e.g., `feat: add FastAPI startup handler`).
   - No secrets or temporary generated files should ever be committed.

## Local Prerequisites

Before running or contributing to this project locally, ensure you have installed:

- **Operating System:** Linux / Windows / macOS
- **Python:** `3.10+` (for local backend development)
- **Node.js:** `20.x+` (for local frontend development)
- **Docker & Docker Compose:** Required for running the application via containers.
  - **Linux (Ubuntu):** Install [Docker Engine](https://docs.docker.com/engine/install/ubuntu/) and [Docker Compose plugin](https://docs.docker.com/compose/install/linux/).
  - **Windows / macOS:** Install [Docker Desktop](https://docs.docker.com/desktop/) (includes Docker Engine and Compose).

---

# Backend - YOLO Detection API

FastAPI + Ultralytics YOLOv8. Chạy hoàn toàn local, không Docker, không database.

## 1. Cài đặt

cd backend
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

Lần chạy đầu tiên, Ultralytics sẽ tự động tải file yolov8n.pt (~6MB) về máy — cần có kết nối internet.

Đã kết nối sau lần đầu, những lần sau chỉ cần:

cd backend
.\.venv\Scripts\Activate.ps1      # macOS/Linux: source .venv/bin/activate

## 2. Chạy server

uvicorn main:app --reload --port 8000

- API docs (Swagger UI, tự sinh bởi FastAPI): http://localhost:8000/docs
- Health check: http://localhost:8000/health

## 3. API Contract

### GET /health

Trả về trạng thái server + model.

{ 
  "status": "ok", 
  "model_loaded": true, 
  "model_name": "yolov8n.pt" 
}

### POST /api/detect/image

multipart/form-data:
| field | type | bắt buộc | ghi chú |
|---|---|---|---|
| file | file | có | jpg/jpeg/png, tối đa 10MB |
| confidence | float | không (mặc định 0.25) | 0.0 - 1.0 |

Response 200:

{
  "annotated_image_base64": "...",
  "detections": [
    {
      "class_id": 0,
      "class_name": "person",
      "confidence": 0.87,
      "bbox": { "x1": 10.2, "y1": 20.5, "x2": 100.1, "y2": 300.4 }
    }
  ],
  "count": 1,
  "processing_time_ms": 45.32,
  "confidence_threshold": 0.25
}

### POST /api/detect/video

multipart/form-data:
| field | type | bắt buộc | ghi chú |
|---|---|---|---|
| file | file | có | .mp4, tối đa 50MB, tối đa 15 giây |
| confidence | float | không (mặc định 0.25) | 0.0 - 1.0 |

Response 200:

{
  "result_video_url": "/static/processed_video.mp4",
  "detections": [],
  "processing_time_ms": 1250.45,
  "confidence_threshold": 0.25
}

---

# Frontend - Web Application (React + Vite)

Giao diện người dùng tương tác được xây dựng bằng React và Vite, kết nối REST API với Backend FastAPI để xử lý nhận diện vật thể.

## 1. Cài đặt

cd frontend
npm install

## 2. Chạy ứng dụng Frontend

npm run dev

- Giao diện Web: http://localhost:5173

## 3. Tính năng chính trên UI

- 📸 **Nhận diện Ảnh**: Tải ảnh (.jpg, .jpeg, .png), xem trước và hiển thị kết quả khoanh vùng (bounding box) kèm danh sách phân loại chi tiết.
- 🎥 **Nhận diện Video**: Hỗ trợ định dạng .mp4, xem trước và phát trực tiếp video kết quả đã được xử lý AI.
- 🎚️ **Thanh điều chỉnh Confidence Threshold**: Tùy chỉnh độ tin cậy trực tiếp từ 0.10 đến 1.00.
- ⏱️ **Báo cáo chi tiết**: Hiển thị thời gian xử lý (ms) và thống kê danh sách vật thể phát hiện được.

---

## 🐳 Running with Docker (Recommended)

Run the entire stack (Backend + Frontend) with a single command without setting up local Python or Node environments.

### 1. Clone the Repository
First, clone the project repository to your local machine and navigate into the project folder:
```bash
git clone [https://github.com/](https://github.com/)<your-username>/yolo-web-app.git
cd yolo-web-app

### 2. One-Command Startup
Build and launch all services simultaneously:
```
docker compose up --build
```
- API docs (Swagger UI, tự sinh bởi FastAPI): http://localhost:8000/docs
- Giao diện Web: http://localhost:5173

