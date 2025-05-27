import React, { useState } from 'react';
import './AdminPanel.css';

function AdminPanel() {
  const [workerStatus, setWorkerStatus] = useState('');
  const [logMessage, setLogMessage] = useState('');
  const [file, setFile] = useState(null);

  const fetchWorkerStatus = async () => {
    try {
      const res = await fetch('http://localhost:5000/admin/worker_status');
      const data = await res.json();
      setWorkerStatus(data.running ? 'Running' : 'Stopped');
    } catch (error) {
      setWorkerStatus('Error fetching status');
    }
  };

  const startWorker = async () => {
    try {
      const res = await fetch('http://localhost:5000/admin/start_shortterm_worker', {
        method: 'POST',
      });
      const data = await res.json();
      setLogMessage(data.message || 'Worker started.');
      fetchWorkerStatus();
    } catch (error) {
      setLogMessage('Error starting worker.');
    }
  };

  const stopWorker = async () => {
    try {
      const res = await fetch('http://localhost:5000/admin/stop_shortterm_worker', {
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
      const res = await fetch('http://localhost:5000/admin/logs');
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
    const formData = new FormData();
    formData.append('file', file);
    try {
      const res = await fetch('http://localhost:5000/admin/upload_json', {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      setLogMessage(data.message || 'File uploaded successfully.');
    } catch (error) {
      setLogMessage('Error uploading file.');
    }
  };

  return (
    <div className="admin-panel">
      <h2>Admin Panel</h2>
      <div className="worker-status">
        <button onClick={fetchWorkerStatus}>Check Worker Status</button>
        <p>Status: {workerStatus}</p>
      </div>
      <div className="worker-controls">
        <button onClick={startWorker}>Start Worker</button>
        <button onClick={stopWorker}>Stop Worker</button>
      </div>
      <div className="upload-json">
        <form onSubmit={uploadJson}>
          <input
            type="file"
            accept="application/json"
            onChange={(e) => setFile(e.target.files[0])}
          />
          <button type="submit">Upload JSON</button>
        </form>
      </div>
      <div className="logs">
        <button onClick={downloadLogs}>Download Logs</button>
        <p>{logMessage}</p>
      </div>
    </div>
  );
}

export default AdminPanel;
