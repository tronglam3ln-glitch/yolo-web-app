/**
 * Khung chọn file + xem trước ảnh/video trước khi gửi lên backend.
 */
function UploadPanel({ fileType, previewUrl, onFileChange }) {
  const handleChange = (e) => {
    const file = e.target.files[0];
    if (file) onFileChange(file);
  };

  return (
    <div className="upload-panel">
      <input
        type="file"
        accept={fileType === 'image' ? 'image/*' : 'video/mp4'}
        onChange={handleChange}
      />

      {previewUrl && (
        <div className="upload-panel__preview">
          <p className="upload-panel__preview-label">Xem trước:</p>
          {fileType === 'image' ? (
            <img src={previewUrl} alt="Xem trước file đã chọn" />
          ) : (
            <video src={previewUrl} controls />
          )}
        </div>
      )}
    </div>
  );
}

export default UploadPanel;
