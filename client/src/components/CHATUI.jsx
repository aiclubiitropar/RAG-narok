import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

// --- Helper to check device size ---
const isMobile = window.innerWidth <= 768; // Adjusted breakpoint for better responsiveness
const isTablet = window.innerWidth > 768 && window.innerWidth <= 1024; // Adjusted breakpoint for tablets
const isPortraitMobile = window.innerWidth <= 768 && window.innerHeight > window.innerWidth; // Check for portrait mode

// --- SVG Icon Components (to replace react-icons) ---
const ChevronDownIcon = ({ size = 14, color = 'currentColor' }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="6 9 12 15 18 9"></polyline>
  </svg>
);

const ChevronRightIcon = ({ size = 14, color = 'currentColor' }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="9 18 15 12 9 6"></polyline>
  </svg>
);

const SunIcon = ({ size = 18, color = 'currentColor' }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="5"></circle>
    <line x1="12" y1="1" x2="12" y2="3"></line>
    <line x1="12" y1="21" x2="12" y2="23"></line>
    <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
    <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
    <line x1="1" y1="12" x2="3" y2="12"></line>
    <line x1="21" y1="12" x2="23" y2="12"></line>
    <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
    <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
  </svg>
);

const MoonIcon = ({ size = 18, color = 'currentColor' }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
  </svg>
);


// --- Theming and Styles ---
const themes = {
  light: {
    bg: 'linear-gradient(135deg, #f5f7fa 0%, #e0e7ef 100%)',
    containerBg: '#ffffff',
    headerBg: 'linear-gradient(90deg, #1e293b 0%, #334155 100%)',
    headerColor: '#ffffff',
    titleColor: '#facc15',
    chatAreaBg: '#f1f5f9',
    botMessageBg: 'linear-gradient(90deg, #d1d5db 0%, #e5e7eb 100%)', // Darker in light mode
    botMessageColor: '#1e293b',
    userMessageBg: 'linear-gradient(90deg, #facc15 0%, #fbbf24 100%)',
    userMessageColor: '#1e293b',
    inputAreaBg: '#ffffff',
    inputBg: '#e2e8f0',
    inputColor: '#1e293b',
    borderColor: '#e2e8f0',
    sendButtonBg: 'linear-gradient(90deg, #1e293b 0%, #334155 100%)',
    sendButtonColor: '#ffffff',
    reasoningBoxBg: 'rgba(30, 41, 59, 0.05)',
    reasoningBoxColor: '#334155',
    reasoningChevronColor: '#334155',
    reasoningTitleColor: '#1e293b',
    disclaimerColor: '#475569',
    disclaimerBg: 'rgba(255, 255, 255, 0.5)',
  },
  dark: {
    bg: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
    containerBg: '#1a202c',
    headerBg: 'linear-gradient(90deg, #0f172a 0%, #1e293b 100%)',
    headerColor: '#e2e8f0',
    titleColor: '#facc15',
    chatAreaBg: '#2d3748',
    botMessageBg: 'linear-gradient(90deg, #5a6473 0%, #3b4252 100%)', // Lighter in dark mode
    botMessageColor: '#f7fafc',
    userMessageBg: 'linear-gradient(90deg, #facc15 0%, #fbbf24 100%)',
    userMessageColor: '#1e293b',
    inputAreaBg: '#1a202c',
    inputBg: '#2d3748',
    inputColor: '#f7fafc',
    borderColor: '#4a5568',
    sendButtonBg: 'linear-gradient(90deg, #facc15 0%, #fbbf24 100%)',
    sendButtonColor: '#1e293b',
    reasoningBoxBg: 'rgba(0, 0, 0, 0.2)',
    reasoningBoxColor: '#cbd5e0',
    reasoningChevronColor: '#facc15',
    reasoningTitleColor: '#facc15',
    disclaimerColor: '#facc15',
    disclaimerBg: 'rgba(15, 23, 42, 0.5)',
  }
};

