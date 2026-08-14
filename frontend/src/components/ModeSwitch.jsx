/**
 * Cho phép người dùng chọn chế độ: nhận diện Ảnh hoặc Video.
 */
function ModeSwitch({ mode, onChange }) {
  const options = [
    { value: 'image', label: 'Nhận diện Ảnh' },
    { value: 'video', label: 'Nhận diện Video (.mp4)' },
  ];

  return (
    <div className="mode-switch">
      {options.map((opt) => (
        <label key={opt.value} className="mode-switch__option">
          <input
            type="radio"
            name="mode"
            checked={mode === opt.value}
            onChange={() => onChange(opt.value)}
          />
          <span>{opt.label}</span>
        </label>
      ))}
    </div>
  );
}

export default ModeSwitch;
