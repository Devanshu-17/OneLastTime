import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import App from './App';
// import Output from './output';
import MedicalChatbot from './MedicalChatbot'; // Adjust the path as necessary
import "./css/App.css";
// import "./css/med.css";
import "./css/upload.css";
import "./css/output.css";
import DoctorReviewDashboard from './DoctorReviewDashboard';


const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <Router>
      <Routes>
        <Route path="/" element={<App />} />
        <Route path="/chat" element={<MedicalChatbot />} />
        <Route path="/doctor-review-dashboard" element={<DoctorReviewDashboard />} />
      </Routes>
    </Router>
  </React.StrictMode>
);
