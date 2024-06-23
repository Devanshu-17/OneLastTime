import React, { useEffect, useState } from "react";
import "./css/doc.css";
import Navbar from "./Navbar_upload.js";
import previewBg from "./images/preview/Bug_Loader.gif";

function DoctorReviewDashboard() {
  const [queries, setQueries] = useState([]);
  const [selectedQuery, setSelectedQuery] = useState(null);
  const [notificationVisible, setNotificationVisible] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const response = await fetch("http://localhost:8000/get_user_queries");
      const data = await response.json();
      setQueries(data);
    } catch (error) {
      console.error("Error fetching data:", error);
    }
  };

  const displayDetails = (item) => {
    setSelectedQuery(item);
  };

  const handleAccept = async () => {
    if (!selectedQuery) return;
    try {
      await fetch(`http://localhost:8000/update_status`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          id: selectedQuery._id,
          status: "accepted",
        }),
      });
      alert("Response accepted and saved");
      showNotification();
      resetView();
    } catch (error) {
      console.error("Error updating status:", error);
    }
  };

  const handleReject = async () => {
    if (!selectedQuery) return;
    const feedback = prompt("Please provide your feedback for rejection:");
    if (feedback) {
      try {
        await fetch(`http://localhost:8000/update_status`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            id: selectedQuery._id,
            status: "rejected",
            response: feedback,
          }),
        });
        alert("Response rejected and feedback sent");
        showNotification();
        resetView();
      } catch (error) {
        console.error("Error updating status:", error);
      }
    }
  };

  const showNotification = () => {
    setNotificationVisible(true);
    setTimeout(() => {
      setNotificationVisible(false);
    }, 3000);
  };

  const resetView = () => {
    setSelectedQuery(null);
    fetchData();
  };

  return (
    <div className="mainmed">
      <Navbar />
      <img
        src={previewBg}
        style={{
          position: "fixed",
          top: "-400px",
          width: "100%",
          height: "auto",
          zIndex:"-100",
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          opacity: "0.1",
        }}
      />
      <div className="bodydoc">
        <div className="sidebar">
          {queries.map((item) => (
            <div
              key={item._id}
              className={`doc-query-item ${
                selectedQuery && selectedQuery._id === item._id ? "active" : ""
              }`}
              onClick={() => displayDetails(item)}
            >
              {item.question}
            </div>
          ))}
        </div>

        <div className="doc-main-content">
          <h2>
            {selectedQuery
              ? `Question: ${selectedQuery.question}`
              : "Select a query from the left to view details"}
          </h2>
          {selectedQuery && (
            <>
              <p>Email: {selectedQuery.email}</p>
              <p>Status: {selectedQuery.status}</p>
              <p>Response: {selectedQuery.response}</p>
              <div className="doc-buttons">
                <button className="accept" onClick={handleAccept}>
                  Accept
                </button>
                <button className="reject" onClick={handleReject}>
                  Reject
                </button>
              </div>
            </>
          )}
          {notificationVisible && (
            <div className="notification">
              Action completed successfully!
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default DoctorReviewDashboard;