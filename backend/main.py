"""
Luồng xử lý: browser -> frontend -> backend (file này) -> YOLO model -> response -> frontend.
Các đoạn code có ghi chú "Tham khảo Ultralytics docs" là các đoạn được viết dựa theo
ví dụ chính thức trong tài liệu mã nguồn mở của Ultralytics YOLO:
https://docs.ultralytics.com/modes/predict/
https://docs.ultralytics.com/usage/python/
"""
import logging
import os
import shutil
import tempfile
import time
import uuid
from pathlib import Path
from typing import List, Optional
import subprocess
import imageio_ffmpeg

import cv2
import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from PIL import Image
import io
import base64

from ultralytics import YOLO

# ============================================================================
# 1. CẤU HÌNH CHUNG
# ============================================================================
# Đọc từ biến môi trường để dễ chuyển sang Docker/Cloud ở các tuần sau,
# nhưng luôn có giá trị mặc định để chạy local ngay bằng `uvicorn main:app`.
MODEL_NAME = os.getenv("MODEL_NAME", "yolov8n.pt")
ALLOWED_ORIGIN = os.getenv("ALLOWED_ORIGIN", "*")  # mở "*" để test local

MAX_IMAGE_SIZE_MB = float(os.getenv("MAX_IMAGE_SIZE_MB", "10"))
MAX_VIDEO_SIZE_MB = float(os.getenv("MAX_VIDEO_SIZE_MB", "50"))
MAX_VIDEO_DURATION_SEC = float(os.getenv("MAX_VIDEO_DURATION_SEC", "15"))

ALLOWED_IMAGE_EXT = {".jpg", ".jpeg", ".png"}
ALLOWED_VIDEO_EXT = {".mp4"}

# Thư mục tạm để lưu file upload và kết quả video (dọn dẹp sau khi trả response)
BASE_TMP_DIR = Path(tempfile.gettempdir()) / "yolo_backend"
UPLOAD_TMP_DIR = BASE_TMP_DIR / "uploads"
RESULTS_DIR = BASE_TMP_DIR / "results"
UPLOAD_TMP_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# 2. LOGGING
# ============================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("yolo-backend")

# ============================================================================
# 3. KHỞI TẠO APP + CORS
# ============================================================================
app = FastAPI(
    title="YOLO Detection API",
    description="Backend nhận diện vật thể bằng Ultralytics YOLOv8 cho ảnh và video ngắn.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    # Chỉ mở đúng origin của frontend khi deploy thật; để "*" phục vụ test local.
    allow_origins=[ALLOWED_ORIGIN] if ALLOWED_ORIGIN != "*" else ["*"],
    # allow_credentials chỉ bật khi có origin cụ thể (deploy thật, cần gửi cookie/session).
    # Khi test local với "*", phải tắt credentials vì "*" + credentials=True bị trình duyệt chặn.
    allow_credentials=ALLOWED_ORIGIN != "*",
    allow_methods=["*"],
    allow_headers=["*"],
)
# Biến toàn cục giữ model - yêu cầu bắt buộc: load ĐÚNG MỘT LẦN khi startup.
model: Optional[YOLO] = None


@app.on_event("startup")
def load_model() -> None:
    """
    Load model YOLOv8 một lần duy nhất khi server khởi động.

    Tham khảo Ultralytics docs: cách khởi tạo model chỉ cần
        model = YOLO("yolov8n.pt")
    Ultralytics sẽ tự động tải file trọng số (.pt) về nếu máy chưa có sẵn.
    """
    global model
    logger.info("Đang load YOLO model: %s ...", MODEL_NAME)
    try:
        model = YOLO(MODEL_NAME)
        # Tham khảo Ultralytics docs: chạy 1 lần "warm-up" trên ảnh giả để
        # framework build sẵn graph/cache, giúp request đầu tiên của user không bị chậm.
        dummy_frame = np.zeros((640, 640, 3), dtype=np.uint8)
        model.predict(source=dummy_frame, verbose=False)
        logger.info("Load model thành công, class names: %s", model.names)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Không thể load YOLO model lúc startup")
        # Nếu model load lỗi thì để app crash sớm ngay khi startup, tốt hơn là
        # crash âm thầm lúc user gọi API.
        raise RuntimeError(f"Model load failed: {exc}") from exc


