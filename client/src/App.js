import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './App.css';
import CHATUI from './components/CHATUI';
import AdminPanel from './components/AdminPanel';

function App() {
  return (
    <Router>
      <div className="App">
        <header className="App-header">
          <h1>Welcome to RAGnarok</h1>
          <p>Ask about IIT Ropar, campus life, academics, and more.</p>
        </header>
        <Routes>
          <Route path="/" element={<CHATUI />} />
          <Route path="/admin-login" element={<AdminPanel />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
