import React, { useState } from "react";
import axios from "axios";
import "./App.css";

function App() {
  const [url, setUrl] = useState("");
  const [billData, setBillData] = useState(null);
  const [question, setQuestion] = useState("");
  const [chatHistory, setChatHistory] = useState([]);
  const [isScanning, setIsScanning] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsScanning(true);
    try {
      const response = await axios.post("http://localhost:5000/process", {
        url,
      });
      setBillData(response.data);
      setChatHistory([]);
    } catch (error) {
      console.error("Error processing URL:", error);
    } finally {
      setIsScanning(false);
    }
  };

  const handleQuestion = async (e) => {
    e.preventDefault();
    if (!question.trim()) return;

    const newQuestion = { type: "question", text: question };
    setChatHistory((prev) => [...prev, newQuestion]);
    setQuestion("");

    try {
      const response = await axios.post("http://localhost:5000/ask", {
        question: newQuestion.text,
        context: billData.full_text, // Make sure you're sending the full text
      });
      setChatHistory((prev) => [
        ...prev,
        { type: "answer", text: response.data.answer },
      ]);
    } catch (error) {
      console.error("Error asking question:", error);
      setChatHistory((prev) => [
        ...prev,
        { type: "answer", text: "Sorry, I couldn't process that question." },
      ]);
    }
  };

  return (
    <div className="App">
      <header>
        <h1>LegiScan</h1>
        <p>Bringing sense back to politics</p>
      </header>

      <form onSubmit={handleSubmit} className="url-form">
        <input
          type="text"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="Enter GovTrack URL..."
        />
        <button type="submit" disabled={isScanning}>
          {isScanning ? "Scanning..." : "Scan"}
        </button>
      </form>

      {billData && (
        <div className="content">
          <div className="summary">
            <h2>{billData.title}</h2>
            <h3>Summary</h3>
            <p>{billData.summary}</p>
          </div>
          <div className="chat">
            <div className="chat-box">
              {chatHistory.map((item, index) => (
                <div key={index} className={`chat-message ${item.type}`}>
                  {item.text}
                </div>
              ))}
            </div>
            <form onSubmit={handleQuestion}>
              <input
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Ask a follow-up..."
              />
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