@app.on_event("shutdown")
def cleanup_tmp_dirs() -> None:
    """Dọn dẹp toàn bộ file tạm khi server tắt (best-effort, không raise lỗi)."""
    for d in (UPLOAD_TMP_DIR, RESULTS_DIR):
        shutil.rmtree(d, ignore_errors=True)
        d.mkdir(parents=True, exist_ok=True)


# ============================================================================
# 4. HÀM TIỆN ÍCH (VALIDATION)
# ============================================================================
def _get_extension(filename: str) -> str:
    return Path(filename or "").suffix.lower()


def validate_image_upload(file: UploadFile, content: bytes) -> None:
    """Kiểm tra định dạng và dung lượng file ảnh, raise HTTPException 4xx nếu sai."""
    ext = _get_extension(file.filename)
    if ext not in ALLOWED_IMAGE_EXT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Định dạng file không hỗ trợ: '{ext or 'không rõ'}'. "
            f"Chỉ chấp nhận: {', '.join(sorted(ALLOWED_IMAGE_EXT))}",
        )

    size_mb = len(content) / (1024 * 1024)
    if size_mb > MAX_IMAGE_SIZE_MB:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File quá lớn ({size_mb:.2f} MB). Giới hạn cho phép: {MAX_IMAGE_SIZE_MB} MB.",
        )

    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="File ảnh rỗng, vui lòng chọn lại file."
        )


def validate_video_upload(file: UploadFile, content: bytes) -> None:
    """Kiểm tra định dạng và dung lượng file video, raise HTTPException 4xx nếu sai."""
    ext = _get_extension(file.filename)
    if ext not in ALLOWED_VIDEO_EXT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Định dạng video không hỗ trợ: '{ext or 'không rõ'}'. "
            f"Chỉ chấp nhận: {', '.join(sorted(ALLOWED_VIDEO_EXT))}",
        )

    size_mb = len(content) / (1024 * 1024)
    if size_mb > MAX_VIDEO_SIZE_MB:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Video quá lớn ({size_mb:.2f} MB). Giới hạn cho phép: {MAX_VIDEO_SIZE_MB} MB.",
        )

    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="File video rỗng, vui lòng chọn lại file."
        )


def validate_confidence(confidence: float) -> float:
    if not (0.0 <= confidence <= 1.0):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="confidence phải nằm trong khoảng [0.0, 1.0].",
        )
    return confidence


def check_video_duration(video_path: Path) -> float:
    """Mở video bằng OpenCV để kiểm tra thời lượng, raise 400 nếu vượt giới hạn."""
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        cap.release()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không thể đọc file video. File có thể bị hỏng hoặc sai định dạng.",
        )

    fps = cap.get(cv2.CAP_PROP_FPS) or 0
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
    cap.release()

    duration_sec = (frame_count / fps) if fps > 0 else 0
    if duration_sec > MAX_VIDEO_DURATION_SEC:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Video dài {duration_sec:.1f}s vượt quá giới hạn "
                f"{MAX_VIDEO_DURATION_SEC}s cho phiên bản demo này."
            ),
        )
    return duration_sec


def encode_image_to_base64(bgr_image: np.ndarray) -> str:
    """Encode ảnh numpy (BGR - định dạng OpenCV) sang chuỗi base64 (JPEG)."""
    success, buffer = cv2.imencode(".jpg", bgr_image)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi khi encode ảnh kết quả.",
        )
    return base64.b64encode(buffer).decode("utf-8")


# ============================================================================
# 5. ENDPOINTS
# ============================================================================
@app.get("/health")
def health_check():
    """Health check đơn giản, sẽ được Docker/Cloud dùng ở các tuần sau."""
    return {
        "status": "ok" if model is not None else "model_not_loaded",
        "model_loaded": model is not None,
        "model_name": MODEL_NAME,
    }


