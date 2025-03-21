// import React, { useState, useEffect } from 'react';
// import axios from 'axios';

// const App: React.FC = () => {
//   const [sessionId, setSessionId] = useState<string | null>(null);
//   const [state, setState] = useState<string>('store_info');
//   const [message, setMessage] = useState<string>('');
//   const [userInput, setUserInput] = useState<string>('');
//   const [error, setError] = useState<boolean>(false);
//   const [reportReady, setReportReady] = useState<boolean>(false);
//   const [quickReport, setQuickReport] = useState<any>(null);
//   const [detailedReport, setDetailedReport] = useState<any>(null);

//   useEffect(() => {
//     startSession();
//   }, []);

//   const startSession = async () => {
//     try {
//       const response = await axios.post('http://localhost:5000/api/start_session');
//       setSessionId(response.data.session_id);
//       setState(response.data.state);
//       setMessage(response.data.message);
//     } catch (error) {
//       console.error('Error starting session:', error);
//     }
//   };

//   const handleUserInput = async () => {
//     if (!sessionId || !userInput) return;

//     try {
//       const response = await axios.post('http://localhost:5000/api/message', {
//         session_id: sessionId,
//         message: userInput,
//       });

//       setState(response.data.state);
//       setMessage(response.data.message);
//       setError(response.data.error || false);

//       if (response.data.state === 'report') {
//         checkReportStatus();
//       }

//       setUserInput('');
//     } catch (error) {
//       console.error('Error sending message:', error);
//     }
//   };

//   const checkReportStatus = async () => {
//     if (!sessionId) return;

//     try {
//       const response = await axios.get('http://localhost:5000/api/get_report', {
//         params: { session_id: sessionId },
//       });

//       if (response.data.ready) {
//         setReportReady(true);
//         setQuickReport(response.data.quick_report);
//         setDetailedReport(response.data.detailed_report);
//       }
//     } catch (error) {
//       console.error('Error checking report status:', error);
//     }
//   };

//   const downloadReport = async (type: string) => {
//     if (!sessionId) return;

//     try {
//       const response = await axios.get('http://localhost:5000/api/download_report', {
//         params: { session_id: sessionId, type },
//         responseType: 'blob',
//       });

//       const url = window.URL.createObjectURL(new Blob([response.data]));
//       const link = document.createElement('a');
//       link.href = url;
//       link.setAttribute('download', `security_assessment_${type}.pdf`);
//       document.body.appendChild(link);
//       link.click();
//     } catch (error) {
//       console.error('Error downloading report:', error);
//     }
//   };

//   return (
//     <div className="App">
//       <h1>Security Risk Assessment</h1>
//       <div className="chat-container">
//         <div className="message">{message}</div>
//         {state !== 'report' && (
//           <div className="input-container">
//             <input
//               type="text"
//               value={userInput}
//               onChange={(e) => setUserInput(e.target.value)}
//               onKeyPress={(e) => e.key === 'Enter' && handleUserInput()}
//             />
//             <button onClick={handleUserInput}>Send</button>
//           </div>
//         )}
//         {error && <div className="error">Please answer with Y or N</div>}
//       </div>
//       {reportReady && (
//         <div className="report-container">
//           <h2>Reports</h2>
//           <div className="quick-report">
//             <h3>Quick Report</h3>
//             <p>{quickReport.risk_summary}</p>
//             <button onClick={() => downloadReport('quick')}>Download Quick Report</button>
//           </div>
//           <div className="detailed-report">
//             <h3>Detailed Report</h3>
//             <button onClick={() => downloadReport('detailed')}>Download Detailed Report</button>
//           </div>
//         </div>
//       )}
//     </div>
//   );
// };

// export default App;

// import React, { useState, useEffect, useRef } from 'react';
// import axios from 'axios';
// import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, Legend } from 'recharts';

// const App: React.FC = () => {
//   const [sessionId, setSessionId] = useState<string | null>(null);
//   const [state, setState] = useState<string>('store_info');
//   const [messages, setMessages] = useState<Array<{ type: 'bot' | 'user'; text: string }>>([]);
//   const [userInput, setUserInput] = useState<string>('');
//   const [error, setError] = useState<boolean>(false);
//   const [reportReady, setReportReady] = useState<boolean>(false);
//   const [quickReport, setQuickReport] = useState<any>(null);
//   const [detailedReport, setDetailedReport] = useState<any>(null);
//   const [riskData, setRiskData] = useState<Array<{ name: string; value: number }>>([]);
//   const [surveyData, setSurveyData] = useState<Array<{ question: string; answer: string }>>([]);

//   const chatContainerRef = useRef<HTMLDivElement>(null);

//   useEffect(() => {
//     startSession();
//   }, []);

//   useEffect(() => {
//     if (chatContainerRef.current) {
//       chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
//     }
//   }, [messages]);

//   const startSession = async () => {
//     try {
//       const response = await axios.post('http://localhost:5000/api/start_session');
//       setSessionId(response.data.session_id);
//       setState(response.data.state);
//       addBotMessage(response.data.message);
//     } catch (error) {
//       console.error('Error starting session:', error);
//     }
//   };

