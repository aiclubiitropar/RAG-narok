import React, { useState } from 'react';
import { motion } from 'framer-motion';
import RAGnarokLogo from './RAG_logo.png';

export default function AdminPanel() {
  const [showLogin, setShowLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [workerStatus, setWorkerStatus] = useState('');
  const [logMessage, setLogMessage] = useState('');
  const [file, setFile] = useState(null);
  const [selectedModel, setSelectedModel] = useState('deepseek-r1-distill-llama-70b');

  const modelOptions = [
    'deepseek-r1-distill-llama-70b',
    'qwen-qwq-32b',
    'qwen/qwen3-32b',
    'llama-3.1-8b-instant',
    'llama-3.3-70b-versatile',
    'llama3-70b-8192',
    'llama3-8b-8192',
    'meta-llama/llama-4-maverick-17b-128e-instruct',
    'meta-llama/llama-4-scout-17b-16e-instruct'
  ];

  const handleLogin = async () => {
    try {
      const response = await fetch('https://rag-narok-ul49.onrender.com/admin/verify_credentials', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      const result = await response.json();
      if (response.ok && result.message === 'Authentication successful.') {
        setIsAuthenticated(true);
        setShowLogin(false);
      } else {
        alert('Invalid credentials');
      }
    } catch (error) {
      console.error('Error verifying credentials:', error);
      alert('Error verifying credentials');
    }
  };

  const fetchWorkerStatus = async () => {
    try {
      const res = await fetch('https://rag-narok-ul49.onrender.com/admin/worker_status', {
        method: 'GET',
        headers: {
          'X-Admin-Email': 'club.iotacluster@iitrpr.ac.in', // Ensure the admin email is sent
        },
      });
      if (!res.ok) {
        throw new Error('Failed to fetch worker status');
      }
      const data = await res.json();
      setWorkerStatus(data.running ? 'Running' : 'Stopped');
    } catch (error) {
      console.error('Error fetching worker status:', error);
      setWorkerStatus('Error fetching status');
    }
  };

  const startWorker = async () => {
    try {
      const res = await fetch('https://rag-narok-ul49.onrender.com/admin/start_shortterm_worker', {
        method: 'POST',
      });
      const data = await res.json();
      setLogMessage(data.message || 'Worker started.');
      fetchWorkerStatus();

      // Continuously fetch worker status until stopped
      const intervalId = setInterval(async () => {
        const statusRes = await fetch('https://rag-narok-ul49.onrender.com/admin/worker_status');
        const statusData = await statusRes.json();
        if (!statusData.running) {
          clearInterval(intervalId);
        }
        setWorkerStatus(statusData.running ? 'Running' : 'Stopped');
      }, 5000); // Check every 5 seconds
    } catch (error) {
      setLogMessage('Error starting worker.');
    }
  };

  const stopWorker = async () => {
    try {
      const res = await fetch('https://rag-narok-ul49.onrender.com/admin/stop_shortterm_worker', {
        method: 'POST',
      });
      const data = await res.json();
      setLogMessage(data.message || 'Worker stopped.');
      fetchWorkerStatus();
    } catch (error) {
      setLogMessage('Error stopping worker.');
    }
  };

  const downloadLogs = async () => {
    try {
      const res = await fetch('https://rag-narok-ul49.onrender.com/admin/logs');
      if (res.status === 404) {
        setLogMessage('Log file not found.');
        return;
      }
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = 'rag.log';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      setLogMessage('Log file downloaded.');
    } catch (error) {
      setLogMessage('Error downloading log file.');
    }
  };

  const uploadJson = async (e) => {
    e.preventDefault();
    if (!file) {
      setLogMessage('Please select a file to upload.');
      return;
    }
    setLogMessage('Uploading...'); // Show loading message
    const formData = new FormData();
    formData.append('file', file);
    try {
      const res = await fetch('https://rag-narok-ul49.onrender.com/admin/upload_json', {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      setLogMessage(data.message || 'File uploaded successfully.');
    } catch (error) {
      setLogMessage('Error uploading file.');
    }
  };

  const handleChangeModel = async () => {
    try {
      const res = await fetch('https://rag-narok-ul49.onrender.com/admin/change_model', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model: selectedModel })
      });
      const data = await res.json();
      setLogMessage(data.message || 'Model changed successfully.');
    } catch (error) {
      setLogMessage('Error changing model.');
    }
  };

  // Theme colors inspired by the chatbot: dark background, off-white text, yellow accent
  const pageBg = '#e0e7ef'; // Light blue-gray background for the whole page
  const panelBg = 'linear-gradient(135deg, #e0e7ef 60%,rgb(224, 224, 224) 100%)';
  const borderColor = '#e5e5dc';
  const logoColor = '#23232b';
  const buttonBg = 'linear-gradient(90deg, #facc15 60%, #fbbf24 100%)';
  const buttonText = '#181a18';
  const accentShadow = '0 2px 12px #facc1533';
  const inputBg = 'rgba(34,36,58,0.7)';
  const inputBorder = '#facc15';
  const inputText = '#23232b';

  if (showLogin) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: 'Inter, Segoe UI, sans-serif' }}>
        <div style={{ width: 400, padding: '2em', borderRadius: 12, boxShadow: '0 8px 40px #000a', background: '#fff', textAlign: 'center' }}>
          <img src={RAGnarokLogo} alt="RAGnarok Logo" style={{ width: 50, marginBottom: 20 }} />
          <h2 style={{ marginBottom: 20 }}>Admin Login</h2>
          <input
            type="email"
            placeholder="Enter email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            style={{ width: '100%', padding: '10px', marginBottom: '10px', borderRadius: '5px', border: '1px solid #ccc' }}
          />
          <input
            type="password"
            placeholder="Enter password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={{ width: '100%', padding: '10px', marginBottom: '20px', borderRadius: '5px', border: '1px solid #ccc' }}
          />
          <button
            onClick={handleLogin}
            style={{ padding: '10px 20px', borderRadius: '5px', background: '#facc15', color: '#1e293b', fontWeight: 'bold', cursor: 'pointer' }}
          >
            Login
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', background: pageBg, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: 'Inter, Segoe UI, sans-serif' }}>
      <div style={{ width: 480, background: panelBg, borderRadius: 24, boxShadow: '0 8px 40px #000a', padding: '2.5em 2.5em 2em 2.5em', color: logoColor, border: 'none', backdropFilter: 'blur(12px)', borderTop: `4px solid ${borderColor}` }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'linear-gradient(90deg, #1e293b 60%, #334155 100%)',
          borderRadius: '16px 16px 0 0',
          padding: '0.9em 1.2em',
          margin: '-2.5em -2.5em 2em -2.5em',
          color: '#fff',
          fontWeight: 800,
          fontSize: 24,
          letterSpacing: 1.2,
          boxShadow: '0 2px 8px #0002',
        }}>
          <img src={RAGnarokLogo} alt="RAGnarok Logo" style={{ width: 38, height: 38, borderRadius: '50%', background: '#fff', objectFit: 'cover', boxShadow: '0 2px 8px #0001', marginRight: 14 }} />
          Admin Panel
        </div>

        {/* Worker Status */}
        <div style={{ marginBottom: 28, textAlign: 'center' }}>
          <button
            onClick={fetchWorkerStatus}
            style={{
              background: buttonBg,
              color: buttonText,
              border: 'none',
              borderRadius: 12,
              padding: '10px 22px',
              fontWeight: 700,
              fontSize: 16,
              cursor: 'pointer',
              boxShadow: accentShadow,
              marginBottom: 8,
              marginRight: 8,
              transition: 'transform 0.1s, box-shadow 0.2s',
              outline: 'none',
            }}
            onMouseDown={e => e.currentTarget.style.transform = 'scale(0.97)'}
            onMouseUp={e => e.currentTarget.style.transform = 'scale(1)'}
            onBlur={e => e.currentTarget.style.boxShadow = accentShadow}
            onFocus={e => e.currentTarget.style.boxShadow = '0 0 0 2px #facc1555'}
          >Check Worker Status</button>
          <span style={{
            fontWeight: 700,
            fontSize: 17,
            color:
              workerStatus === 'Running'
                ? '#34d399' // green
                : workerStatus === 'Stopped'
                ? '#f87171' // red
                : '#23232b', // black for all other cases
            marginLeft: 10,
            letterSpacing: 1,
            transition: 'color 0.3s',
          }}>Status: {workerStatus}</span>
        </div>

        {/* Worker Controls */}
        <div style={{ display: 'flex', justifyContent: 'center', gap: 16, marginBottom: 32 }}>
          <button
            onClick={startWorker}
            style={{
              background: buttonBg,
              color: buttonText,
              border: 'none',
              borderRadius: 12,
              padding: '10px 22px',
              fontWeight: 700,
              fontSize: 16,
              cursor: 'pointer',
              boxShadow: '0 2px 12px #34d39933',
              transition: 'transform 0.1s, box-shadow 0.2s',
              outline: 'none',
            }}
            onMouseDown={e => e.currentTarget.style.transform = 'scale(0.97)'}
            onMouseUp={e => e.currentTarget.style.transform = 'scale(1)'}
            onBlur={e => e.currentTarget.style.boxShadow = '0 2px 12px #34d39933'}
            onFocus={e => e.currentTarget.style.boxShadow = '0 0 0 2px #facc1555'}
          >Start Worker</button>
          <button
            onClick={stopWorker}
            style={{
              background: buttonBg,
              color: buttonText,
              border: 'none',
              borderRadius: 12,
              padding: '10px 22px',
              fontWeight: 700,
              fontSize: 16,
              cursor: 'pointer',
              boxShadow: '0 2px 12px #a78bfa33',
              transition: 'transform 0.1s, box-shadow 0.2s',
              outline: 'none',
            }}
            onMouseDown={e => e.currentTarget.style.transform = 'scale(0.97)'}
            onMouseUp={e => e.currentTarget.style.transform = 'scale(1)'}
            onBlur={e => e.currentTarget.style.boxShadow = '0 2px 12px #a78bfa33'}
            onFocus={e => e.currentTarget.style.boxShadow = '0 0 0 2px #facc1555'}
          >Stop Worker</button>
        </div>

        {/* Upload JSON */}
        <div style={{
          background: 'rgba(163, 161, 161, 0.62)',
          borderRadius: 16,
          padding: '1.2em 1em',
          marginBottom: 32,
          boxShadow: '0 2px 12pxrgba(229, 229, 220, 0.94)',
          border: '1.5px solidrgb(224, 224, 232)',
        }}>
          <form onSubmit={uploadJson} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12 }}>
            <input
              type="file"
              accept="application/json"
              onChange={e => setFile(e.target.files[0])}
              style={{
                background: '#f5f6fa', // lighter color for file input
                color: inputText,
                border: `2px solid ${inputBorder}`,
                borderRadius: 10,
                padding: '8px 12px',
                fontSize: 15,
                fontWeight: 500,
                marginBottom: 6,
                outline: 'none',
                width: '100%',
                maxWidth: 260,
                cursor: 'pointer',
              }}
            />
            <button
              type="submit"
              style={{
                background: buttonBg,
                color: buttonText,
                border: 'none',
                borderRadius: 10,
                padding: '8px 22px',
                fontWeight: 700,
                fontSize: 15,
                cursor: 'pointer',
                boxShadow: accentShadow,
                transition: 'transform 0.1s, box-shadow 0.2s',
                outline: 'none',
              }}
              onMouseDown={e => e.currentTarget.style.transform = 'scale(0.97)'}
              onMouseUp={e => e.currentTarget.style.transform = 'scale(1)'}
              onBlur={e => e.currentTarget.style.boxShadow = accentShadow}
              onFocus={e => e.currentTarget.style.boxShadow = '0 0 0 2pxrgba(235, 233, 223, 0.89)'}
            >Upload JSON</button>
          </form>
        </div>

        {/* Download Logs and Model Selector */}
        <div style={{ textAlign: 'center', marginBottom: 18, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12 }}>
          <button
            onClick={downloadLogs}
            style={{
              background: buttonBg,
              color: buttonText,
              border: 'none',
              borderRadius: 12,
              padding: '10px 22px',
              fontWeight: 700,
              fontSize: 16,
              cursor: 'pointer',
              boxShadow: accentShadow,
              marginBottom: 8,
              transition: 'transform 0.1s, box-shadow 0.2s',
              outline: 'none',
            }}
            onMouseDown={e => e.currentTarget.style.transform = 'scale(0.97)'}
            onMouseUp={e => e.currentTarget.style.transform = 'scale(1)'}
            onBlur={e => e.currentTarget.style.boxShadow = accentShadow}
            onFocus={e => e.currentTarget.style.boxShadow = '0 0 0 2px #facc1555'}
          >Download Logs</button>
          <select
            value={selectedModel}
            onChange={e => setSelectedModel(e.target.value)}
            style={{
              background: '#f5f6fa',
              color: inputText,
              border: `2px solid ${inputBorder}`,
              borderRadius: 10,
              padding: '8px 12px',
              fontSize: 15,
              fontWeight: 500,
              outline: 'none',
              minWidth: 220,
              marginBottom: 8
            }}
          >
            {modelOptions.map(model => (
              <option key={model} value={model}>{model}</option>
            ))}
          </select>
          <button
            onClick={handleChangeModel}
            style={{
              background: buttonBg,
              color: buttonText,
              border: 'none',
              borderRadius: 12,
              padding: '10px 22px',
              fontWeight: 700,
              fontSize: 16,
              cursor: 'pointer',
              boxShadow: accentShadow,
              marginBottom: 8,
              transition: 'transform 0.1s, box-shadow 0.2s',
              outline: 'none',
            }}
            onMouseDown={e => e.currentTarget.style.transform = 'scale(0.97)'}
            onMouseUp={e => e.currentTarget.style.transform = 'scale(1)'}
            onBlur={e => e.currentTarget.style.boxShadow = accentShadow}
            onFocus={e => e.currentTarget.style.boxShadow = '0 0 0 2px #facc1555'}
          >Change Model</button>
        </div>
        <div style={{ color: '#facc15', fontWeight: 600, fontSize: 15, minHeight: 24, marginTop: 6 }}>{logMessage}</div>
      </div>
    </div>
  );
}
