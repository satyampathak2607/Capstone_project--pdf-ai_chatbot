import React, { useState } from "react";
import axios from "axios";
import "./App.css";

function App() {
  const [pdfFile, setPdfFile] = useState(null);
  const [status, setStatus] = useState("");
  const [question, setQuestion] = useState("");
  const [chatHistory, setChatHistory] = useState([]);
  const [deviceStatus, setDeviceStatus] = useState(null);

React.useEffect(() => {
  axios.get("http://localhost:8000/status")
    .then((res) => setDeviceStatus(res.data))
    .catch((err) => console.error("Failed to fetch device status:", err));
}, []);


  const handleUpload = async () => {
    if (!pdfFile) return;
    const formData = new FormData();
    formData.append("file", pdfFile);

    setStatus("Uploading PDF...");
    try {
      await axios.post("http://localhost:8000/upload", formData);
      setStatus("Summarizing...");
      await axios.post("http://localhost:8000/summarize");
      setStatus("Ready to chat!");
    } catch (err) {
      setStatus("Upload or Summarization Failed");
    }
  };

  const handleAsk = async () => {
    if (!question.trim()) return;
    setChatHistory([...chatHistory, { question, answer: "..." }]);

    try {
      const res = await axios.post("http://localhost:8000/chat", { question });
      setChatHistory((prev) => {
        const updated = [...prev];
        updated[updated.length - 1].answer = res.data.answer;
        return updated;
      });
      setQuestion("");
    } catch (err) {
      setStatus("Error getting answer");
    }
  };

  return (
  <div className="container">
    <h1>PDF-AI Chatbot</h1>

    {deviceStatus && (
      <div
        style={{
          backgroundColor: deviceStatus.device === "GPU" ? "#d2f8d2" : "#ffe0e0",
          padding: "8px",
          borderRadius: "5px",
          marginBottom: "12px",
          fontWeight: "bold"
        }}
      >
        {deviceStatus.device === "GPU"
          ? `⚡ Using GPU: ${deviceStatus.gpu_name}`
          : `⚠️ Using CPU: ${deviceStatus.gpu_name}`}
      </div>
    )}

    <input type="file" accept=".pdf" onChange={(e) => setPdfFile(e.target.files[0])} />
    <button onClick={handleUpload}>Upload & Summarize</button>
    <p className="status">{status}</p>

    <div className="chat-box">
      {chatHistory.map((chat, idx) => (
        <div key={idx} className="chat-item">
          <p><strong>Q:</strong> {chat.question}</p>
          <p><strong>A:</strong> {chat.answer}</p>
        </div>
      ))}
    </div>

    <div className="chat-input">
      <input
        type="text"
        placeholder="Ask a question..."
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
      />
      <button onClick={handleAsk}>Ask</button>
    </div>
  </div>
    
  );
}

export default App;
