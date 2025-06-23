import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { FaChevronDown, FaChevronRight } from 'react-icons/fa';
import RAGnarokLogo from './RAG_logo.png';

// Inline styles for the chatbot UI
const styles = {
  container: {
    width: '90vw', // Slightly smaller than full width
    maxWidth: 1600, // Cap the width for large screens
    minWidth: 320,
    margin: '40px auto', // Center horizontally
    borderRadius: 24, // Rounded corners
    boxShadow: '0 8px 32px rgba(0,0,0,0.18)', // Soft shadow
    background: 'linear-gradient(135deg, #f8fafc 60%, #e0e7ef 100%)',
    overflow: 'hidden',
    display: 'flex',
    flexDirection: 'column',
    minHeight: 600,
    border: '1.5px solid #e5e7eb', // Slightly thicker border
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    background: 'linear-gradient(90deg, #1e293b 60%, #334155 100%)',
    color: '#fff',
    padding: '0.7rem 1.5rem',
    fontWeight: 600,
    fontSize: 18,
    borderBottom: '1px solid #334155',
  },
  headerLeft: { fontWeight: 700, letterSpacing: 1 },
  headerCenter: {
    display: 'flex', alignItems: 'center', gap: 10
  },
  logo: {
    width: 38, height: 38, borderRadius: '50%', background: '#fff', objectFit: 'cover', boxShadow: '0 2px 8px #0001',
  },
  title: {
    fontWeight: 800, fontSize: 22, letterSpacing: 1, color: '#facc15', marginLeft: 6
  },
  headerRight: {
    display: 'flex', alignItems: 'center', gap: 12
  },
  adminButton: {
    background: 'linear-gradient(90deg, #facc15 60%, #fbbf24 100%)',
    color: '#1e293b',
    border: 'none',
    borderRadius: 8,
    padding: '6px 16px',
    fontWeight: 700,
    cursor: 'pointer',
    fontSize: 15,
    boxShadow: '0 2px 8px #facc1533',
    transition: 'background 0.2s',
  },
  adminFloating: {
    position: 'absolute',
    top: 18,
    right: 32,
    zIndex: 10,
    background: 'linear-gradient(90deg, #facc15 60%, #fbbf24 100%)',
    color: '#1e293b',
    border: 'none',
    borderRadius: 8,
    padding: '8px 20px',
    fontWeight: 700,
    fontSize: 16,
    boxShadow: '0 2px 8px #facc1533',
    transition: 'background 0.2s',
    cursor: 'pointer',
  },
  chatArea: {
    flex: 1,
    padding: '1.2rem',
    overflowY: 'auto',
    background: 'linear-gradient(135deg,rgb(237, 237, 237) 80%,rgba(203, 208, 213, 0.92) 100%)',
    display: 'flex', flexDirection: 'column', gap: 12,
  },
  message: {
    maxWidth: '80%',
    padding: '0.7rem 1.1rem',
    borderRadius: 16,
    fontSize: 16,
    marginBottom: 2,
    boxShadow: '0 2px 8px #0001',
    wordBreak: 'break-word',
    lineHeight: 1.5,
    display: 'inline-block',
    animation: 'fadeIn 0.2s',
  },
  botMessage: {
    background: 'linear-gradient(90deg, #e0e7ef 60%, #f8fafc 100%)',
    color: '#1e293b',
    alignSelf: 'flex-start',
    borderTopLeftRadius: 4,
  },
  userMessage: {
    background: 'linear-gradient(90deg, #facc15 60%, #fbbf24 100%)',
    color: '#1e293b',
    alignSelf: 'flex-end',
    borderTopRightRadius: 4,
  },
  reasoningBox: {
    background: 'rgba(30, 41, 59, 0.8)',
    borderLeft: '3px solid #1e293b',
    padding: '0.5rem 0.9rem',
    borderRadius: 12,
    fontSize: 14,
    marginBottom: 2,
    boxShadow: '0 1px 6px #0001',
    wordBreak: 'break-word',
    lineHeight: 1.4,
    display: 'inline-block',
    animation: 'fadeIn 0.2s',
    color: '#f8fafc',
  },
  inputArea: {
    display: 'flex',
    alignItems: 'center',
    padding: '1rem',
    borderTop: '1px solid #e5e7eb',
    background: '#f8fafc',
    gap: 10,
  },
  input: {
    flex: 1,
    border: '1px solid #e5e7eb',
    borderRadius: 8,
    padding: '0.7rem 1rem',
    fontSize: 16,
    outline: 'none',
    background: '#fff',
    transition: 'border 0.2s',
  },
  sendButton: {
    background: 'linear-gradient(90deg, #1e293b 60%, #334155 100%)',
    color: '#fff',
    border: 'none',
    borderRadius: 8,
    padding: '0.7rem 1.2rem',
    fontWeight: 700,
    fontSize: 18,
    cursor: 'pointer',
    boxShadow: '0 2px 8px #0002',
    transition: 'background 0.2s',
  },
};

