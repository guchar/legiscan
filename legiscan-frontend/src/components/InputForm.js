// src/components/InputForm.js
import React, { useState } from "react";
import axios from "axios";

const InputForm = ({ setData }) => {
  const [url, setUrl] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post("http://127.0.0.1:5000/process", {
        url,
      });
      setData(response.data);
    } catch (error) {
      console.error("Error fetching data:", error);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="text"
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        placeholder="Enter GovTrack URL"
      />
      <button type="submit">Submit</button>
    </form>
  );
};

export default InputForm;
