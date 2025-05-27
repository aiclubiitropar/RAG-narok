import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';

// Avatar component for user and bot
const Avatar = ({ sender }) => (
  <div style={{
    width: 36,
    height: 36,
    borderRadius: '50%',
    background: sender === 'user' ? 'linear-gradient(135deg, #1976d2 60%, #42a5f5 100%)' : 'linear-gradient(135deg, #263238 60%, #90caf9 100%)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 18,
    marginRight: 12,
    boxShadow: '0 2px 8px rgba(0,0,0,0.15)'
  }}>
    {sender === 'user' ? 'U' : 'B'}
  </div>
);

// Message bubble with animation
const MessageBubble = ({ sender, text, time }) => (
  <div style={{
    display: 'flex',
    flexDirection: sender === 'user' ? 'row-reverse' : 'row',
    alignItems: 'flex-end',
    marginBottom: 18,
    animation: 'fadeIn 0.4s',
  }}>
    <Avatar sender={sender} />
    <div style={{
      background: sender === 'user' ? 'linear-gradient(135deg, #1976d2 60%, #42a5f5 100%)' : 'linear-gradient(135deg, #23272f 60%, #263238 100%)',
      color: '#fff',
      borderRadius: 16,
      padding: '12px 18px',
      maxWidth: 420,
      fontSize: 16,
      boxShadow: sender === 'user' ? '0 2px 8px #1976d2aa' : '0 2px 8px #23272faa',
      marginLeft: sender === 'user' ? 0 : 8,
      marginRight: sender === 'user' ? 8 : 0,
      position: 'relative',
      wordBreak: 'break-word',
      borderTopRightRadius: sender === 'user' ? 4 : 16,
      borderTopLeftRadius: sender === 'user' ? 16 : 4,
      transition: 'background 0.2s',
    }}>
      {text}
      <div style={{ fontSize: 11, color: '#90caf9', marginTop: 6, textAlign: sender === 'user' ? 'right' : 'left' }}>{time}</div>
    </div>
  </div>
);

// Typing indicator
const TypingIndicator = () => (
  <div style={{ display: 'flex', alignItems: 'center', marginBottom: 18, marginLeft: 48 }}>
    <div style={{
      background: 'linear-gradient(135deg, #23272f 60%, #263238 100%)',
      borderRadius: 16,
      padding: '12px 18px',
      color: '#90caf9',
      fontSize: 16,
      display: 'flex',
      alignItems: 'center',
      minWidth: 60,
    }}>
      <span className="dot" style={{ animation: 'blink 1s infinite', marginRight: 2 }}>●</span>
      <span className="dot" style={{ animation: 'blink 1s 0.2s infinite', marginRight: 2 }}>●</span>
      <span className="dot" style={{ animation: 'blink 1s 0.4s infinite' }}>●</span>
    </div>
  </div>
);

// Scroll to bottom button
const ScrollToBottom = ({ onClick, visible }) => (
  visible ? (
    <button onClick={onClick} style={{
      position: 'absolute',
      right: 24,
      bottom: 100,
      background: 'linear-gradient(135deg, #1976d2 60%, #42a5f5 100%)',
      color: '#fff',
      border: 'none',
      borderRadius: 20,
      padding: '8px 18px',
      fontWeight: 600,
      cursor: 'pointer',
      boxShadow: '0 2px 8px #1976d2aa',
      zIndex: 10,
      fontSize: 15
    }}>↓ New</button>
  ) : null
);

