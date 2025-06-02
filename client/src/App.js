import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import CHATUI from './components/CHATUI';
import AdminPanel from './components/AdminPanel';

function App() {
  return (
    <Router>
      <div style={{ minHeight: '100vh', background: 'linear-gradient(135deg, #0d1117 60%, #1976d2 100%)', display: 'flex', flexDirection: 'column' }}>
        <Routes>
          <Route path="/" element={<CHATUI />} />
          <Route path="/admin" element={<AdminPanel />} />
          <Route path="/admin-login" element={<AdminPanel />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
