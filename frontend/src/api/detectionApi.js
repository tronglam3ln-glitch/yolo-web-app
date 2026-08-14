import axios from 'axios';

// Đọc URL backend từ biến môi trường (xem file .env.example).
// Nếu không cấu hình, mặc định trỏ về backend FastAPI chạy local.
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const DETECT_ENDPOINTS = {
  image: '/api/detect/image',
  video: '/api/detect/video',
};

/**
 * Gửi file (ảnh hoặc video) lên backend để nhận diện vật thể.
 * @param {'image' | 'video'} fileType
 * @param {File} file
 * @param {number} confidence - ngưỡng tin cậy 0.0 - 1.0
 */
export async function detectObjects(fileType, file, confidence) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('confidence', confidence);

  const { data } = await axios.post(
    `${API_BASE_URL}${DETECT_ENDPOINTS[fileType]}`,
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } }
  );

  return data;
}

/** Trả về URL đầy đủ tới video kết quả do backend trả về (đường dẫn tương đối). */
export function resolveResultVideoUrl(relativeUrl) {
  return `${API_BASE_URL}${relativeUrl}`;
}
