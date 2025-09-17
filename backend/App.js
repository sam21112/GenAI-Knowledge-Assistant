// frontend/src/App.js
import React, { useState } from 'react';
import axios from 'axios';

function App() {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [caption, setCaption] = useState('');
  const [loading, setLoading] = useState(false);
  const [fileName, setFileName] = useState('');

  const askQuestion = async () => {
    setLoading(true);
    const form = new FormData();
    form.append('prompt', question);
    try {
      const res = await axios.post('http://localhost:8000/text-query', form);
      setAnswer(res.data.answer);
    } catch (e) {
      alert('Error asking question');
    }
    setLoading(false);
  };

  const uploadFile = async (file, type) => {
    const form = new FormData();
    form.append('file', file);
    const endpoint =
      type === 'pdf' ? 'upload-doc' : 'upload-image';
    setLoading(true);
    try {
      const res = await axios.post(`http://localhost:8000/${endpoint}`, form);
      if (res.data.caption) setCaption(res.data.caption);
      if (res.data.filename) setFileName(res.data.filename);
    } catch (e) {
      alert('Upload failed');
    }
    setLoading(false);
  };

  return (
    <div style={{ padding: 40, fontFamily: 'sans-serif' }}>
      <h1>🧠 GenAI Knowledge Assistant</h1>

      <div style={{ marginBottom: 20 }}>
        <textarea
          rows={4}
          cols={60}
          value={question}
          placeholder="Ask me a question..."
          onChange={(e) => setQuestion(e.target.value)}
        />
        <br />
        <button onClick={askQuestion} disabled={loading}>
          {loading ? 'Loading...' : 'Ask'}
        </button>
        {answer && (
          <div style={{ marginTop: 20 }}>
            <strong>Answer:</strong>
            <p>{answer}</p>
          </div>
        )}
      </div>

      <div style={{ marginBottom: 20 }}>
        <h3>📄 Upload PDF</h3>
        <input
          type="file"
          accept="application/pdf"
          onChange={(e) => uploadFile(e.target.files[0], 'pdf')}
        />
        {fileName && <p>Uploaded: {fileName}</p>}
      </div>

      <div style={{ marginBottom: 20 }}>
        <h3>🖼️ Upload Image</h3>
        <input
          type="file"
          accept="image/*"
          onChange={(e) => uploadFile(e.target.files[0], 'image')}
        />
        {caption && (
          <div>
            <strong>Caption:</strong> <p>{caption}</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
