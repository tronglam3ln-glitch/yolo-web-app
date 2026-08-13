import React, { useState } from 'react';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

function App() {
  const [fileType, setFileType] = useState('image'); // 'image' hoặc 'video'
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [confidence, setConfidence] = useState(0.25);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleModeChange = (mode) => {
    setFileType(mode);
    setSelectedFile(null);
    setPreviewUrl(null);
    setResult(null);
    setError(null);
  };

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
      setError(`Vui lòng chọn một file ${fileType === 'image' ? 'ảnh' : 'video'}!`);
      return;
    }

    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('confidence', confidence);

    const endpoint = fileType === 'image'
      ? `${API_BASE_URL}/api/detect/image`
      : `${API_BASE_URL}/api/detect/video`;

    try {
      const response = await axios.post(endpoint, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
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
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif', maxWidth: '800px', margin: '0 auto' }}>
      <h2 style={{ textAlign: 'center' }}>🔍 YOLOv8 Object Detection Dashboard</h2>

      {/* Nút chọn Chế độ Ảnh / Video */}
      <div style={{ display: 'flex', gap: '20px', marginBottom: '20px', justifyContent: 'center' }}>
        <label style={{ fontSize: '16px', cursor: 'pointer' }}>
          <input
            type="radio"
            name="mode"
            checked={fileType === 'image'}
            onChange={() => handleModeChange('image')}
          />
          <b> Nhận diện Ảnh</b>
        </label>
        <label style={{ fontSize: '16px', cursor: 'pointer' }}>
          <input
            type="radio"
            name="mode"
            checked={fileType === 'video'}
            onChange={() => handleModeChange('video')}
          />
          <b> Nhận diện Video (.mp4)</b>
        </label>
      </div>

      {/* Khung Upload File */}
      <div style={{ border: '2px dashed #007bff', borderRadius: '8px', padding: '20px', textAlign: 'center', marginBottom: '20px' }}>
        <input 
          type="file" 
          accept={fileType === 'image' ? 'image/*' : 'video/mp4'} 
          onChange={handleFileChange} 
        />
        {previewUrl && (
          <div style={{ marginTop: '15px' }}>
            <p><strong>Xem trước:</strong></p>
            {fileType === 'image' ? (
              <img src={previewUrl} alt="Preview" style={{ maxWidth: '100%', maxHeight: '250px', borderRadius: '5px' }} />
            ) : (
              <video src={previewUrl} controls style={{ maxWidth: '100%', maxHeight: '250px', borderRadius: '5px' }} />
            )}
          </div>
        )}
      </div>

      {/* Thanh chỉnh Ngưỡng tin cậy */}
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

      {/* Nút Phân tích */}
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
          cursor: loading ? 'not-allowed' : 'pointer',
          fontWeight: 'bold'
        }}
      >
        {loading ? '⏳ Đang xử lý AI...' : '🚀 Bắt đầu Phân tích'}
      </button>

      {/* Hiển thị lỗi */}
      {error && (
        <div style={{ color: 'red', marginTop: '15px', padding: '10px', backgroundColor: '#ffe6e6', borderRadius: '5px' }}>
          ⚠️ {error}
        </div>
      )}

      {/* Hiển thị kết quả */}
      {result && (
        <div style={{ marginTop: '30px', borderTop: '2px solid #ddd', paddingTop: '20px' }}>
          <h3>🎉 Kết quả Nhận diện</h3>
          {result.processing_time_ms && <p>⏱️ Thời gian xử lý: <strong>{result.processing_time_ms} ms</strong></p>}

          {fileType === 'image' && result.annotated_image_base64 && (
            <img
              src={result.annotated_image_base64.startsWith('data:') ? result.annotated_image_base64 : `data:image/jpeg;base64,${result.annotated_image_base64}`}
              alt="Annotated Result"
              style={{ maxWidth: '100%', borderRadius: '8px', border: '1px solid #ccc' }}
            />
          )}

          {fileType === 'video' && result.result_video_url && (
            <video
              src={`${API_BASE_URL}${result.result_video_url}`}
              controls
              autoPlay
              style={{ maxWidth: '100%', borderRadius: '8px', border: '1px solid #ccc' }}
            />
          )}

          {result.detections && (
            <>
              <h4 style={{ marginTop: '15px' }}>Chi tiết danh sách:</h4>
              <ul>
                {result.detections.map((det, idx) => (
                  <li key={idx}>
                    <strong>{det.class_name}</strong> - Độ tin cậy: {(det.confidence * 100).toFixed(1)}%
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
      )}
    </div>
  );
}

export default App;