const getStyles = (theme) => {
  const currentTheme = themes[theme];
  return {
    page: {
      position: 'relative',
      minHeight: '100vh',
      background: currentTheme.bg,
      padding: isMobile ? '10px' : '20px',
      overflow: 'hidden',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
    },
    container: {
      width: isMobile ? '95vw' : isTablet ? '90vw' : '80vw',
      maxWidth: 1200,
      margin: '0 auto',
      borderRadius: isMobile ? 8 : 16,
      boxShadow: isMobile ? 'none' : '0 8px 30px rgba(0,0,0,0.1)',
      background: currentTheme.containerBg,
      overflow: 'hidden',
      display: 'flex',
      flexDirection: 'column',
      height: isMobile ? '100vh' : 'calc(100vh - 40px)',
      border: `1px solid ${currentTheme.borderColor}`,
    },
    header: {
      display: 'flex',
      flexWrap: 'wrap', // Ensure wrapping for all child elements
      alignItems: 'center',
      justifyContent: 'space-between', // Default spacing for desktop
      background: currentTheme.headerBg,
      color: currentTheme.headerColor,
      padding: isMobile || isTablet ? '16px' : '12px 24px', // Larger padding for mobile/tablet
      borderBottom: `1px solid ${currentTheme.borderColor}`,
      gap: isMobile || isTablet ? '12px' : '0',
      position: 'relative', // Allow absolute positioning for centered elements
      flexDirection: isMobile || isTablet ? 'column' : 'row', // Stack elements vertically in responsive mode
    },
    headerGroup: {
      display: 'flex',
      alignItems: 'center',
      gap: isMobile ? '6px' : '12px',
      position: isMobile || isTablet ? 'relative' : 'static', // Adjust positioning for responsive mode
      justifyContent: 'flex-start', // Ensure IIT Ropar logo and name are aligned to the left
      width: '100%', // Take full width to align to the left
    },
    logo: {
      width: isMobile ? 28 : 36,
      height: isMobile ? 28 : 36,
      borderRadius: '50%',
      objectFit: 'cover',
      boxShadow: '0 2px 6px rgba(0,0,0,0.2)',
    },
    title: {
      fontWeight: 700,
      fontSize: isMobile ? 18 : 22,
      letterSpacing: 0.5,
      color: currentTheme.titleColor,
    },
    adminButton: {
      background: 'transparent',
      color: currentTheme.headerColor,
      border: `1px solid ${currentTheme.headerColor}`,
      borderRadius: 8,
      padding: '6px 16px',
      fontWeight: 600,
      cursor: 'pointer',
      fontSize: 14,
      transition: 'background 0.2s, color 0.2s',
    },
    themeToggleButton: {
        background: 'rgba(255,255,255,0.1)',
        border: '1px solid rgba(255,255,255,0.2)',
        borderRadius: '50%',
        width: 36,
        height: 36,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        cursor: 'pointer',
        color: currentTheme.titleColor,
    },
    chatArea: {
      flex: 1,
      padding: isMobile ? '20px 6px' : '20px 16px', // Shift first bot message slightly down
      overflowY: 'auto',
      background: currentTheme.chatAreaBg,
      display: 'flex',
      flexDirection: 'column',
      gap: isMobile ? '8px' : '12px',
    },
    message: {
      maxWidth: isPortraitMobile ? '90%' : isMobile ? '85%' : '70%',
      padding: isPortraitMobile ? '6px 10px' : isMobile ? '8px 12px' : '10px 16px',
      borderRadius: 16,
      fontSize: isPortraitMobile ? 12 : isMobile ? 14 : 16,
      wordBreak: 'break-word',
      lineHeight: 1.5,
      display: 'inline-block',
    },
    botMessage: {
      background: currentTheme.botMessageBg,
      color: currentTheme.botMessageColor,
      alignSelf: 'flex-start',
      borderTopLeftRadius: 4,
    },
    userMessage: {
      background: currentTheme.userMessageBg,
      color: currentTheme.userMessageColor,
      alignSelf: 'flex-end',
      borderTopRightRadius: 4,
      fontWeight: 500,
    },
    reasoningBox: {
      background: currentTheme.reasoningBoxBg,
      borderLeft: `3px solid ${currentTheme.reasoningChevronColor}`,
      padding: '12px 16px',
      borderRadius: 12,
      fontSize: 14,
      color: currentTheme.reasoningBoxColor,
      wordBreak: 'break-word',
      lineHeight: 1.5,
      display: 'inline-block',
    },
    reasoningToggle: {
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        cursor: 'pointer',
        color: currentTheme.reasoningTitleColor,
        fontWeight: 700,
        fontSize: 14,
    },
    inputArea: {
      display: 'flex',
      alignItems: 'center',
      padding: isMobile ? '8px' : '12px 20px',
      borderTop: `1px solid ${currentTheme.borderColor}`,
      background: currentTheme.inputAreaBg,
      gap: isMobile ? 6 : 10,
    },
    input: {
      flex: 1,
      border: 'none',
      borderRadius: 10,
      padding: isMobile ? '10px 12px' : '12px 16px',
      fontSize: isMobile ? 14 : 16,
      background: currentTheme.inputBg,
      color: currentTheme.inputColor,
    },
    sendButton: {
      background: currentTheme.sendButtonBg,
      color: currentTheme.sendButtonColor,
      border: 'none',
      borderRadius: 10,
      padding: isMobile ? '10px' : '12px',
      width: isMobile ? '40px' : '48px',
      height: isMobile ? '40px' : '48px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontWeight: 700,
      fontSize: 20,
    },
    disclaimer: {
      width: '90%',
      maxWidth: 1200,
      textAlign: 'center',
      marginTop: 16,
      fontWeight: 500,
      fontSize: isMobile ? 12 : 14,
      color: currentTheme.disclaimerColor,
      background: currentTheme.disclaimerBg,
      padding: '10px',
      borderRadius: 10,
    },
  };
};

