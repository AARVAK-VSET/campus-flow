import React, { useState, useEffect } from 'react';
import api from '../api';
import { FaServer, FaCheckCircle, FaExclamationTriangle, FaTerminal, FaWifi, FaSync } from 'react-icons/fa';
import { useNavigate } from 'react-router-dom';
import { FaBriefcaseMedical, FaStore, FaBullhorn, FaParking } from 'react-icons/fa';

const Home = () => {
  const navigate = useNavigate();
  const [backendStatus, setBackendStatus] = useState<'checking' | 'online' | 'offline'>('checking');
  const [errorMsg, setErrorMsg] = useState('');

  const checkHealth = async () => {
    setBackendStatus('checking');
    try {
      await api.get('health');
      setBackendStatus('online');
    } catch (err: any) {
      setBackendStatus('offline');
      setErrorMsg(err.message || 'Connection refused');
    }
  };

  useEffect(() => {
    checkHealth();
  }, []);
  
  const features = [
    {
      title: 'Medical Room',
      desc: 'Track student health records and get AI-powered disease pattern alerts.',
      icon: <FaBriefcaseMedical size={40} />,
      path: '/medical',
      color: 'var(--accent-primary)',
    },
    {
      title: 'Stationery Store',
      desc: 'Manage inventory with smart demand forecasting and automated proposals.',
      icon: <FaStore size={40} />,
      path: '/stationery',
      color: '#ff00ff',
    },
    {
      title: 'Voice Agency',
      desc: 'Multilingual AI announcement agent with scheduled multilingual text-to-speech.',
      icon: <FaBullhorn size={40} />,
      path: '/announcements',
      color: '#00ff00',
    },
    {
      title: 'Smart Parking',
      desc: 'Computer vision based car slot tracking and occupancy prediction.',
      icon: <FaParking size={40} />,
      path: '/parking',
      color: '#ffff00',
    },
  ];

  return (
    <div className="home-page" style={{ padding: '2rem 0' }}>
      <header style={{ textAlign: 'center', marginBottom: '4rem' }}>
        <h1 style={{ fontSize: '4rem', fontWeight: '700', marginBottom: '1rem', background: 'linear-gradient(to right, var(--accent-primary), var(--accent-secondary))', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
          CAMPUS AI
        </h1>
        <p style={{ fontSize: '1.5rem', color: 'var(--text-secondary)', maxWidth: '800px', margin: '0 auto' }}>
          The intelligent operating system for the modern campus. Powered by advanced AI and computer vision.
        </p>
      </header>

      <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr', gap: '2rem', marginTop: '2rem' }}>
        <div className="glass-card">
          <h3>Welcome to CampusAI Hub</h3>
          <p style={{ color: 'var(--text-secondary)', marginTop: '1rem', lineHeight: '1.6' }}>
            Empowering campus management with artificial intelligence. Select a module from the sidebar to manage medical records, inventory, announcements, or smart parking.
          </p>
          <div style={{ marginTop: '2rem', display: 'flex', gap: '1rem' }}>
            <div style={{ padding: '1.5rem', background: 'rgba(255,255,255,0.03)', borderRadius: '12px', flex: 1 }}>
              <h4 style={{ color: 'var(--accent-primary)', marginBottom: '0.5rem' }}>AI Insights</h4>
              <p style={{ fontSize: '0.85rem' }}>Real-time forecasting and pattern recognition active across all modules.</p>
            </div>
            <div style={{ padding: '1.5rem', background: 'rgba(255,255,255,0.03)', borderRadius: '12px', flex: 1 }}>
              <h4 style={{ color: 'var(--accent-primary)', marginBottom: '0.5rem' }}>Automated Booking</h4>
              <p style={{ fontSize: '0.85rem' }}>Now integrated with Uber and Ola for emergency student transport.</p>
            </div>
          </div>
        </div>

        <div className="glass-card" style={{ borderLeft: `4px solid ${backendStatus === 'online' ? '#00ffa3' : backendStatus === 'offline' ? '#ff4d4d' : '#666'}` }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h3>System Status</h3>
            <span style={{ 
              padding: '0.3rem 0.8rem', 
              borderRadius: '20px', 
              fontSize: '0.75rem', 
              fontWeight: 700,
              background: backendStatus === 'online' ? 'rgba(0, 255, 163, 0.1)' : 'rgba(255, 77, 77, 0.1)',
              color: backendStatus === 'online' ? '#00ffa3' : '#ff4d4d'
            }}>
              {backendStatus.toUpperCase()}
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem' }}>
             {backendStatus === 'online' ? (
               <FaCheckCircle size={32} color="#00ffa3" />
             ) : (
               <FaExclamationTriangle size={32} color="#ff4d4d" />
             )}
             <div>
               <div style={{ fontWeight: 600 }}>Backend Connection</div>
               <div style={{ fontSize: '0.8rem', opacity: 0.7 }}>
                 {backendStatus === 'online' ? 'Connected to 127.0.0.1:8000' : 'Disconnected / Blocked'}
               </div>
             </div>
          </div>

          {(backendStatus === 'offline' || backendStatus === 'checking') && (
            <div style={{ background: 'rgba(0,0,0,0.2)', padding: '1rem', borderRadius: '8px', fontSize: '0.85rem' }}>
              {backendStatus === 'offline' ? (
                <>
                  <strong style={{ color: '#ff4d4d' }}>Error:</strong> {errorMsg}
                </>
              ) : (
                <div style={{ color: 'var(--accent-primary)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <FaSync size={12} className="spin" /> Verifying connection...
                </div>
              )}
              
              <div style={{ marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <FaTerminal size={12} /> Run <code>start_backend.bat</code>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <FaWifi size={12} /> Check local firewall (Port 8000)
                </div>
                <button 
                  onClick={checkHealth}
                  disabled={backendStatus === 'checking'}
                  style={{ 
                    marginTop: '0.5rem',
                    padding: '0.5rem',
                    background: backendStatus === 'checking' ? '#444' : 'var(--accent-primary)',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: backendStatus === 'checking' ? 'not-allowed' : 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '0.5rem',
                    fontSize: '0.8rem',
                    fontWeight: 600
                  }}
                >
                  <FaSync size={10} className={backendStatus === 'checking' ? 'spin' : ''} />
                  {backendStatus === 'checking' ? 'Checking...' : 'Retry Connection'}
                </button>
              </div>
            </div>
          )}
          
          <p style={{ fontSize: '0.8rem', marginTop: '1.5rem', opacity: 0.5 }}>
            {backendStatus === 'online' ? 'All features are fully operational.' : 'Some features (data loading, AI insights) will be unavailable.'}
          </p>
        </div>
      </div>

      <div className="grid-dashboard" style={{ marginTop: '2rem' }}>
        {features.map((f, i) => (
          <div
            key={i}
            className="glass-card"
            style={{ cursor: 'pointer', textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem' }}
            onClick={() => navigate(f.path)}
          >
            <div style={{ color: f.color, marginBottom: '0.5rem' }}>{f.icon}</div>
            <h3 style={{ fontSize: '1.5rem' }}>{f.title}</h3>
            <p style={{ color: 'var(--text-secondary)' }}>{f.desc}</p>
            <div style={{ marginTop: 'auto', paddingTop: '1rem', fontWeight: '700', color: f.color }}>
              LAUNCH MODULE &rarr;
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Home;
