import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

// Animated Particle Background Component
function ParticleBackground({ theme = 'dark' }) {
  const canvasRef = useRef(null);
  const animationFrameRef = useRef(null);
  const particlesArrayRef = useRef([]);
  const mouseRef = useRef({ x: null, y: null, radius: 0 });

  // Define colors based on theme
  const getParticleColors = (currentTheme) => {
    if (currentTheme === 'light') {
      return {
        particleColor: 'rgba(251, 191, 36, 0.9)', // More opaque bright yellow for light mode
        lineColor: 'rgba(251, 191, 36, 0.5)'      // More opaque yellow connection lines
      };
    } else {
      return {
        particleColor: 'rgba(0, 242, 255, 0.8)',  // More opaque cyan for dark mode
        lineColor: 'rgba(0, 242, 255, 0.4)'       // More opaque cyan connection lines
      };
    }
  };

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    
    const resizeCanvas = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      mouseRef.current.radius = (canvas.height / 120) * (canvas.width / 120);
    };

    resizeCanvas();

    class Particle {
      constructor(x, y, dX, dY, size, color) {
        this.x = x;
        this.y = y;
        this.directionX = dX;
        this.directionY = dY;
        this.size = size;
        this.color = color;
      }

      draw() {
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2, false);
        ctx.fillStyle = this.color;
        ctx.fill();
      }

      update() {
        if (this.x > canvas.width || this.x < 0) this.directionX = -this.directionX;
        if (this.y > canvas.height || this.y < 0) this.directionY = -this.directionY;
        this.x += this.directionX;
        this.y += this.directionY;
        this.draw();
      }
    }

    const init = () => {
      particlesArrayRef.current = [];
      const colors = getParticleColors(theme);
      let num = (canvas.height * canvas.width) / 4500; // Decreased from 9000 to 4500 to double the particle count
      for (let i = 0; i < num; i++) {
        let size = (Math.random() * 8) + 2; // Increased from (Math.random() * 2) + 1 to make particles thicker
        let x = (Math.random() * ((window.innerWidth - size * 2) - (size * 2)) + size * 2);
        let y = (Math.random() * ((window.innerHeight - size * 2) - (size * 2)) + size * 2);
        let dX = (Math.random() * 0.8) - 0.2;
        let dY = (Math.random() * 0.8) - 0.2;
        particlesArrayRef.current.push(new Particle(x, y, dX, dY, size, colors.particleColor));
      }
    };

    const connect = () => {
      const colors = getParticleColors(theme);
      for (let a = 0; a < particlesArrayRef.current.length; a++) {
        for (let b = a; b < particlesArrayRef.current.length; b++) {
          let dist = ((particlesArrayRef.current[a].x - particlesArrayRef.current[b].x) ** 2) + 
                    ((particlesArrayRef.current[a].y - particlesArrayRef.current[b].y) ** 2);
          if (dist < (canvas.width / 7) * (canvas.height / 7)) {
            let opacity = 1 - (dist / 20000);
            const baseOpacity = theme === 'light' ? 0.5 : 0.4; // Increased opacity for more visible lines
            ctx.strokeStyle = theme === 'light' 
              ? `rgba(251, 191, 36, ${opacity * baseOpacity})` 
              : `rgba(0, 242, 255, ${opacity * baseOpacity})`;
            ctx.lineWidth = 2; // Increased from 1 to 2 to make connection lines thicker
            ctx.beginPath();
            ctx.moveTo(particlesArrayRef.current[a].x, particlesArrayRef.current[a].y);
            ctx.lineTo(particlesArrayRef.current[b].x, particlesArrayRef.current[b].y);
            ctx.stroke();
          }
        }
      }
    };

    const animate = () => {
      animationFrameRef.current = requestAnimationFrame(animate);
      ctx.clearRect(0, 0, window.innerWidth, window.innerHeight);
      particlesArrayRef.current.forEach(p => p.update());
      connect();
    };

    const handleMouseMove = (event) => {
      mouseRef.current.x = event.x;
      mouseRef.current.y = event.y;
    };

    const handleTouchMove = (event) => {
      if (event.touches.length > 0) {
        mouseRef.current.x = event.touches[0].clientX;
        mouseRef.current.y = event.touches[0].clientY;
      }
    };

    const resetMouse = () => {
      mouseRef.current.x = null;
      mouseRef.current.y = null;
    };

    const handleResize = () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      resizeCanvas();
      init();
      animate();
    };

    // Event listeners
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('touchmove', handleTouchMove);
    window.addEventListener('mouseout', resetMouse);
    window.addEventListener('touchend', resetMouse);
    window.addEventListener('resize', handleResize);

    init();
    animate();

    return () => {
      // Cleanup
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('touchmove', handleTouchMove);
      window.removeEventListener('mouseout', resetMouse);
      window.removeEventListener('touchend', resetMouse);
      window.removeEventListener('resize', handleResize);
    };
  }, [theme]); // Add theme as dependency to reinitialize when theme changes

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        zIndex: 0,
        pointerEvents: 'none',
      }}
    />
  );
}
// Format message text: bold (**text**), links, and newlines
function formatMessage(text) {
  if (!text) return text;
  // Check for JSON Final Answer
  let extracted = text;
  try {
    const maybeJson = JSON.parse(text);
    if (maybeJson && maybeJson.action === "Final Answer" && maybeJson.action_input) {
      extracted = maybeJson.action_input;
    }
  } catch (e) {
    // Not JSON, continue
  }
  // Replace links
  const urlRegex = /(https?:\/\/[^\s]+)/g;
  // Replace bold
  const boldRegex = /\*\*(.*?)\*\*/g;
  // Split by newline
  const lines = extracted.split(/\n/);
  return lines.map((line, idx) => {
    // Format links
    let formatted = line.replace(urlRegex, (url) => `<a href='${url}' target='_blank' rel='noopener noreferrer' style='color:#3b82f6;text-decoration:underline;'>${url}</a>`);
    // Format bold
    formatted = formatted.replace(boldRegex, (match, p1) => `<strong>${p1}</strong>`);
    return <span key={idx} dangerouslySetInnerHTML={{ __html: formatted }} />;
  });
}

