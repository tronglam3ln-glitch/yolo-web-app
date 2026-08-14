/**
 * Thanh trượt điều chỉnh ngưỡng tin cậy (confidence threshold) gửi kèm request.
 * Khớp với giới hạn của backend: 0.0 - 1.0 (UI giới hạn 0.10 - 1.00 theo README backend).
 */
function ConfidenceSlider({ value, onChange }) {
  return (
    <div className="confidence-slider">
      <label htmlFor="confidence">
        Ngưỡng tin cậy (Confidence Threshold): <strong>{value.toFixed(2)}</strong>
      </label>
      <input
        id="confidence"
        type="range"
        min="0.1"
        max="1.0"
        step="0.05"
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
      />
    </div>
  );
}

export default ConfidenceSlider;