// Function to get or set the theme preference in cookies
function getOrSetThemePreference(theme) {
  const cookieName = 'theme_preference';
  if (theme) {
    document.cookie = `${cookieName}=${theme}; path=/; SameSite=Lax;`;
    return theme;
  }
  const match = document.cookie.match(new RegExp('(^| )' + cookieName + '=([^;]+)'));
  return match ? match[2] : 'light'; // Default to 'light' theme if no cookie is found
}

// Function to set the authentication cookie
function setAuthCookie() {
  const authCookieName = 'auth_cookie';
  const authCookieValue = process.env.AUTH_COOKIE_SECRET;
  if (authCookieValue) {
    document.cookie = `${authCookieName}=${authCookieValue}; path=/; SameSite=Lax;`;
  }
}

export default function CHATUI() {
  const [theme, setTheme] = useState(getOrSetThemePreference()); // Initialize theme from cookie
  const [messages, setMessages] = useState([
    { sender: 'bot', text: "Hello! I'm RAGnarok, an AI assistant. How can I help you today?" }
  ]);
  const [input, setInput] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  const [reasoningStates, setReasoningStates] = useState({});
  const scrollRef = useRef(null);
  
  // This replaces useNavigate for simple navigation.
  // In a real app, you'd use the router's navigate function.
  const navigateToAdmin = () => window.location.href = '/admin';

  const styles = getStyles(theme);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  useEffect(() => {
    setAuthCookie(); // Set the authentication cookie on component mount
  }, []);

  const toggleTheme = () => {
    setTheme(prevTheme => {
      const newTheme = prevTheme === 'light' ? 'dark' : 'light';
      getOrSetThemePreference(newTheme); // Update the cookie with the new theme
      return newTheme;
    });
  };

  function getOrSetUserUUID() {
    const cookieName = 'user_uuid';
    const match = document.cookie.match(new RegExp('(^| )' + cookieName + '=([^;]+)'));
    if (match) return match[2];
    const uuid = crypto.randomUUID ? crypto.randomUUID() : ([1e7]+-1e3+-4e3+-8e3+-1e11).replace(/[018]/g, c=>(c^crypto.getRandomValues(new Uint8Array(1))[0]&15>>c/4).toString(16));
    document.cookie = `${cookieName}=${uuid}; path=/; SameSite=Lax;`;
    return uuid;
  }

  const sendMessage = async () => {
    if (!input.trim()) return;
    const newMessages = [...messages, { sender: 'user', text: input }];
    setMessages(newMessages);
    setIsThinking(true);
    setInput('');
    
    // Add thinking message after a short delay for better UX
    setTimeout(() => {
        setMessages(prev => [...prev, { sender: 'bot', text: '__THINKING__' }]);
    }, 300);

    const user_uuid = getOrSetUserUUID();

    try {
      const response = await fetch('https://rag-narok-faig.onrender.com/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: input, user_uuid }),
        credentials: 'include',
      });

      if (!response.ok) throw new Error(`Network response was not ok: ${response.statusText}`);

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

        if (reasoning) {
          const reasoningIdx = messages.length + 1; // Predict index
          setReasoningStates(states => ({ ...states, [reasoningIdx]: true }));
          setMessages(prev => [...prev, { sender: 'bot', text: `**Reasoning:** ${reasoning}`, type: 'reasoning' }]);
          
          setTimeout(() => {
            setReasoningStates(states => ({ ...states, [reasoningIdx]: false }));
          }, 4000); // Auto-collapse after 4 seconds
        }
        setMessages(prev => [...prev, { sender: 'bot', text: botText }]);
      }
    } catch (error) {
      setMessages(prev => prev.filter(msg => msg.text !== '__THINKING__'));
      console.error('Error communicating with the backend:', error);
      setMessages(prev => [...prev, { sender: 'bot', text: 'Sorry, I encountered an error. The server is under maintenance. Please try again later.' }]);
    } finally {
      setIsThinking(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !isThinking) sendMessage();
  };

  function parseTextWithFormatting(text) {
    const urlRegex = /(https?:\/\/[^\s]+)/g;
    const parts = text.split(/(\*\*.*?\*\*|https?:\/\/[^\s]+)/g);
    return parts.map((part, index) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={index}>{part.slice(2, -2)}</strong>;
      }
      if (urlRegex.test(part)) {
        return <a key={index} href={part} target="_blank" rel="noopener noreferrer" style={{ color: '#3b82f6', textDecoration: 'underline' }}>{part}</a>;
      }
      return part;
    });
  }

  return (
    <div style={styles.page}>
      <div style={styles.container}>
        <header style={{ ...styles.header, justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <img src={require('./iit-ropar-01.jpg')} alt="IIT Ropar Logo" style={{ ...styles.logo, borderRadius: '6px' }} />
                <span style={{ fontWeight: 600, fontSize: isMobile ? 14 : 16 }}>IIT Ropar</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <img src={require('./RAG_logo.png')} alt="RAGnarok Logo" style={styles.logo} />
                <span style={styles.title}>RAGnarok</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <img src={require('./logo_iota.png')} alt="IOTA Logo" style={styles.logo} />
                <span style={{ fontWeight: 600, fontSize: isMobile ? 14 : 16 }}>Iota Cluster</span>
                <button onClick={navigateToAdmin} style={styles.adminButton}>Admin</button>
                <button onClick={toggleTheme} style={styles.themeToggleButton} aria-label="Toggle theme">
                    <AnimatePresence mode="wait">
                        <motion.div
                            key={theme}
                            initial={{ opacity: 0, rotate: -90 }}
                            animate={{ opacity: 1, rotate: 0 }}
                            exit={{ opacity: 0, rotate: 90 }}
                            transition={{ duration: 0.2 }}
                        >
                            {theme === 'light' ? <MoonIcon size={18} /> : <SunIcon size={18} />}
                        </motion.div>
                    </AnimatePresence>
                </button>
            </div>
        </header>

        <div style={styles.chatArea} ref={scrollRef}>
          <AnimatePresence>
            {messages.map((msg, idx) => {
              if (msg.type === 'reasoning') {
                const isExpanded = reasoningStates[idx] !== false;
                return (
                  <motion.div key={idx} layout initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                    {isExpanded ? (
                      <div style={{ ...styles.message, ...styles.botMessage, ...styles.reasoningBox }}>
                        <div style={styles.reasoningToggle} onClick={() => setReasoningStates(s => ({ ...s, [idx]: false }))}>
                          <ChevronDownIcon size={14} color={styles.reasoningChevronColor} />
                          <span>Reasoning</span>
                        </div>
                        <p style={{ margin: '8px 0 0', paddingLeft: '22px' }}>{msg.text.replace('**Reasoning:** ', '')}</p>
                      </div>
                    ) : (
                      <div style={{ alignSelf: 'flex-start' }} onClick={() => setReasoningStates(s => ({ ...s, [idx]: true }))}>
                         <div style={{...styles.reasoningToggle, padding: '4px 8px'}}>
                            <ChevronRightIcon size={14} color={styles.reasoningChevronColor} />
                            <span>Reasoning</span>
                         </div>
                      </div>
                    )}
                  </motion.div>
                );
              }
              return (
                <motion.div
                  key={idx}
                  layout
                  style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '12px',
                    ...(msg.sender === 'bot' ? { flexDirection: 'row' } : { flexDirection: 'row-reverse' }),
                  }}
                  initial={{ opacity: 0, y: 10, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  transition={{ duration: 0.3, type: 'spring', stiffness: 150, damping: 20 }}
                >
                  {msg.sender === 'bot' && (
                    <img
                      src={require('./RAG_logo.png')}
                      alt="RAGnarok Avatar"
                      style={{ width: 40, height: 40, borderRadius: '50%' }}
                    />
                  )}
                  <div
                    style={{
                      ...styles.message,
                      ...(msg.sender === 'bot' ? styles.botMessage : styles.userMessage),
                    }}
                  >
                    {msg.text === '__THINKING__' ? (
                      <ThinkingIndicator theme={theme} />
                    ) : (
                      <span>{parseTextWithFormatting(msg.text)}</span>
                    )}
                  </div>
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
            disabled={isThinking}
          />
          <button onClick={sendMessage} style={styles.sendButton} disabled={isThinking}>
            ➤
          </button>
        </div>
      </div>
      <div style={styles.disclaimer}>
        RAGnarok is an AI assistant built using Retrieval-Augmented Generation.
        While it strives to be accurate, mistakes can happen. Please verify critical information.
      </div>
    </div>
  );
}

function ThinkingIndicator({ theme }) {
    const phrases = [
        'RAGnarok is thinking', 'Retrieving knowledge', 'Consulting the archives',
        'Summoning insights', 'Crunching data', 'Synthesizing response',
        'Querying the vault', 'Gathering context'
    ];
    const [current, setCurrent] = useState(phrases[0]);

    useEffect(() => {
        const interval = setInterval(() => {
            setCurrent(phrases[Math.floor(Math.random() * phrases.length)]);
        }, 2000);
        return () => clearInterval(interval);
    }, []);

    const dotColor = theme === 'light' ? '#1e293b' : '#f7fafc';

    return (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <AnimatePresence mode="wait">
                <motion.span
                    key={current}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ duration: 0.3 }}
                    style={{ fontStyle: 'italic', fontWeight: 500 }}
                >
                    {current}
                </motion.span>
            </AnimatePresence>
            <ThinkingDots color={dotColor} />
        </div>
    );
}

function ThinkingDots({ color }) {
  return (
    <div style={{ display: 'flex', gap: 2 }}>
      {[0, 1, 2].map(i => (
        <motion.span
          key={i}
          style={{
            width: 6, height: 6,
            backgroundColor: color,
            borderRadius: '50%',
          }}
          animate={{
            y: [0, -4, 0],
            opacity: [0.5, 1, 0.5],
          }}
          transition={{
            duration: 1.2,
            repeat: Infinity,
            delay: i * 0.2,
            ease: 'easeInOut',
          }}
        />
      ))}
    </div>
  );
}