@app.post("/api/detect/image")
async def detect_image(
    file: UploadFile = File(...),
    confidence: float = Form(0.25),
):
    """
    Nhận 1 ảnh (jpg/jpeg/png), chạy YOLO, trả về:
    - annotated_image_base64: ảnh đã vẽ bounding box, dạng base64 (JPEG)
    - detections: danh sách object {class_name, confidence, bbox}
    - count: tổng số object phát hiện được
    - processing_time_ms: thời gian xử lý (mili giây)
    """
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model chưa sẵn sàng, vui lòng thử lại sau.",
        )

    validate_confidence(confidence)

    content = await file.read()
    validate_image_upload(file, content)

    # Decode bytes -> ảnh PIL -> numpy array (RGB)
    try:
        pil_image = Image.open(io.BytesIO(content)).convert("RGB")
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Không thể đọc file ảnh, file có thể bị hỏng: {exc}",
        ) from exc

    np_image = np.array(pil_image)

    start_time = time.perf_counter()
    try:
        # Tham khảo Ultralytics docs (Python usage): model(source, conf=...) hoặc
        # model.predict(source, conf=...) trả về list các đối tượng Results.
        results = model.predict(source=np_image, conf=confidence, verbose=False)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Lỗi trong lúc inference ảnh")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi xử lý model YOLO: {exc}",
        ) from exc
    processing_time_ms = (time.perf_counter() - start_time) * 1000

    result = results[0]

    # Tham khảo Ultralytics docs: result.plot() trả về ảnh numpy (BGR) đã vẽ sẵn
    # bounding box + label + confidence, không cần tự vẽ bằng OpenCV.
    annotated_bgr = result.plot()
    annotated_base64 = encode_image_to_base64(annotated_bgr)

    detections: List[dict] = []
    boxes = result.boxes
    if boxes is not None:
        for box in boxes:
            cls_id = int(box.cls[0])
            conf_score = float(box.conf[0])
            x1, y1, x2, y2 = [float(v) for v in box.xyxy[0]]
            detections.append(
                {
                    "class_id": cls_id,
                    "class_name": model.names.get(cls_id, str(cls_id)),
                    "confidence": round(conf_score, 4),
                    "bbox": {
                        "x1": round(x1, 2),
                        "y1": round(y1, 2),
                        "x2": round(x2, 2),
                        "y2": round(y2, 2),
                    },
                }
            )

    return JSONResponse(
        content={
            "annotated_image_base64": annotated_base64,
            "detections": detections,
            "count": len(detections),
            "processing_time_ms": round(processing_time_ms, 2),
            "confidence_threshold": confidence,
        }
    )


@app.post("/api/detect/video")
async def detect_video(
    file: UploadFile = File(...),
    confidence: float = Form(0.25),
):
    """
   
    """
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model chưa sẵn sàng, vui lòng thử lại sau.",
        )

    validate_confidence(confidence)

    content = await file.read()
    validate_video_upload(file, content)

    job_id = uuid.uuid4().hex
    upload_path = UPLOAD_TMP_DIR / f"{job_id}.mp4"
    job_output_dir = RESULTS_DIR / job_id

    try:
        with open(upload_path, "wb") as f:
            f.write(content)

        # Kiểm tra thời lượng để tránh video quá dài làm treo server (theo giới hạn đề bài)
        check_video_duration(upload_path)

        start_time = time.perf_counter()
        try:
            # Tham khảo Ultralytics docs (Predict mode - Videos):
            # dùng trực tiếp model.predict(source=..., save=True) để Ultralytics tự
            # đọc từng frame, chạy inference, vẽ bounding box và ghi ra video kết quả,
            # thay vì tự bóc tách frame bằng OpenCV (tiết kiệm thời gian dev).
            results = model.predict(
                source=str(upload_path),
                conf=confidence,
                save=True,
                project=str(RESULTS_DIR),
                name=job_id,
                exist_ok=True,
                verbose=False,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Lỗi trong lúc inference video")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Lỗi xử lý model YOLO trên video: {exc}",
            ) from exc
        processing_time_ms = (time.perf_counter() - start_time) * 1000

        # Tổng hợp số lượng object theo từng class trên toàn bộ frame của video.
        class_counts: dict = {}
        total_detections = 0
        for frame_result in results:
            boxes = frame_result.boxes
            if boxes is None:
                continue
            for box in boxes:
                cls_id = int(box.cls[0])
                cls_name = model.names.get(cls_id, str(cls_id))
                class_counts[cls_name] = class_counts.get(cls_name, 0) + 1
                total_detections += 1


        
        # Ultralytics lưu video output trong project/name/<tên_file_gốc>.mp4 (hoặc .avi
        # tuỳ codec hệ thống). Tìm đúng file đó để trả về cho client.
        output_video_path = _find_output_video(job_output_dir)
        if output_video_path is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Model chạy thành công nhưng không tìm thấy file video kết quả.",
            )

        output_video_path = reencode_to_h264(output_video_path)

        return JSONResponse(
            content={
                "result_video_url": f"/api/results/{job_id}",
                "total_frames": len(results),
                "class_counts": class_counts,
                "count": total_detections,
                "processing_time_ms": round(processing_time_ms, 2),
                "confidence_threshold": confidence,
            }
        )
    finally:
        # Dọn file upload gốc, chỉ giữ lại video kết quả để phục vụ tải xuống.
        upload_path.unlink(missing_ok=True)