export default function CHATUI() {
  const [messages, setMessages] = useState([
    { sender: 'bot', text: "Hello! I'm RAGnarok, an AI assistant. How can I help you today?" }
  ]);
  const [input, setInput] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  const [reasoningStates, setReasoningStates] = useState({}); // {idx: expanded}
  const scrollRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    // Scroll to bottom on new message
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim()) return;
    setMessages(prev => [...prev, { sender: 'user', text: input }]);
    setIsThinking(true);
    setMessages(prev => [...prev, { sender: 'bot', text: '__THINKING__' }]);

    try {
      const response = await fetch('https://rag-narok-ul49.onrender.com/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: input }),
        credentials: 'include', // <-- Ensure cookies are sent for session persistence
      });

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      const data = await response.json();
      setMessages(prev => prev.filter(msg => msg.text !== '__THINKING__'));

      if (data.error) {
        setMessages(prev => [...prev, { sender: 'bot', text: `Error: ${data.error}` }]);
      } else {
        let botText = data.response;
        let reasoning = '';

        if (typeof botText === 'string' && botText.includes('<think>')) {
          const thinkStart = botText.indexOf('<think>') + 7;
          const thinkEnd = botText.indexOf('</think>');
          reasoning = botText.substring(thinkStart, thinkEnd);
          botText = botText.substring(thinkEnd + 8).trim();
        }

        let reasoningIdx = null;
        if (reasoning) {
          setMessages(prev => {
            reasoningIdx = prev.length;
            setReasoningStates(states => ({ ...states, [reasoningIdx]: true }));
            return [...prev, { sender: 'bot', text: `**Reasoning:** ${reasoning}`, type: 'reasoning' }];
          });
          setTimeout(() => {
            setReasoningStates(states => {
              if (states[reasoningIdx] !== undefined) {
                return { ...states, [reasoningIdx]: false };
              }
              return states;
            });
          }, 2000);
        }
        setMessages(prev => [...prev, { sender: 'bot', text: botText }]);
      }
    } catch (error) {
      setMessages(prev => prev.filter(msg => msg.text !== '__THINKING__'));
      console.error('Error communicating with the backend:', error);
      setMessages(prev => [...prev, { sender: 'bot', text: 'Error: Unable to connect to the server.' }]);
    } finally {
      setIsThinking(false);
    }
    setInput('');
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') sendMessage();
  };

  const stylesWithScroll = {
    ...styles.chatArea,
    overflowY: 'auto', // Ensure scroll bar is always present
    maxHeight: '60vh', // Optional: limit height for better scroll
  };

  return (
    <div style={{ position: 'relative', minHeight: '100vh', background: 'linear-gradient(90deg, #1e293b 60%, #334155 100%)', paddingTop: 30 }}>
      <button style={styles.adminFloating} onClick={() => navigate('/admin')}>Admin</button>
      <div style={styles.container}>
        <header style={styles.header}>
          <div style={styles.headerLeft}>
            <img src={require('./iit_logo.png')} alt="IIT Ropar Logo" style={{ height: 34, marginRight: 10, verticalAlign: 'middle', borderRadius: 6, background: '#fff', boxShadow: '0 1px 4px #0001' }} />
            <span style={{ verticalAlign: 'middle' }}>IIT Ropar</span>
          </div>
          <div style={styles.headerCenter}>
            <img src={RAGnarokLogo} alt="RAGnarok Logo" style={styles.logo} />
            <span style={styles.title}>RAGnarok</span>
            <span style={{
              marginLeft: 18,
              fontWeight: 500,
              fontSize: 16,
              color: '#f1f5f9',
              letterSpacing: 0.5,
              background: 'rgba(30,41,59,0.18)',
              borderRadius: 8,
              padding: '4px 14px',
              boxShadow: '0 1px 4px #0001',
              display: 'inline-block',
            }}>
              AI Assistant
            </span>
          </div>
          <div style={styles.headerRight}>
            <img src={require('./logo_iota.png')} alt="Iota Cluster Logo" style={{ height: 40, marginRight: 5, verticalAlign: 'middle', borderRadius: 6, background: '#fff', boxShadow: '0 1px 4px #0001' }} />
            <span style={{ verticalAlign: 'middle', fontWeight: 900, fontSize: 17, color: '#fff', letterSpacing: 1 }}>Iota Cluster</span>
          </div>
        </header>
        <div style={stylesWithScroll} ref={scrollRef}>
          <AnimatePresence initial={false}>
            {messages.map((msg, idx) => {
              if (msg.type === 'reasoning') {
                const expanded = reasoningStates[idx] !== false;
                return expanded ? (
                  <motion.div
                    key={idx}
                    style={{ ...styles.message, ...styles.reasoningBox, marginBottom: 0, cursor: 'pointer', position: 'relative', display: 'flex', alignItems: 'center', gap: 8 }}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ duration: 0.2 }}
                  >
                    <span
                      style={{ marginRight: 8, display: 'flex', alignItems: 'flex-end', cursor: 'pointer', marginTop: -2 }}
                      onClick={() => setReasoningStates(states => ({ ...states, [idx]: false }))}
                    >
                      <FaChevronDown size={18} />
                    </span>
                    <span style={{ fontWeight: 700, color: '#fbbf24', marginRight: 6 }}>Reasoning:</span>
                    <span style={{ fontWeight: 400 }}>{msg.text.replace('**Reasoning:** ', '')}</span>
                  </motion.div>
                ) : (
                  <motion.div
                    key={idx}
                    style={{ ...styles.message, ...styles.reasoningBox, marginBottom: 7, minHeight: 0, padding: 0, display: 'flex', alignItems: 'center', justifyContent: 'flex-start', cursor: 'pointer', background: 'transparent', borderLeft: 'none', color: '#fbbf24', boxShadow: 'none', width: 'fit-content' }}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ duration: 0.2 }}
                    onClick={() => setReasoningStates(states => ({ ...states, [idx]: true }))}
                  >
                    <span style={{ display: 'flex', alignItems: 'flex-end', marginTop: -2, marginRight: 4 }}><FaChevronRight size={18} /></span>
                    <span style={{ fontWeight: 700, color: '#fbbf24', fontSize: 14 }}>Reasoning</span>
                  </motion.div>
                );
              }
              return (
                <motion.div
                  key={idx}
                  style={{
                    ...styles.message,
                    ...(msg.sender === 'bot' ? styles.botMessage : styles.userMessage),
                  }}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.2 }}
                >
                  {msg.text === '__THINKING__' ? <ThinkingDots /> : <span>{msg.text}</span>}
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>
        <div style={styles.inputArea}>
          <input
            type="text"
            placeholder="Type a message..."
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            style={styles.input}
          />
          <button onClick={sendMessage} style={styles.sendButton}>
            ➤
          </button>
        </div>
      </div>
    </div>
  );
}

function ThinkingDots() {
  const [dotCount, setDotCount] = React.useState(1);
  React.useEffect(() => {
    const interval = setInterval(() => {
      setDotCount(d => (d % 3) + 1);
    }, 400);
    return () => clearInterval(interval);
  }, []);
  return (
    <span style={{ fontStyle: 'italic', color: '#1e293b', fontWeight: 700 }}>
      RAGnarok is thinking{'.'.repeat(dotCount)}
    </span>
  );
}