// Main Chat UI
function CHATUI() {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState([]);
  const [isTyping, setIsTyping] = useState(false);
  const [showScroll, setShowScroll] = useState(false);
  const navigate = useNavigate();
  const messagesEndRef = useRef(null);
  const chatRef = useRef(null);

  // Scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Show scroll-to-bottom button if not at bottom
  useEffect(() => {
    const handleScroll = () => {
      if (!chatRef.current) return;
      const { scrollTop, scrollHeight, clientHeight } = chatRef.current;
      setShowScroll(scrollHeight - scrollTop - clientHeight > 60);
    };
    const chatDiv = chatRef.current;
    if (chatDiv) chatDiv.addEventListener('scroll', handleScroll);
    return () => chatDiv && chatDiv.removeEventListener('scroll', handleScroll);
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  // Format time
  const getTime = () => {
    const d = new Date();
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  // Handle send
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    const userMessage = { sender: 'user', text: query, time: getTime() };
    setMessages((prev) => [...prev, userMessage]);
    setQuery('');
    setIsTyping(true);
    try {
      const res = await fetch('http://localhost:5000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
      });
      const data = await res.json();
      // Only use the actual response string, not the whole dictionary
      const botMessage = { sender: 'bot', text: typeof data === 'string' ? data : data.response, time: getTime() };
      setMessages((prev) => [...prev, botMessage]);
    } catch {
      setMessages((prev) => [...prev, { sender: 'bot', text: 'Error: Unable to fetch response.', time: getTime() }]);
    } finally {
      setIsTyping(false);
    }
  };

  // Admin click
  const handleAdminClick = () => navigate('/admin-login');

  // File upload (for advanced chatbot UIs)
  const handleFileUpload = (e) => {
    // Placeholder for file upload logic
    alert('File upload is not implemented in this demo.');
  };

  // Main container style
  const containerStyle = {
    display: 'flex',
    flexDirection: 'column',
    height: '100vh',
    background: 'linear-gradient(135deg, #0d1117 60%, #1976d2 100%)',
    color: '#fff',
    fontFamily: 'Inter, Roboto, Arial, sans-serif',
    position: 'relative',
  };

  // Header style
  const headerStyle = {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '18px 32px 12px 32px',
    background: 'rgba(25, 118, 210, 0.95)',
    color: '#fff',
    borderBottom: '1px solid #263238',
    fontWeight: 700,
    fontSize: 22,
    letterSpacing: 1,
    zIndex: 2,
  };

  // Chat area style
  const chatMessagesStyle = {
    flex: 1,
    overflowY: 'auto',
    padding: '32px 0 16px 0',
    background: 'transparent',
    position: 'relative',
    width: '100%',
    maxWidth: 700,
    margin: '0 auto',
    display: 'flex',
    flexDirection: 'column',
  };

  // Input area style
  const chatFormStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: 12,
    padding: '18px 32px',
    background: 'rgba(25, 118, 210, 0.95)',
    borderTop: '1px solid #263238',
    zIndex: 2,
  };

  const inputStyle = {
    flex: 1,
    padding: '12px 16px',
    border: 'none',
    borderRadius: 20,
    fontSize: 16,
    background: '#23272f',
    color: '#fff',
    outline: 'none',
    boxShadow: '0 2px 8px #1976d2aa',
  };

  const buttonStyle = {
    padding: '10px 22px',
    background: 'linear-gradient(135deg, #1976d2 60%, #42a5f5 100%)',
    color: '#fff',
    border: 'none',
    borderRadius: 20,
    fontWeight: 600,
    fontSize: 16,
    cursor: 'pointer',
    boxShadow: '0 2px 8px #1976d2aa',
    transition: 'background 0.2s',
  };

  const iconButtonStyle = {
    ...buttonStyle,
    padding: '10px 14px',
    fontSize: 18,
    borderRadius: '50%',
    minWidth: 0,
    marginLeft: 6,
  };

  return (
    <div style={containerStyle}>
      <header style={headerStyle}>
        <span style={{ letterSpacing: 2 }}>RAGnarok Chat</span>
        <div>
          <button style={buttonStyle} onClick={handleAdminClick}>Admin</button>
        </div>
      </header>
      <div style={chatMessagesStyle} ref={chatRef}>
        {messages.map((msg, idx) => (
          <MessageBubble key={idx} sender={msg.sender} text={msg.text} time={msg.time} />
        ))}
        {isTyping && <TypingIndicator />}
        <div ref={messagesEndRef} />
        <ScrollToBottom onClick={scrollToBottom} visible={showScroll} />
      </div>
      <form onSubmit={handleSubmit} style={chatFormStyle}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Type your message..."
          style={inputStyle}
          autoFocus
        />
        <button type="submit" style={iconButtonStyle} title="Send">➤</button>
        <button type="button" style={iconButtonStyle} title="Upload file" onClick={handleFileUpload}>📎</button>
      </form>
      {/* Animations for dots */}
      <style>{`
        @keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: none; } }
        @keyframes blink { 0%, 80%, 100% { opacity: 0.2; } 40% { opacity: 1; } }
      `}</style>
    </div>
  );
}

export default CHATUI;