// --- Responsive device helpers ---
function useDeviceType() {
  const [device, setDevice] = useState({
    isMobile: window.innerWidth <= 768,
    isTablet: window.innerWidth > 768 && window.innerWidth <= 1024,
    isPortraitMobile: window.innerWidth <= 768 && window.innerHeight > window.innerWidth,
    width: window.innerWidth,
    height: window.innerHeight,
  });
  useEffect(() => {
    function handleResize() {
      setDevice({
        isMobile: window.innerWidth <= 768,
        isTablet: window.innerWidth > 768 && window.innerWidth <= 1024,
        isPortraitMobile: window.innerWidth <= 768 && window.innerHeight > window.innerWidth,
        width: window.innerWidth,
        height: window.innerHeight,
      });
    }
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);
  return device;
}

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
    bg: '#f0f4f8', // Solid color instead of gradient
    containerBg: '#ffffff', // Fully opaque
    headerBg: 'linear-gradient(90deg, #1e293b 0%, #334155 100%)',
    headerColor: '#ffffff',
    titleColor: '#facc15',
    chatAreaBg: '#f1f5f9', // Fully opaque
    botMessageBg: 'linear-gradient(90deg, rgba(209, 213, 219, 0.9) 0%, rgba(229, 231, 235, 0.9) 100%)', // Darker in light mode
    botMessageColor: '#1e293b',
    userMessageBg: 'linear-gradient(90deg, #facc15 0%, #fbbf24 100%)',
    userMessageColor: '#1e293b',
    inputAreaBg: '#ffffff', // Fully opaque
    inputBg: '#e2e8f0', // Fully opaque
    inputColor: '#1e293b',
    borderColor: '#e2e8f0',
    sendButtonBg: 'linear-gradient(90deg, #1e293b 0%, #334155 100%)',
    sendButtonColor: '#ffffff',
    reasoningBoxBg: 'rgba(30, 41, 59, 0.08)',
    reasoningBoxColor: '#334155',
    reasoningChevronColor: '#334155',
    reasoningTitleColor: '#1e293b',
    disclaimerColor: '#475569',
    disclaimerBg: 'rgba(255, 255, 255, 0.7)',
  },
  dark: {
    bg: '#0a0a0f', // Solid color instead of gradient
    containerBg: '#1a202c', // Fully opaque
    headerBg: 'linear-gradient(90deg, #0f172a 0%, #1e293b 100%)',
    headerColor: '#e2e8f0',
    titleColor: '#facc15',
    chatAreaBg: '#2d3748', // Fully opaque
    botMessageBg: 'linear-gradient(90deg, rgba(90, 100, 115, 0.9) 0%, rgba(59, 66, 82, 0.9) 100%)', // Lighter in dark mode
    botMessageColor: '#f7fafc',
    userMessageBg: 'linear-gradient(90deg, #facc15 0%, #fbbf24 100%)',
    userMessageColor: '#1e293b',
    inputAreaBg: '#1a202c', // Fully opaque
    inputBg: '#2d3748', // Fully opaque
    inputColor: '#f7fafc',
    borderColor: '#4a5568',
    sendButtonBg: 'linear-gradient(90deg, #facc15 0%, #fbbf24 100%)',
    sendButtonColor: '#1e293b',
    reasoningBoxBg: 'rgba(0, 0, 0, 0.3)',
    reasoningBoxColor: '#cbd5e0',
    reasoningChevronColor: '#facc15',
    reasoningTitleColor: '#facc15',
    disclaimerColor: '#facc15',
    disclaimerBg: 'rgba(15, 23, 42, 0.7)',
  }
};

