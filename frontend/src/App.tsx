import React, { useState, useEffect } from 'react';
import axios from 'axios';

const App: React.FC = () => {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [state, setState] = useState<string>('store_info');
  const [message, setMessage] = useState<string>('');
  const [userInput, setUserInput] = useState<string>('');
  const [error, setError] = useState<boolean>(false);
  const [reportReady, setReportReady] = useState<boolean>(false);
  const [quickReport, setQuickReport] = useState<any>(null);
  const [detailedReport, setDetailedReport] = useState<any>(null);

  useEffect(() => {
    startSession();
  }, []);

  const startSession = async () => {
    try {
      const response = await axios.post('http://localhost:5000/api/start_session');
      setSessionId(response.data.session_id);
      setState(response.data.state);
      setMessage(response.data.message);
    } catch (error) {
      console.error('Error starting session:', error);
    }
  };

  const handleUserInput = async () => {
    if (!sessionId || !userInput) return;

    try {
      const response = await axios.post('http://localhost:5000/api/message', {
        session_id: sessionId,
        message: userInput,
      });

      setState(response.data.state);
      setMessage(response.data.message);
      setError(response.data.error || false);

      if (response.data.state === 'report') {
        checkReportStatus();
      }

      setUserInput('');
    } catch (error) {
      console.error('Error sending message:', error);
    }
  };

  const checkReportStatus = async () => {
    if (!sessionId) return;

    try {
      const response = await axios.get('http://localhost:5000/api/get_report', {
        params: { session_id: sessionId },
      });

      if (response.data.ready) {
        setReportReady(true);
        setQuickReport(response.data.quick_report);
        setDetailedReport(response.data.detailed_report);
      }
    } catch (error) {
      console.error('Error checking report status:', error);
    }
  };

  const downloadReport = async (type: string) => {
    if (!sessionId) return;

    try {
      const response = await axios.get('http://localhost:5000/api/download_report', {
        params: { session_id: sessionId, type },
        responseType: 'blob',
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `security_assessment_${type}.pdf`);
      document.body.appendChild(link);
      link.click();
    } catch (error) {
      console.error('Error downloading report:', error);
    }
  };

  return (
    <div className="App">
      <h1>Security Risk Assessment</h1>
      <div className="chat-container">
        <div className="message">{message}</div>
        {state !== 'report' && (
          <div className="input-container">
            <input
              type="text"
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleUserInput()}
            />
            <button onClick={handleUserInput}>Send</button>
          </div>
        )}
        {error && <div className="error">Please answer with Y or N</div>}
      </div>
      {reportReady && (
        <div className="report-container">
          <h2>Reports</h2>
          <div className="quick-report">
            <h3>Quick Report</h3>
            <p>{quickReport.risk_summary}</p>
            <button onClick={() => downloadReport('quick')}>Download Quick Report</button>
          </div>
          <div className="detailed-report">
            <h3>Detailed Report</h3>
            <button onClick={() => downloadReport('detailed')}>Download Detailed Report</button>
          </div>
        </div>
      )}
    </div>
  );
};

export default App;