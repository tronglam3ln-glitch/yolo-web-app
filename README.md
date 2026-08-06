# YOLO Object Detection Web Application

## Project Goal

This project is an image and video object-detection web application built using Python (FastAPI), React (Vite), and Ultralytics YOLO. It allows users to upload images and short video clips to analyze and detect objects in real time.

## Team Members
* **Nguyen Thao Nguyen**
* **Nguyen Trong Lam**
* **Ta Truong Son**  
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

- **Operating System:** Linux (Ubuntu/Debian recommended)
- **Python:** `3.10+` (for backend development)

# Backend - YOLO Detection API

FastAPI + Ultralytics YOLOv8. Chạy hoàn toàn local, không Docker, không database.

## 1. Cài đặt

```bash
cd backend
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Lần chạy đầu tiên, Ultralytics sẽ tự động tải file `yolov8n.pt` (~6MB) về máy —
cần có kết nối internet.

Đã kết nối sau lần đầu, những lần sau chỉ cần:

​`powershell
cd backend
.\.venv\Scripts\Activate.ps1      # macOS/Linux: source .venv/bin/activate
​`

## 2. Chạy server

```bash
uvicorn main:app --reload --port 8000
```

- API docs (Swagger UI, tự sinh bởi FastAPI): http://localhost:8000/docs
- Health check: http://localhost:8000/health

## 3. API Contract

### `GET /health`

Trả về trạng thái server + model.

```json
{ "status": "ok", "model_loaded": true, "model_name": "yolov8n.pt" }
```

### `POST /api/detect/image`

`multipart/form-data`:
| field | type | bắt buộc | ghi chú |
|---|---|---|---|
| `file` | file | có | jpg/jpeg/png, tối đa 10MB |
| `confidence` | float | không (mặc định 0.25) | 0.0 - 1.0 |

Response 200:

```json
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
```

### `POST /api/detect/video`

`multipart/form-data`:
| field | type | bắt buộc | ghi chú |
|---|---|---|---|
| `file` | file | có | .mp4, tối đa 50MB, tối đa 15 giây |
| `confidence` | float | không (mặc định 0.25) | 0.0 - 1.0 |

Response 200:

```json
{
  "result_video_url": "/api/results/<job_id>",
  "total_frames": 90,
  "class_counts": { "person": 120, "car": 15 },
  "count": 135,
  "processing_time_ms": 3200.11,
  "confidence_threshold": 0.25
}
```

Tải video kết quả bằng `GET {result_video_url}` (trả về file mp4).

## 4. Giới hạn phiên bản hiện tại

- Ảnh: jpg/jpeg/png, tối đa `MAX_IMAGE_SIZE_MB` (mặc định 10MB).
- Video: chỉ .mp4, tối đa `MAX_VIDEO_SIZE_MB` (50MB) và `MAX_VIDEO_DURATION_SEC` (15s).
- Không có database, không lưu lịch sử, không login.
- File kết quả video lưu ở thư mục tạm hệ thống, không đảm bảo tồn tại lâu dài
  (sẽ bị xoá khi restart server).

## 5. Chạy test

```bash
python -m pytest -v
```

## 6. Nguồn tham khảo mã nguồn mở

Các đoạn logic sau được viết dựa theo ví dụ chính thức của Ultralytics
(đã ghi chú trực tiếp trong `main.py`):

- Cách load model 1 lần: `model = YOLO("yolov8n.pt")`
- Cách chạy inference: `model.predict(source=..., conf=...)`
- Cách vẽ bounding box có sẵn: `result.plot()`
- Cách xử lý video mà không cần tự bóc tách frame bằng OpenCV:
  `model.predict(source="video.mp4", save=True)`

Tài liệu gốc: https://docs.ultralytics.com/modes/predict/
