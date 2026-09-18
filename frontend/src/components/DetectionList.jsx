/**
 * Danh sách chi tiết các vật thể được nhận diện, khớp với field "detections"
 * trong response của cả /api/detect/image và /api/detect/video.
 */
function DetectionList({ detections }) {
  if (!detections || detections.length === 0) return null;

  return (
    <div className="detection-list">
      <h4>Chi tiết danh sách:</h4>
      <ul>
        {detections.map((det, idx) => (
          <li key={idx}>
            <strong>{det.class_name}</strong> — Độ tin cậy:{' '}
            {(det.confidence * 100).toFixed(1)}%
          </li>
        ))}
      </ul>
    </div>
  );
}

export default DetectionList;
