import React, { useState } from 'react';
import axios from 'axios';

// Đường dẫn API Backend của Sơn (chạy local)
const API_BASE_URL = 'http://localhost:8000';

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [confidence, setConfidence] = useState(0.25);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setResult(null);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Vui lòng chọn một file ảnh!');
      return;
    }

    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await axios.post(
        `${API_BASE_URL}/api/detect/image?conf_threshold=${confidence}`,
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      );
      setResult(response.data);
    } catch (err) {
      console.error(err);
      setError(
        err.response?.data?.detail || 'Lỗi kết nối tới Server Backend!'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif', maxWidth: '700px', margin: '0 auto' }}>
      <h2>🔍 YOLOv8 Object Detection - Team App</h2>

      {/* Upload Zone */}
      <div style={{ border: '2px dashed #007bff', borderRadius: '8px', padding: '20px', textAlign: 'center', marginBottom: '20px' }}>
        <input type="file" accept="image/*" onChange={handleFileChange} />
        {previewUrl && (
          <div style={{ marginTop: '15px' }}>
            <p><strong>Ảnh xem trước:</strong></p>
            <img src={previewUrl} alt="Preview" style={{ maxWidth: '100%', maxHeight: '250px', borderRadius: '5px' }} />
          </div>
        )}
      </div>

      {/* Threshold Slider */}
      <div style={{ marginBottom: '20px' }}>
        <label>Ngưỡng tin cậy (Confidence Threshold): <strong>{confidence}</strong></label>
        <input
          type="range"
          min="0.1"
          max="1.0"
          step="0.05"
          value={confidence}
          onChange={(e) => setConfidence(parseFloat(e.target.value))}
          style={{ width: '100%', marginTop: '5px' }}
        />
      </div>

      {/* Action Button */}
      <button
        onClick={handleUpload}
        disabled={loading}
        style={{
          width: '100%',
          padding: '12px',
          backgroundColor: loading ? '#ccc' : '#007bff',
          color: '#fff',
          border: 'none',
          borderRadius: '5px',
          fontSize: '16px',
          cursor: loading ? 'not-allowed' : 'pointer'
        }}
      >
        {loading ? '⏳ Đang xử lý AI...' : '🚀 Bắt đầu Phân tích'}
      </button>

      {/* Error Message */}
      {error && (
        <div style={{ color: 'red', marginTop: '15px', padding: '10px', backgroundColor: '#ffe6e6', borderRadius: '5px' }}>
          ⚠️ {error}
        </div>
      )}

      {/* Results Display */}
      {result && (
        <div style={{ marginTop: '30px', borderTop: '2px solid #ddd', paddingTop: '20px' }}>
          <h3>🎉 Kết quả Nhận diện</h3>
          <p>⏱️ Thời gian xử lý: <strong>{result.processing_time_ms} ms</strong></p>
          <p>📦 Vận thể phát hiện: <strong>{result.total_objects}</strong></p>

          <img
            src={result.annotated_image_base64}
            alt="Annotated Result"
            style={{ maxWidth: '100%', borderRadius: '8px', border: '1px solid #ccc' }}
          />

          <h4 style={{ marginTop: '15px' }}>Chi tiết danh sách:</h4>
          <ul>
            {result.detections.map((det, idx) => (
              <li key={idx}>
                <strong>{det.class_name}</strong> - Độ tin cậy: {(det.confidence * 100).toFixed(1)}%
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default App;