def _find_output_video(job_output_dir: Path) -> Optional[Path]:
    """Tìm file video (.mp4/.avi) đầu tiên trong thư mục output của 1 job."""
    if not job_output_dir.exists():
        return None
    for ext in (".mp4", ".avi"):
        found = list(job_output_dir.glob(f"*{ext}"))
        if found:
            return found[0]
    return None
def reencode_to_h264(input_path: Path) -> Path:
    """
    Re-encode video sang H.264 (yuv420p) để trình duyệt phát được qua thẻ <video>.
    Ultralytics/OpenCV mặc định ghi bằng codec mp4v, hầu hết browser không hỗ trợ
    phát trực tiếp codec này dù đuôi file là .mp4.
    """
    output_path = input_path.with_name(f"{input_path.stem}_h264.mp4")
    ffmpeg_bin = imageio_ffmpeg.get_ffmpeg_exe()

    cmd = [
        ffmpeg_bin, "-y",
        "-i", str(input_path),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",  # cho phép phát trước khi tải xong toàn bộ file
        "-an",  # video YOLO output không có audio track, bỏ qua xử lý audio
        str(output_path),
    ]

    try:
        subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except subprocess.CalledProcessError as exc:
        logger.error("ffmpeg re-encode thất bại: %s", exc.stderr)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Xử lý video kết quả thất bại (re-encode).",
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Re-encode video quá thời gian cho phép.",
        ) from exc

    # Xoá file gốc codec mp4v, chỉ giữ bản h264 để phục vụ FE
    input_path.unlink(missing_ok=True)
    return output_path


def _find_saved_output_video(job_output_dir: Path) -> Optional[Path]:
    """Tìm file video kết quả trong thư mục output của 1 job.
    Ưu tiên file đã re-encode h264 (phục vụ phát trên browser)."""
    if not job_output_dir.exists():
        return None
    h264_files = list(job_output_dir.glob("*_h264.mp4"))
    if h264_files:
        return h264_files[0]
    for ext in (".mp4", ".avi"):
        found = list(job_output_dir.glob(f"*{ext}"))
        if found:
            return found[0]
    return None


@app.get("/api/results/{job_id}")
def get_result_video(job_id: str):
    """Trả về file video kết quả (đã re-encode h264) cho browser phát/tải xuống."""
    job_output_dir = RESULTS_DIR / job_id
    video_path = _find_saved_output_video(job_output_dir)
    if video_path is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy video kết quả cho job_id này.",
        )
    return FileResponse(
        path=str(video_path),
        media_type="video/mp4",
        filename=video_path.name,
    )


# ============================================================================
# 6. GLOBAL EXCEPTION HANDLER (chống crash server với lỗi không lường trước)
# ============================================================================
@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc: Exception):
    logger.exception("Lỗi không xác định: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Đã xảy ra lỗi không xác định trên server."},
    )