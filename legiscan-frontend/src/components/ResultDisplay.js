// src/components/ResultDisplay.js
import React from "react";

const ResultDisplay = ({ data }) => {
  if (!data) return null;

  return (
    <div>
      <h1>{data.title}</h1>
      <p>{data.summary}</p>
      <h2>Vote Visualization</h2>
      <img
        src={`http://127.0.0.1:5000/static/vote_visualization.png`}
        alt="Vote Visualization"
      />
      <h2>Timeline</h2>
      <img src={`http://127.0.0.1:5000/static/timeline.png`} alt="Timeline" />
    </div>
  );
};

export default ResultDisplay;
