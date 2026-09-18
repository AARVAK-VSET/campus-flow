import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { IconContext } from 'react-icons';
import { FaHome, FaBriefcaseMedical, FaStore, FaBullhorn, FaParking } from 'react-icons/fa';
import { Toaster } from 'react-hot-toast';

import Home from './pages/Home';
import Medical from './pages/Medical';
import Stationery from './pages/Stationery';
import Announcements from './pages/Announcements';
import Parking from './pages/Parking';

const Sidebar = () => {
  const location = useLocation();
  
  const links = [
    { path: '/', name: 'Home', icon: <FaHome /> },
    { path: '/medical', name: 'Medical Room', icon: <FaBriefcaseMedical /> },
    { path: '/stationery', name: 'Stationery Store', icon: <FaStore /> },
    { path: '/announcements', name: 'Voice Agency', icon: <FaBullhorn /> },
    { path: '/parking', name: 'Smart Parking', icon: <FaParking /> },
  ];

  return (
    <div className="sidebar">
      <div className="logo" style={{ fontSize: '1.5rem', marginBottom: '2rem', color: 'var(--accent-primary)' }}>
        CampusAI
      </div>
      <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        {links.map((link) => (
          <Link
            key={link.path}
            to={link.path}
            className={`sidebar-link ${location.pathname === link.path ? 'active' : ''}`}
          >
            {link.icon}
            <span>{link.name}</span>
          </Link>
        ))}
      </nav>
    </div>
  );
};

function App() {
  return (
    <Router>
      <IconContext.Provider value={{ size: '1.2rem' }}>
        <div style={{ display: 'flex' }}>
          <Sidebar />
          <main className="main-content">
            <Toaster position="top-right" />
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/medical" element={<Medical />} />
              <Route path="/stationery" element={<Stationery />} />
              <Route path="/announcements" element={<Announcements />} />
              <Route path="/parking" element={<Parking />} />
            </Routes>
          </main>
        </div>
      </IconContext.Provider>
    </Router>
  );
}

export default App;
