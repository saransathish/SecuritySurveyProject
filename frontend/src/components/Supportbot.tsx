import React, { useState, useRef, useEffect } from 'react';
import { MessageSquare, X, Send, ChevronDown, ChevronUp, Paperclip, Smile } from 'lucide-react';

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
}

const exampleQuestions = [
  "How much does it cost to implement a CCTV solution?",
  "What are the risks present in the absence of static security guards?",
  "What security measures do you recommend for a superstore?",
];

const SupportChatbot: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [inputValue, setInputValue] = useState('');
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      text: "👋 Hello! I'm your security solutions assistant. How can I help you today?",
      sender: 'bot',
      timestamp: new Date()
    }
  ]);
  const [showExamples, setShowExamples] = useState(true);
  const [isTyping, setIsTyping] = useState(false);
  const messageEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isOpen) {
      messageEndRef.current?.scrollIntoView({ behavior: 'smooth' });
      inputRef.current?.focus();
    }
  }, [messages, isOpen]);

  const toggleChat = () => {
    setIsOpen(!isOpen);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputValue,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsTyping(true);
    
    // Simulate bot response after a short delay
    setTimeout(() => {
      setIsTyping(false);
      const botResponse: Message = {
        id: (Date.now() + 1).toString(),
        text: "Thank you for your inquiry. This feature is currently under construction.",
        sender: 'bot',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, botResponse]);
    }, 1500);
  };

  const handleExampleClick = (question: string) => {
    setInputValue(question);
    if (inputRef.current) {
      inputRef.current.focus();
    }
  };

  return (
    <div className="fixed  bottom-10 right-8 z-50 flex flex-col items-end">
      {/* Chat popup */}
      {isOpen && (
        <div className="mb-4 w-80 md:w-96 bg-white rounded-2xl shadow-2xl overflow-hidden flex flex-col border border-gray-100 transform transition-all duration-300 ease-in-out">
          {/* Header */}
          <div className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white p-4 flex justify-between items-center">
            <div className="font-medium flex items-center">
              <div className="bg-white text-indigo-600 p-1 rounded-full mr-3">
                <MessageSquare className="h-5 w-5" />
              </div>
              <div>
                <div className="font-bold">Security Assistant</div>
                <div className="text-xs opacity-80">Online | 24/7 Support</div>
              </div>
            </div>
            <button 
              onClick={toggleChat}
              className="p-1 rounded-full hover:bg-white/20 transition-colors"
              aria-label="Close chat"
            >
              <X size={18} />
            </button>
          </div>
          
          {/* Messages */}
          <div className="flex-1 p-4 overflow-y-auto max-h-96 bg-gray-50">
            {messages.map(message => (
              <div 
                key={message.id} 
                className={`mb-4 flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {message.sender === 'bot' && (
                  <div className="w-8 h-8 rounded-full bg-gradient-to-r from-indigo-600 to-purple-600 flex items-center justify-center text-white text-xs mr-2 flex-shrink-0 mt-1">
                    SA
                  </div>
                )}
                <div
                  className={`p-3 rounded-2xl max-w-[85%] shadow-sm ${
                    message.sender === 'user' 
                      ? 'bg-gradient-to-r from-indigo-500 to-purple-500 text-white rounded-br-none' 
                      : 'bg-white text-gray-800 rounded-bl-none border border-gray-100'
                  }`}
                >
                  {message.text}
                  <div 
                    className={`text-xs mt-1 ${
                      message.sender === 'user' ? 'text-indigo-100' : 'text-gray-500'
                    }`}
                  >
                    {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </div>
                </div>
                {message.sender === 'user' && (
                  <div className="w-8 h-8 rounded-full bg-gradient-to-r from-green-500 to-emerald-500 flex items-center justify-center text-white text-xs ml-2 flex-shrink-0 mt-1">
                    You
                  </div>
                )}
              </div>
            ))}
            
            {/* Typing indicator */}
            {isTyping && (
              <div className="flex items-center mb-4">
                <div className="w-8 h-8 rounded-full bg-gradient-to-r from-indigo-600 to-purple-600 flex items-center justify-center text-white text-xs mr-2 flex-shrink-0">
                  SA
                </div>
                <div className="bg-white text-gray-500 rounded-2xl py-2 px-4 shadow-sm border border-gray-100">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-300 rounded-full animate-bounce" style={{ animationDelay: '0s' }}></div>
                    <div className="w-2 h-2 bg-gray-300 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    <div className="w-2 h-2 bg-gray-300 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messageEndRef} />
            
            {/* Example questions */}
            {showExamples && messages.length < 3 && (
              <div className="mt-4 bg-white rounded-xl border border-gray-100 p-3 shadow-sm">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm font-medium text-gray-700">Suggested questions</span>
                  <button 
                    onClick={() => setShowExamples(!showExamples)}
                    className="text-gray-500 hover:text-gray-700"
                    aria-label={showExamples ? "Hide suggestions" : "Show suggestions"}
                  >
                    {showExamples ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                  </button>
                </div>
                <div className="flex flex-col gap-2">
                  {exampleQuestions.map((question, index) => (
                    <button
                      key={index}
                      className="text-left text-sm py-2 px-3 text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
                      onClick={() => handleExampleClick(question)}
                    >
                      {question}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
          
          {/* Input */}
          <form onSubmit={handleSubmit} className="p-3 border-t border-gray-100 bg-white">
            <div className="flex items-center bg-gray-50 rounded-full p-1 border border-gray-200">
              <button
                type="button"
                className="p-2 text-gray-500 hover:text-indigo-600 transition-colors"
                aria-label="Add attachment"
              >
                <Paperclip size={18} />
              </button>
              
              <input
                ref={inputRef}
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder="Type your message..."
                className="flex-1 p-2 bg-transparent border-none focus:outline-none text-gray-700"
              />
              
              <button
                type="button"
                className="p-2 text-gray-500 hover:text-indigo-600 transition-colors mr-1"
                aria-label="Add emoji"
              >
                <Smile size={18} />
              </button>
              
              <button
                type="submit"
                className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white p-2 rounded-full hover:shadow-md transition-all disabled:opacity-70"
                disabled={!inputValue.trim()}
                aria-label="Send message"
              >
                <Send size={18} />
              </button>
            </div>
          </form>
        </div>
      )}
      
      {/* Chat button with pulsing effect */}
      <button
        onClick={toggleChat}
        className={`p-4 rounded-full shadow-lg transition-all duration-300 relative ${
          isOpen 
            ? 'bg-gradient-to-r from-red-500 to-pink-500 hover:from-red-600 hover:to-pink-600' 
            : 'bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700'
        }`}
        aria-label={isOpen ? "Close chat" : "Open chat"}
      >
        {isOpen ? (
          <X size={24} className="text-white" />
        ) : (
          <>
            <MessageSquare size={24} className="text-white relative z-10" />
            <span className="absolute inset-0 rounded-full bg-indigo-600 animate-ping opacity-75"></span>
          </>
        )}
      </button>
    </div>
  );
};

export default SupportChatbot;