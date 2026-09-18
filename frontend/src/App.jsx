import { useState } from 'react';
import ModeSwitch from './components/ModeSwitch';
import UploadPanel from './components/UploadPanel';
import ConfidenceSlider from './components/ConfidenceSlider';
import ResultPanel from './components/ResultPanel';
import { detectObjects } from './api/detectionApi';
import './App.css';

function App() {
  const [fileType, setFileType] = useState('image'); // 'image' | 'video'
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [confidence, setConfidence] = useState(0.25);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const resetOutput = () => {
    setResult(null);
    setError(null);
  };

  const handleModeChange = (mode) => {
    setFileType(mode);
    setSelectedFile(null);
    setPreviewUrl(null);
    resetOutput();
  };

  const handleFileChange = (file) => {
    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
    resetOutput();
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError(`Vui lòng chọn một file ${fileType === 'image' ? 'ảnh' : 'video'}!`);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const data = await detectObjects(fileType, selectedFile, confidence);
      setResult(data);
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'Lỗi kết nối tới Server Backend!');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <h1 className="app__title">YOLOv8 Object Detection Dashboard</h1>

      <ModeSwitch mode={fileType} onChange={handleModeChange} />

      <UploadPanel
        fileType={fileType}
        previewUrl={previewUrl}
        onFileChange={handleFileChange}
      />

      <ConfidenceSlider value={confidence} onChange={setConfidence} />

      <button
        className="app__submit"
        onClick={handleUpload}
        disabled={loading}
      >
        {loading ? 'Đang xử lý...' : 'Bắt đầu Phân tích'}
      </button>

      {error && <div className="app__error">{error}</div>}

      <ResultPanel fileType={fileType} result={result} />
    </div>
  );
}

export default App;