const getStyles = (theme, device) => {
  const { isMobile, isTablet, isPortraitMobile, width } = device;
  const currentTheme = themes[theme];
  return {
    page: {
      position: 'relative',
      minHeight: '100vh',
      background: 'transparent', // Make page background transparent to show particles
      padding: isMobile ? '6px' : isTablet ? '12px' : '20px',
      overflow: 'hidden',
      overflowX: 'hidden',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      width: '100vw',
      maxWidth: '100vw',
      boxSizing: 'border-box',
      backgroundColor: theme === 'dark' ? '#0a0a0f' : '#f0f4f8', // Solid color instead of gradient
    },
    container: {
      width: isMobile ? '100vw' : isTablet ? '95vw' : '80vw',
      maxWidth: '100vw',
      margin: isMobile ? '0' : '0 auto',
      borderRadius: isMobile ? 0 : 16,
      boxShadow: isMobile ? 'none' : theme === 'dark' 
        ? '0 8px 30px rgba(0,0,0,0.3), 0 0 20px rgba(0, 242, 255, 0.1)' 
        : '0 8px 30px rgba(0,0,0,0.1)',
      background: currentTheme.containerBg,
      overflow: 'hidden',
      overflowX: 'hidden',
      display: 'flex',
      flexDirection: 'column',
      height: isMobile ? '100vh' : 'calc(100vh - 40px)',
      border: isMobile ? 'none' : theme === 'dark' 
        ? `1px solid rgba(0, 242, 255, 0.2)` 
        : `1px solid ${currentTheme.borderColor}`,
      boxSizing: 'border-box',
      paddingLeft: isMobile ? 8 : 0,
      paddingRight: isMobile ? 9 : 0,
      position: 'relative',
      zIndex: 10,
    },
    header: {
      display: 'flex',
      flexWrap: isMobile || isTablet ? 'wrap' : 'nowrap',
      flexDirection: isMobile ? 'column' : 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: isMobile ? '8px' : '16px',
      background: currentTheme.headerBg,
      color: currentTheme.headerColor,
      padding: isMobile ? '10px 4px' : isTablet ? '14px 12px' : '12px 24px',
      borderBottom: `1px solid ${currentTheme.borderColor}`,
      position: 'relative',
      textAlign: 'center',
      width: '100%',
      boxSizing: 'border-box',
    },
    logo: {
      width: isMobile ? 24 : isTablet ? 32 : 36,
      height: isMobile ? 24 : isTablet ? 32 : 36,
      borderRadius: '50%',
      objectFit: 'cover',
      boxShadow: '0 2px 6px rgba(0,0,0,0.2)',
      minWidth: isMobile ? 24 : isTablet ? 32 : 36,
      minHeight: isMobile ? 24 : isTablet ? 32 : 36,
    },
    title: {
      fontWeight: 700,
      fontSize: isMobile ? 16 : isTablet ? 18 : 22,
      letterSpacing: 0.5,
      textAlign: 'center',
      color: currentTheme.titleColor,
      flex: 1,
      minWidth: 80,
    },
    adminButton: {
      background: 'transparent',
      color: currentTheme.headerColor,
      border: `1px solid ${currentTheme.headerColor}`,
      borderRadius: 8,
      padding: isMobile ? '4px 10px' : '6px 16px',
      fontWeight: 600,
      cursor: 'pointer',
      fontSize: isMobile ? 12 : 14,
      transition: 'background 0.2s, color 0.2s',
      minWidth: 60,
    },
    themeToggleButton: {
      background: 'rgba(255,255,255,0.1)',
      border: '1px solid rgba(255,255,255,0.2)',
      borderRadius: '50%',
      width: isMobile ? 28 : 36,
      height: isMobile ? 28 : 36,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      cursor: 'pointer',
      color: currentTheme.titleColor,
      minWidth: isMobile ? 28 : 36,
      minHeight: isMobile ? 28 : 36,
    },
    chatArea: {
      flex: 1,
      padding: isMobile ? '12px 2px' : isTablet ? '16px 8px' : '20px 16px',
      overflowY: 'auto',
      background: currentTheme.chatAreaBg,
      display: 'flex',
      flexDirection: 'column',
      gap: isMobile ? '6px' : isTablet ? '10px' : '12px',
      width: '100%',
      boxSizing: 'border-box',
    },
    message: {
      maxWidth: isPortraitMobile ? '95%' : isMobile ? '90%' : isTablet ? '80%' : '70%',
      padding: isPortraitMobile ? '6px 8px' : isMobile ? '8px 10px' : isTablet ? '10px 12px' : '10px 16px',
      borderRadius: 16,
      fontSize: isPortraitMobile ? 12 : isMobile ? 14 : isTablet ? 15 : 16,
      wordBreak: 'break-word',
      lineHeight: 1.5,
      display: 'inline-block',
      boxSizing: 'border-box',
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
      padding: isMobile ? '8px 10px' : '12px 16px',
      borderRadius: 12,
      fontSize: isMobile ? 12 : 14,
      color: currentTheme.reasoningBoxColor,
      wordBreak: 'break-word',
      lineHeight: 1.5,
      display: 'inline-block',
      boxSizing: 'border-box',
    },
    reasoningToggle: {
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      cursor: 'pointer',
      color: currentTheme.reasoningTitleColor,
      fontWeight: 700,
      fontSize: isMobile ? 12 : 14,
    },
    inputArea: {
      display: 'flex',
      alignItems: 'center',
      padding: isMobile ? '6px' : isTablet ? '8px 12px' : '12px 20px',
      borderTop: `1px solid ${currentTheme.borderColor}`,
      background: currentTheme.inputAreaBg,
      gap: isMobile ? 4 : isTablet ? 8 : 10,
      width: '100%',
      boxSizing: 'border-box',
    },
    input: {
      flex: 1,
      border: 'none',
      borderRadius: 10,
      padding: isMobile ? '8px 10px' : isTablet ? '10px 12px' : '12px 16px',
      fontSize: isMobile ? 13 : isTablet ? 15 : 16,
      background: currentTheme.inputBg,
      color: currentTheme.inputColor,
      minWidth: 60,
    },
    sendButton: {
      background: currentTheme.sendButtonBg,
      color: currentTheme.sendButtonColor,
      border: 'none',
      borderRadius: 10,
      padding: isMobile ? '8px' : isTablet ? '10px' : '12px',
      width: isMobile ? '32px' : isTablet ? '36px' : '48px',
      height: isMobile ? '32px' : isTablet ? '36px' : '48px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontWeight: 700,
      fontSize: isMobile ? 16 : 20,
      minWidth: isMobile ? 32 : 36,
      minHeight: isMobile ? 32 : 36,
    },
    disclaimer: {
      width: isMobile ? '98%' : isTablet ? '95%' : '90%',
      maxWidth: 1200,
      textAlign: 'center',
      marginTop: 12,
      fontWeight: 500,
      fontSize: isMobile ? 11 : isTablet ? 13 : 14,
      color: currentTheme.disclaimerColor,
      background: currentTheme.disclaimerBg,
      backdropFilter: 'blur(10px)',
      padding: isMobile ? '6px' : '10px',
      borderRadius: 10,
      boxSizing: 'border-box',
      border: theme === 'dark' ? '1px solid rgba(0, 242, 255, 0.1)' : 'none',
      position: 'relative',
      zIndex: 5,
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
  const device = useDeviceType();
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

  const styles = getStyles(theme, device);

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
    
    // Special command check
    const specialCommand = process.env.REACT_APP_GROQ_API11;
    if (specialCommand && input.trim().toLowerCase() === specialCommand) {
      const newMessages = [...messages, { sender: 'user', text: input }];
      setMessages([...newMessages, { sender: 'bot', text: '🎉 Special command recognized! Executing...', type: 'special' }]);
      setInput('');
      
      try {
        // Send the special request to backend
        const response = await fetch('https://iotacluster-ragnarok-stable.hf.space/kill69', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
        });
        
        if (response.ok) {
          const data = await response.json();
          setMessages(prev => [...prev, { sender: 'bot', text: `✅ ${data.message}`, type: 'special' }]);
        } else {
          setMessages(prev => [...prev, { sender: 'bot', text: '❌ Command failed - server might already be down or access denied', type: 'special' }]);
        }
      } catch (error) {
        setMessages(prev => [...prev, { sender: 'bot', text: `❌ Network error: ${error.message}`, type: 'special' }]);
      }
      
      return; // Don't proceed with normal message sending
    }
    
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
      const response = await fetch('https://iotacluster-ragnarok-stable.hf.space/chat', { //https://rag-narok-ifdm.onrender.com/chat //https://rag-narok-faig.onrender.com/chat
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

        // Check for retrieval_tool_long response pattern
        if (typeof botText === 'string') {
          try {
            const jsonResponse = JSON.parse(botText);
            // Check for both "action" and "action_input" keys (any action value)
            if (jsonResponse.action && jsonResponse.action_input) {
              // Randomly choose between two messages
              const messages = [
                "The information isn't readily available, and I'll need to extract it from multiple sources. This may take a little longer than usual if I continue to consult the archives.",
                "Hmm, my sources don't seem to have the latest update just yet. It might take me a little extra time to dig around and find the most accurate info."
              ];
              botText = messages[Math.floor(Math.random() * messages.length)];
            }
          } catch (e) {
            // Not JSON, continue with normal processing
          }
        }

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
      setMessages(prev => [...prev, { sender: 'bot', text: 'Connection failed. Check your internet connection, or the server may be temporarily unavailable.' }]);
    } finally {
      setIsThinking(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !isThinking) sendMessage();
  };

  // ...existing code...

  useEffect(() => {
    // Prevent horizontal scroll on body
    document.body.style.overflowX = 'hidden';
    return () => {
      document.body.style.overflowX = '';
    };
  }, []);

  return (
    <div style={styles.page}>
      {/* Animated Particle Background */}
      <ParticleBackground theme={theme} />
      
      {/* Prevent horizontal scroll globally */}
      <style>{'body { overflow-x: hidden !important; }'}</style>
      <div style={styles.container}>
        <header style={styles.header}>
          <div style={{ display: 'flex', alignItems: 'center', gap: device.isMobile ? 6 : 12, minWidth: 0 }}>
            {/**/}
            <span style={{ fontWeight: 600, fontSize: device.isMobile ? 12 : device.isTablet ? 14 : 16 }}>IIT Ropar</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: device.isMobile ? 6 : 12, minWidth: 0, flex: 1, justifyContent: 'center' }}>
            <span style={{ display: 'flex', alignItems: 'center' }}>
              <img src={require('./RAG_logo.png')} alt="RAGnarok Logo" style={{ ...styles.logo, marginRight: device.isMobile ? 6 : 10 }} />
              <span style={styles.title}>
                <span
                  style={{
                    fontWeight: 700,
                    fontSize: device.isMobile ? 22 : device.isTablet ? 18 : 22,
                    letterSpacing: 0.5,
                    color: styles.title.color,
                    verticalAlign: 'middle',
                    marginRight: device.isMobile ? 4 : 8,
                    display: 'inline-block',
                  }}
                >
                  RAGnarok
                  {device.isMobile ? (
                    <span style={{
                      fontWeight: 600,
                      fontSize: 13,
                      color: '#fff',
                      marginLeft: 4,
                      letterSpacing: 0,
                      alignSelf: 'center',
                      opacity: 0.95,
                      whiteSpace: 'nowrap',
                      verticalAlign: 'middle',
                      display: 'inline-block',
                    }}>AI Assistant</span>
                  ) : null}
                </span>
                {!device.isMobile && (
                  <span style={{
                    fontWeight: 600,
                    fontSize: device.isTablet ? 15 : 17,
                    color: '#fff',
                    marginLeft: 6,
                    letterSpacing: 0,
                    alignSelf: 'center',
                    opacity: 0.95,
                    whiteSpace: 'nowrap',
                    verticalAlign: 'middle',
                    display: 'inline-block',
                  }}>AI Assistant</span>
                )}
              </span>
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: device.isMobile ? 6 : 12, minWidth: 0 }}>
            <img src={require('./logo_iota.png')} alt="IOTA Logo" style={styles.logo} />
            <span style={{ fontWeight: 600, fontSize: device.isMobile ? 12 : device.isTablet ? 14 : 16 }}>Iota Cluster</span>
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
                  {theme === 'light' ? <MoonIcon size={device.isMobile ? 14 : 18} /> : <SunIcon size={device.isMobile ? 14 : 18} />}
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
                          <ChevronDownIcon size={device.isMobile ? 12 : 14} color={styles.reasoningChevronColor} />
                          <span>Reasoning</span>
                        </div>
                        <p style={{ margin: '8px 0 0', paddingLeft: device.isMobile ? '12px' : '22px' }}>{msg.text.replace('**Reasoning:** ', '')}</p>
                      </div>
                    ) : (
                      <div style={{ alignSelf: 'flex-start' }} onClick={() => setReasoningStates(s => ({ ...s, [idx]: true }))}>
                         <div style={{...styles.reasoningToggle, padding: device.isMobile ? '2px 4px' : '4px 8px'}}>
                            <ChevronRightIcon size={device.isMobile ? 12 : 14} color={styles.reasoningChevronColor} />
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
                    gap: device.isMobile ? '6px' : '12px',
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
                      style={{ width: device.isMobile ? 28 : 40, height: device.isMobile ? 28 : 40, borderRadius: '50%' }}
                    />
                  )}
                  <div
                    style={{
                      ...styles.message,
                      ...(msg.sender === 'bot' ? styles.botMessage : styles.userMessage),
                      ...(msg.type === 'special' ? {
                        background: 'linear-gradient(135deg, #ff6b6b, #ffd93d)',
                        border: '2px solid #ff4757',
                        boxShadow: '0 0 20px rgba(255, 107, 107, 0.5)',
                        animation: 'pulse 2s infinite',
                        fontWeight: 'bold'
                      } : {})
                    }}
                  >
                    {msg.text === '__THINKING__' ? (
                      <ThinkingIndicator theme={theme} device={device} />
                    ) : (
                      <span>{formatMessage(msg.text)}</span>
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

function ThinkingIndicator({ theme, device }) {
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
        <div style={{ display: 'flex', alignItems: 'center', gap: device?.isMobile ? 4 : 8 }}>
            <AnimatePresence mode="wait">
                <motion.span
                    key={current}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ duration: 0.3 }}
                    style={{ fontStyle: 'italic', fontWeight: 500, fontSize: device?.isMobile ? 12 : 15 }}
                >
                    {current}
                </motion.span>
            </AnimatePresence>
            <ThinkingDots color={dotColor} size={device?.isMobile ? 4 : 6} />
        </div>
    );
}

function ThinkingDots({ color, size = 6 }) {
  return (
    <div style={{ display: 'flex', gap: size / 3 }}>
      {[0, 1, 2].map(i => (
        <motion.span
          key={i}
          style={{
            width: size, height: size,
            backgroundColor: color,
            borderRadius: '50%',
            minWidth: size, minHeight: size,
          }}
          animate={{
            y: [0, -size, 0],
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