//   const addBotMessage = (text: string) => {
//     setMessages((prev) => [...prev, { type: 'bot', text }]);
//   };

//   const addUserMessage = (text: string) => {
//     setMessages((prev) => [...prev, { type: 'user', text }]);
//   };

//   const handleUserInput = async () => {
//     if (!sessionId || !userInput) return;

//     addUserMessage(userInput);

//     try {
//       const response = await axios.post('http://localhost:5000/api/message', {
//         session_id: sessionId,
//         message: userInput,
//       });

//       setState(response.data.state);
//       addBotMessage(response.data.message);
//       setError(response.data.error || false);

//       if (response.data.state === 'report') {
//         checkReportStatus();
//       }

//       setUserInput('');
//     } catch (error) {
//       console.error('Error sending message:', error);
//     }
//   };

//   const checkReportStatus = async () => {
//     if (!sessionId) return;

//     try {
//       const response = await axios.get('http://localhost:5000/api/get_report', {
//         params: { session_id: sessionId },
//       });

//       if (response.data.ready) {
//         setReportReady(true);
//         setQuickReport(response.data.quick_report);
//         setDetailedReport(response.data.detailed_report);

//         // Prepare data for visualizations
//         const risks = response.data.detailed_report.identified_risks;
//         const riskCounts = risks.reduce((acc: any, risk: any) => {
//           acc[risk.risk_type] = (acc[risk.risk_type] || 0) + 1;
//           return acc;
//         }, {});

//         const riskChartData = Object.keys(riskCounts).map((key) => ({
//           name: key,
//           value: riskCounts[key],
//         }));

//         setRiskData(riskChartData);

//         // Prepare survey data for visualization
//         const surveyResponses = Object.entries(response.data.detailed_report.answers).map(([question, answer]) => ({
//           question,
//           answer: answer as string,
//         }));

//         setSurveyData(surveyResponses);
//       }
//     } catch (error) {
//       console.error('Error checking report status:', error);
//     }
//   };

//   const downloadReport = async (type: string) => {
//     if (!sessionId) return;

//     try {
//       const response = await axios.get('http://localhost:5000/api/download_report', {
//         params: { session_id: sessionId, type },
//         responseType: 'blob',
//       });

//       const url = window.URL.createObjectURL(new Blob([response.data]));
//       const link = document.createElement('a');
//       link.href = url;
//       link.setAttribute('download', `security_assessment_${type}.pdf`);
//       document.body.appendChild(link);
//       link.click();
//     } catch (error) {
//       console.error('Error downloading report:', error);
//     }
//   };

//   return (
//     <div className="App">
//       <h1>Security Risk Assessment</h1>
//       <div className="chat-container" ref={chatContainerRef}>
//         {messages.map((msg, index) => (
//           <div key={index} className={`message ${msg.type}`}>
//             {msg.text}
//           </div>
//         ))}
//       </div>
//       {state !== 'report' && (
//         <div className="input-container">
//           <input
//             type="text"
//             value={userInput}
//             onChange={(e) => setUserInput(e.target.value)}
//             onKeyPress={(e) => e.key === 'Enter' && handleUserInput()}
//             placeholder="Type your answer here..."
//           />
//           <button onClick={handleUserInput}>Send</button>
//         </div>
//       )}
//       {error && <div className="error">Please answer with Y or N</div>}
//       {reportReady && (
//         <div className="report-container">
//           <h2>Reports</h2>
//           <div className="quick-report">
//             <h3>Quick Report</h3>
//             <p>{quickReport.risk_summary}</p>
//             <button onClick={() => downloadReport('quick')}>Download Quick Report</button>
//           </div>
//           <div className="detailed-report">
//             <h3>Detailed Report</h3>
//             <button onClick={() => downloadReport('detailed')}>Download Detailed Report</button>
//           </div>
//           <div className="visualizations">
//             <h3>Risk Analysis</h3>
//             <PieChart width={400} height={400}>
//               <Pie
//                 data={riskData}
//                 cx={200}
//                 cy={200}
//                 labelLine={false}
//                 label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
//                 outerRadius={80}
//                 fill="#8884d8"
//                 dataKey="value"
//               >
//                 {riskData.map((entry, index) => (
//                   <Cell key={`cell-${index}`} fill={`#${Math.floor(Math.random() * 16777215).toString(16)}`} />
//                 ))}
//               </Pie>
//               <Tooltip />
//               <Legend />
//             </PieChart>
//             <h3>Survey Responses</h3>
//             <BarChart width={600} height={300} data={surveyData}>
//               <XAxis dataKey="question" />
//               <YAxis />
//               <Tooltip />
//               <Legend />
//               <Bar dataKey="answer" fill="#8884d8" />
//             </BarChart>
//           </div>
//         </div>
//       )}
//     </div>
//   );
// };

// export default App;

import React from 'react';
import './App.css';
import SecurityAssessment from './components/Security';

function App() {
  return (
    <div className="App">
      <SecurityAssessment />
    </div>
  );
}
export default App;