import React, { useState } from 'react';
import "./css/med.css"; 
import Footer from "./Footer.js";
import Navbar from "./Navbar_upload.js";
import previewBg from "./images/preview/Bug_Loader.gif";

function MedicalChatbot() {
    const [question, setQuestion] = useState('');
    const [response, setResponse] = useState('');
    const [loading, setLoading] = useState(false);
    const [errorMessage, setErrorMessage] = useState('');
    const [webInfoAlert, setWebInfoAlert] = useState(false);
    const [email, setEmail] = useState('');

    const handleInputChange = (event) => {
        setQuestion(event.target.value);
    };

    const handleEmailChange = (event) => {
        setEmail(event.target.value);
    };

    const submitQuestion = async (event) => {
        event.preventDefault();
        setLoading(true);
        setResponse('');
        setErrorMessage('');
        setWebInfoAlert(false);

        try {
            const initialResponse = await fetch('http://localhost:8000/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ question }),
            });

            if (!initialResponse.ok) {
                throw new Error('Network response was not ok');
            }

            const data = await initialResponse.json();

            if (data.response.includes("**Information found on the web")) {
                setWebInfoAlert(true);
                setResponse(data.response.replace("**Information found on the web", ""));
            } else {
                setResponse(data.response);
            }
        } catch (error) {
            console.error('Fetch Error:', error);
            setErrorMessage(error.message || 'Error: Unable to fetch response.');
        } finally {
            setLoading(false);
        }
    };

    const saveToDatabase = async (event) => {
        event.preventDefault();
        try {
            const response = await fetch('http://localhost:8000/save_query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email, question }),
            });

            if (!response.ok) {
                throw new Error('Failed to save query');
            }

            alert('Query saved successfully!');
        } catch (error) {
            console.error('Save Error:', error);
            alert('Failed to save query. Please try again.');
        }
    };

    return (
        <div className='docmain'>
            <Navbar/>
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

            <section className="container">
                <h1 id="med-h1">Medical Chatbot</h1>
                <form onSubmit={submitQuestion}>
                    <div className="med-form-group">
                        <label id="med-label" htmlFor="question">Enter your medical question:</label>
                        <textarea id="question" rows="4" value={question} onChange={handleInputChange}></textarea>
                    </div>
                    <button id="med-but" type="submit" disabled={loading}>
                        {loading ? 'Loading...' : 'Submit'}
                    </button>
                </form>
                
                {response && (
                    <div className="response">
                        <strong>Response:</strong> <span dangerouslySetInnerHTML={{ __html: response }}></span>
                    </div>
                )}
                {webInfoAlert && (
                    <div>
                        <div className="alert alert-danger" role="alert">
                            🚨  Alert: Information found on the web. Please wait for a response from a medical professional.
                        </div>
                        <form class="save-query" onSubmit={saveToDatabase}>
                            <div className="med-form-group">
                                <label id="med-label" htmlFor="email">Enter your email address:</label>
                                <input type="email" id="email" value={email} onChange={handleEmailChange} required />
                            </div>
                            <button id="med-but-final" type="submit">Save Query</button>
                        </form>
                    </div>
                )}
                {errorMessage && (
                    <div className="alert alert-danger" role="alert">
                        <strong>Error!</strong> {errorMessage}
                    </div>
                )}
                
            </section>
            <br/><br/><br/>
            <Footer/>
        </div>
    );
}

export default MedicalChatbot;