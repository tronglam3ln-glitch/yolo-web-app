import DetectionList from './DetectionList';
import { resolveResultVideoUrl } from '../api/detectionApi';

/**
 * Hiển thị kết quả trả về từ backend: ảnh/video đã khoanh vùng,
 * thời gian xử lý và danh sách vật thể phát hiện được.
 */
function ResultPanel({ fileType, result }) {
  if (!result) return null;

  return (
    <div className="result-panel">
      <h3>Kết quả Nhận diện</h3>

      {typeof result.processing_time_ms === 'number' && (
        <p>
          Thời gian xử lý: <strong>{result.processing_time_ms} ms</strong>
        </p>
      )}

      {fileType === 'image' && result.annotated_image_base64 && (
        <img
          className="result-panel__media"
          src={
            result.annotated_image_base64.startsWith('data:')
              ? result.annotated_image_base64
              : `data:image/jpeg;base64,${result.annotated_image_base64}`
          }
          alt="Kết quả nhận diện đã khoanh vùng"
        />
      )}

      {fileType === 'video' && result.result_video_url && (
        <video
          className="result-panel__media"
          src={resolveResultVideoUrl(result.result_video_url)}
          controls
          autoPlay
        />
      )}

      <DetectionList detections={result.detections} />
    </div>
  );
}

export default ResultPanel;
