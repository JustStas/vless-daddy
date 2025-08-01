import React from 'react';
import { Route, BrowserRouter as Router, Routes } from 'react-router-dom';
import './App.css';
import Clients from './components/Clients';
import Create from './components/Create';
import Dashboard from './components/Dashboard';

function App() {
  return (
    <Router>
      <div className="container">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/create" element={<Create />} />
          <Route path="/clients/:serverId" element={<Clients />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
