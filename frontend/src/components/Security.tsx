import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { AlertTriangle, CheckCircle, Clock, Download, Send, ChevronRight, FileText, PieChart as PieChartIcon, BarChart2 } from 'lucide-react';

// Define the base URL for API requests
const API_BASE_URL = 'http://localhost:5000/api';

// Types for our application
interface Message {
  id: string;
  content: string;
  sender: 'bot' | 'user';
  timestamp: Date;
}

interface Session {
  id: string;
  state: string;
}

interface StoreInfo {
  [key: string]: string;
}

interface RiskReport {
  identified_risks: string[];
  unique_solutions: string[];
  risk_summary: string;
}

interface DetailedReport {
  identified_risks: Array<{
    risk_type: string;
    mitigations: {
      mitigations: {
        tech: string[];
        human: string[];
        tss: string[];
        analytics: string[];
        policy: string[];
      };
      solution_details: {
        [key: string]: {
          use_case: string;
          links: string;
          partners: string;
          data_format: string;
          immediate_actions: string[];
          data_collation: string[];
          dashboard: string[];
          wearable: string[];
          mobile: string[];
          soc: string[];
          audio_visual: string[];
        };
      };
    };
  }>;
}

const SecurityAssessment: React.FC = () => {
  // State management
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(false);
  const [quickReport, setQuickReport] = useState<RiskReport | null>(null);
  const [detailedReport, setDetailedReport] = useState<DetailedReport | null>(null);
  const [showDashboard, setShowDashboard] = useState(false);
  const [activeTab, setActiveTab] = useState('chat');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Initialize the session when component mounts
  useEffect(() => {
    startSession();
  }, []);

  // Scroll to bottom whenever messages updates
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Function to scroll chat to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Start a new session
  const startSession = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/start_session`);
      setSession({
        id: response.data.session_id,
        state: response.data.state
      });
      
      addMessage(response.data.message, 'bot');
    } catch (error) {
      console.error('Error starting session:', error);
      addMessage('Failed to connect to the server. Please try again later.', 'bot');
    } finally {
      setLoading(false);
    }
  };

  // Add a message to the chat
  const addMessage = (content: string, sender: 'bot' | 'user') => {
    const newMessage: Message = {
      id: Date.now().toString(),
      content,
      sender,
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, newMessage]);
  };

  // Handle sending a message
  const handleSendMessage = async () => {
    if (!inputValue.trim() || !session) return;
    
    const userMessage = inputValue;
    setInputValue('');
    addMessage(userMessage, 'user');
    setLoading(true);
    
    try {
      const response = await axios.post(`${API_BASE_URL}/message`, {
        session_id: session.id,
        message: userMessage
      });
      
      // Update session state if it changed
      if (response.data.state !== session.state) {
        setSession({
          ...session,
          state: response.data.state
        });
        
        // If survey is complete, get the report
        if (response.data.state === 'report') {
          fetchReportData();
        }
      }
      
      addMessage(response.data.message, 'bot');
    } catch (error) {
      console.error('Error sending message:', error);
      addMessage('Failed to get a response. Please try again.', 'bot');
    } finally {
      setLoading(false);
    }
  };

  // Fetch report data when survey is complete
  const fetchReportData = async () => {
    if (!session) return;
    
    try {
      const response = await axios.get(`${API_BASE_URL}/get_report`, {
        params: { session_id: session.id }
      });
      
      if (response.data.ready) {
        setQuickReport(response.data.quick_report);
        setDetailedReport(response.data.detailed_report);
        setShowDashboard(true);
        setActiveTab('dashboard');
      }
    } catch (error) {
      console.error('Error fetching report:', error);
      addMessage('Failed to generate the report. Please try again.', 'bot');
    }
  };

  // Download a report
  const downloadReport = async (reportType: 'quick' | 'detailed') => {
    if (!session) return;
    
    try {
      const response = await axios.get(`${API_BASE_URL}/download_report`, {
        params: {
          session_id: session.id,
          type: reportType
        },
        responseType: 'blob'
      });
      
      // Create a download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `security_assessment_${reportType}.pdf`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      addMessage(`Your ${reportType} report has been downloaded.`, 'bot');
    } catch (error) {
      console.error(`Error downloading ${reportType} report:`, error);
      addMessage(`Failed to download the ${reportType} report.`, 'bot');
    }
  };

  // Calculate risk severity based on count
  const getRiskSeverity = (count: number) => {
    if (count === 0) return 'Low';
    if (count <= 2) return 'Medium';
    if (count <= 4) return 'High';
    return 'Critical';
  };

  // Calculate severity color
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'Low': return '#4caf50';
      case 'Medium': return '#ff9800';
      case 'High': return '#f44336';
      case 'Critical': return '#9c27b0';
      default: return '#2196f3';
    }
  };

  // Group risks by category for visualization
  const groupRisksByCategory = () => {
    if (!detailedReport) return [];
    
    const categories: {[key: string]: number} = {
      'Physical Security': 0,
      'Data Security': 0,
      'Personnel Security': 0,
      'Operational Security': 0,
      'Other': 0
    };
    
    detailedReport.identified_risks.forEach(risk => {
      const riskType = risk.risk_type.toLowerCase();
      
      if (riskType.includes('physical') || riskType.includes('theft') || riskType.includes('intrusion')) {
        categories['Physical Security']++;
      } else if (riskType.includes('data') || riskType.includes('information') || riskType.includes('cyber')) {
        categories['Data Security']++;
      } else if (riskType.includes('personnel') || riskType.includes('staff') || riskType.includes('employee')) {
        categories['Personnel Security']++;
      } else if (riskType.includes('operation') || riskType.includes('process')) {
        categories['Operational Security']++;
      } else {
        categories['Other']++;
      }
    });
    
    return Object.keys(categories).map(key => ({
      name: key,
      value: categories[key]
    })).filter(item => item.value > 0);
  };

  // Count mitigation types
  const countMitigationTypes = () => {
    if (!detailedReport) return [];
    
    const counts = {
      Technical: 0,
      Human: 0,
      TSS: 0,
      Analytics: 0,
      Policy: 0
    };
    
    detailedReport.identified_risks.forEach(risk => {
      const mitigations = risk.mitigations.mitigations;
      counts.Technical += mitigations.tech.length;
      counts.Human += mitigations.human.length;
      counts.TSS += mitigations.tss.length;
      counts.Analytics += mitigations.analytics.length;
      counts.Policy += mitigations.policy.length;
    });
    
    return [
      { name: 'Technical', count: counts.Technical },
      { name: 'Human', count: counts.Human },
      { name: 'TSS', count: counts.TSS },
      { name: 'Analytics', count: counts.Analytics },
      { name: 'Policy', count: counts.Policy }
    ].filter(item => item.count > 0);
  };

  // Format a message for display
  const formatMessage = (content: string) => {
    // Replace markdown-style bold with HTML
    let formattedContent = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Handle line breaks
    formattedContent = formattedContent.replace(/\n/g, '<br />');
    
    return <div dangerouslySetInnerHTML={{ __html: formattedContent }} />;
  };

  // Render the chat interface
  const renderChat = () => (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-4 bg-gray-50">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`mb-4 ${
              message.sender === 'bot'
                ? 'flex justify-start'
                : 'flex justify-end'
            }`}
          >
            <div
              className={`rounded-lg px-4 py-2 max-w-xs sm:max-w-md md:max-w-lg ${
                message.sender === 'bot'
                  ? 'bg-white text-gray-800 shadow'
                  : 'bg-blue-600 text-white'
              }`}
            >
              {formatMessage(message.content)}
              <div
                className={`text-xs mt-1 ${
                  message.sender === 'bot' ? 'text-gray-500' : 'text-blue-200'
                }`}
              >
                {message.timestamp.toLocaleTimeString([], {
                  hour: '2-digit',
                  minute: '2-digit'
                })}
              </div>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
      
      <div className="border-t p-4 bg-white">
        <div className="flex items-center">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
            placeholder="Type your message..."
            className="flex-1 border rounded-l-lg py-2 px-4 focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={loading || session?.state === 'report'}
          />
          <button
            onClick={handleSendMessage}
            disabled={loading || !inputValue.trim() || session?.state === 'report'}
            className="bg-blue-600 text-white rounded-r-lg py-2 px-4 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-blue-300"
          >
            {loading ? <Clock className="h-5 w-5 animate-spin" /> : <Send className="h-5 w-5" />}
          </button>
        </div>
      </div>
    </div>
  );

  // Render the dashboard
  const renderDashboard = () => {
    if (!quickReport || !detailedReport) {
      return (
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <Clock className="h-12 w-12 mx-auto text-blue-500 animate-spin" />
            <p className="mt-4 text-lg">Loading report data...</p>
          </div>
        </div>
      );
    }
    
    const riskCount = quickReport.identified_risks.length;
    const severity = getRiskSeverity(riskCount);
    const severityColor = getSeverityColor(severity);
    const riskCategories = groupRisksByCategory();
    const mitigationTypes = countMitigationTypes();
    
    // COLORS for charts
    const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#A174F2'];
    
    return (
      <div className="p-4 overflow-y-auto h-full">
        <h2 className="text-2xl font-bold mb-6">Security Assessment Results</h2>
        
        {/* Risk Summary */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow p-4">
            <h3 className="font-semibold text-gray-600 mb-2">Risk Level</h3>
            <div className="flex items-center">
              <div 
                className="w-16 h-16 rounded-full flex items-center justify-center text-white font-bold text-lg"
                style={{ backgroundColor: severityColor }}
              >
                {severity}
              </div>
              <div className="ml-4">
                <p className="text-3xl font-bold">{riskCount}</p>
                <p className="text-gray-500">Identified Risks</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow p-4">
            <h3 className="font-semibold text-gray-600 mb-2">Solutions Available</h3>
            <div className="flex items-center">
              <CheckCircle className="w-12 h-12 text-green-500" />
              <div className="ml-4">
                <p className="text-3xl font-bold">{quickReport.unique_solutions.length}</p>
                <p className="text-gray-500">Mitigation Solutions</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow p-4">
            <h3 className="font-semibold text-gray-600 mb-2">Reports</h3>
            <div className="flex flex-col space-y-2">
              <button 
                onClick={() => downloadReport('quick')}
                className="flex items-center justify-between bg-blue-50 hover:bg-blue-100 text-blue-700 py-2 px-4 rounded"
              >
                <span>Quick Report</span>
                <Download className="h-4 w-4" />
              </button>
              <button 
                onClick={() => downloadReport('detailed')}
                className="flex items-center justify-between bg-indigo-50 hover:bg-indigo-100 text-indigo-700 py-2 px-4 rounded"
              >
                <span>Detailed Report</span>
                <Download className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
        
        {/* Charts */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          {/* Risk Categories Chart */}
          <div className="bg-white rounded-lg shadow p-4">
            <h3 className="font-semibold text-gray-600 mb-4">Risks by Category</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={riskCategories}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {riskCategories.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
          
          {/* Mitigation Types Chart */}
          <div className="bg-white rounded-lg shadow p-4">
            <h3 className="font-semibold text-gray-600 mb-4">Mitigation Solutions by Type</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={mitigationTypes}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="count" name="Number of Solutions" fill="#8884d8" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
        
        {/* Identified Risks */}
        <div className="bg-white rounded-lg shadow p-4 mb-6">
          <h3 className="font-semibold text-gray-600 mb-4">Identified Risks</h3>
          <div className="space-y-2">
            {quickReport.identified_risks.map((risk, index) => (
              <div key={index} className="flex items-center p-2 bg-red-50 text-red-800 rounded">
                <AlertTriangle className="h-5 w-5 mr-2" />
                <span>{risk}</span>
              </div>
            ))}
            {quickReport.identified_risks.length === 0 && (
              <div className="p-4 text-center text-gray-500">
                No risks identified. Great job!
              </div>
            )}
          </div>
        </div>
        
        {/* Available Solutions */}
        <div className="bg-white rounded-lg shadow p-4">
          <h3 className="font-semibold text-gray-600 mb-4">Available Solutions</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
            {quickReport.unique_solutions.map((solution, index) => (
              <div key={index} className="p-2 bg-green-50 text-green-800 rounded flex items-center">
                <CheckCircle className="h-4 w-4 mr-2 flex-shrink-0" />
                <span className="text-sm">{solution}</span>
              </div>
            ))}
            {quickReport.unique_solutions.length === 0 && (
              <div className="p-4 col-span-3 text-center text-gray-500">
                No solutions available.
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="flex flex-col h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-blue-700 text-white p-4 shadow-md">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-bold">Security Risk Assessment</h1>
          {showDashboard && (
            <div className="flex space-x-2">
              <button 
                onClick={() => setActiveTab('chat')}
                className={`px-3 py-1 rounded text-sm flex items-center ${
                  activeTab === 'chat' ? 'bg-blue-800' : 'hover:bg-blue-600'
                }`}
              >
                <FileText className="h-4 w-4 mr-1" />
                <span>Chat</span>
              </button>
              <button 
                onClick={() => setActiveTab('dashboard')}
                className={`px-3 py-1 rounded text-sm flex items-center ${
                  activeTab === 'dashboard' ? 'bg-blue-800' : 'hover:bg-blue-600'
                }`}
              >
                <BarChart2 className="h-4 w-4 mr-1" />
                <span>Dashboard</span>
              </button>
            </div>
          )}
        </div>
      </header>
      
      {/* Main Content */}
      <main className="flex-1 overflow-hidden">
        {activeTab === 'chat' ? renderChat() : renderDashboard()}
      </main>
      
      {/* Footer */}
      <footer className="bg-gray-100 text-center p-2 text-xs text-gray-500 border-t">
        Security Risk Assessment Tool &copy; 2025 - All rights reserved
      </footer>
    </div>
  );
};

export default SecurityAssessment;