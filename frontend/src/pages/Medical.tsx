import React, { useState, useEffect } from 'react';
import api from '../api';
import VoiceButton from '../components/VoiceButton';
import VoiceAssistant from '../components/VoiceAssistant';
import ChartCard from '../components/ChartCard';
import toast from 'react-hot-toast';
import { FaPlus, FaTrash, FaEdit, FaPhone, FaTaxi, FaRobot } from 'react-icons/fa';

const Medical = () => {
  const [records, setRecords] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [insights, setInsights] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [showAssistant, setShowAssistant] = useState(false);
  const [formData, setFormData] = useState({
    student_name: '',
    branch: '',
    year: 1,
    issue: '',
    severity: 'low',
    treatment_status: 'pending',
    parent_contact: '',
    address: '',
  });
  const [showCabModal, setShowCabModal] = useState(false);
  const [selectedStudent, setSelectedStudent] = useState<any>(null);
  const [estimates, setEstimates] = useState<{ uber: string; ola: string } | null>(null);
  const [calcLoading, setCalcLoading] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      // 1. Fetch Records (Priority)
      const resRecords = await api.get('medical/');
      setRecords(resRecords.data);
      
      // 2. Fetch Analytics (Non-blocking)
      try {
        const resDashboard = await api.get('medical/analytics');
        setStats(resDashboard.data.stats);
        setInsights(resDashboard.data.insights);
      } catch (analyticsErr: any) {
        console.warn('Analytics failed to load', analyticsErr);
        toast.error('Dashboard analytics unavailable');
      }
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message;
      toast.error('Failed to fetch medical records: ' + msg);
      console.error('Fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('medical/', formData);
      toast.success('Record added successfully');
      setShowModal(false);
      fetchData();
    } catch (err) {
      toast.error('Failed to add record');
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('Are you sure?')) return;
    try {
      await api.delete(`medical/${id}`);
      toast.success('Record deleted');
      fetchData();
    } catch (err) {
      toast.error('Failed to delete record');
    }
  };

  const getGeocode = async (address: string) => {
    try {
      const res = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(address)}&limit=1`);
      const data = await res.json();
      if (data && data[0]) {
        return { lat: parseFloat(data[0].lat), lon: parseFloat(data[0].lon) };
      }
    } catch (e) {
      console.error('Geocoding failed', e);
    }
    return null;
  };

  const calculateDistance = (lat1: number, lon1: number, lat2: number, lon2: number) => {
    const R = 6371; // km
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
              Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
              Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
  };

  useEffect(() => {
    if (showCabModal && selectedStudent?.address) {
      setCalcLoading(true);
      setEstimates(null);
      
      const fetchEstimates = async () => {
        // 1. Get Destination Coords
        const destCoords = await getGeocode(selectedStudent.address);
        
        // 2. Get User Coords
        navigator.geolocation.getCurrentPosition(async (pos) => {
          const userLat = pos.coords.latitude;
          const userLon = pos.coords.longitude;
          
          if (destCoords) {
            const distance = calculateDistance(userLat, userLon, destCoords.lat, destCoords.lon);
            // Mock Pricing: ₹50 base + ₹12/km (Uber), ₹45 base + ₹11.5/km (Ola)
            const uberPrice = 50 + (distance * 12);
            const olaPrice = 45 + (distance * 11.5);
            setEstimates({
              uber: `₹${Math.round(uberPrice)}`,
              ola: `₹${Math.round(olaPrice)}`
            });
          }
          setCalcLoading(false);
        }, () => setCalcLoading(false));
      };

      fetchEstimates();
    }
  }, [showCabModal, selectedStudent]);

  const handleCabSearch = (brand: string) => {
    const destination = selectedStudent?.address ? encodeURIComponent(selectedStudent.address) : '';
    const query = brand ? `${brand} cabs near me` : 'cabs near me';

    const openUrls = (lat?: number, lng?: number) => {
      let url = '';
      const origin = lat && lng ? `${lat},${lng}` : 'current+location';
      
      if (brand === 'Uber') {
        const pickupStr = lat && lng ? `pickup[latitude]=${lat}&pickup[longitude]=${lng}` : 'pickup=my_location';
        url = `https://m.uber.com/ul/?action=setPickup&${pickupStr}${destination ? `&dropoff[formatted_address]=${destination}` : ''}`;
      } else if (brand === 'Ola') {
        url = `https://book.olacabs.com/?pickup_name=Current+Location&drop_name=${destination || 'me'}`;
      } else if (brand === 'Rapido') {
        url = `https://www.google.com/maps/search/Rapido+bike+taxi+at+${destination || 'me'}`;
      } else {
        url = `https://www.google.com/maps/search/cabs+near+me/@${lat || 28.6139},${lng || 77.2090},14z`;
      }

      if (url) {
        window.open(url, '_blank');
      }
      setShowCabModal(false);
    };

    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => openUrls(pos.coords.latitude, pos.coords.longitude),
        () => openUrls()
      );
    } else {
      openUrls();
    }
  };

  const handleVoiceResult = async (text: string) => {
    try {
      const res = await api.post('medical/voice', null, { params: { command: text } });
      toast.success('AI parsed: ' + text);
    } catch (err) {
      toast.error('Voice parsing failed');
    }
  };

  const handleAssistantComplete = async (data: any) => {
    try {
      await api.post('medical/', data);
      toast.success('Record added by Arjun!');
      setShowAssistant(false);
      fetchData();
    } catch (err) {
      toast.error('Failed to save record from Assistant');
    }
  };

  return (
    <div className="medical-page">
      {showAssistant && (
        <VoiceAssistant 
          context="medical" 
          onComplete={handleAssistantComplete} 
          onClose={() => setShowAssistant(false)} 
        />
      )}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h2>Medical Room Management</h2>
        <div style={{ display: 'flex', gap: '1rem' }}>
          <button className="btn-primary" onClick={() => setShowAssistant(true)} style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
            <FaRobot /> Start Arjun (AI)
          </button>
          <VoiceButton onResult={handleVoiceResult} />
          <button className="btn-primary" onClick={() => setShowModal(true)}>
            <FaPlus /> Add Record
          </button>
        </div>
      </div>

      <div className="grid-dashboard">
        {stats && (
          <>
            <ChartCard title="Diseases Frequency" type="bar" data={stats.by_issue} dataKey="count" />
            <ChartCard title="Visit Trends" type="line" data={stats.daily_visits} dataKey="count" nameKey="date" />
            <div className="glass-card">
              <h3 style={{ marginBottom: '1rem' }}>AI Insights & Predictions</h3>
              <div style={{ color: 'var(--text-secondary)', lineHeight: '1.6', fontSize: '0.95rem', whiteSpace: 'pre-wrap' }}>
                {insights || 'Analyzing patterns...'}
              </div>
            </div>
          </>
        )}
      </div>

      <div className="glass-card" style={{ marginTop: '2rem', overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--accent-primary)' }}>
              <th style={{ padding: '1rem' }}>Student</th>
              <th>Branch/Year</th>
              <th>Issue</th>
              <th>Severity</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {records.map((r) => (
              <tr key={r.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <td style={{ padding: '1rem' }}>{r.student_name}</td>
                <td>{r.branch} - Year {r.year}</td>
                <td>{r.issue}</td>
                <td>
                  <span className={`status-badge status-${r.severity === 'high' || r.severity === 'critical' ? 'danger' : 'pending'}`}>
                    {r.severity}
                  </span>
                </td>
                <td>{r.treatment_status}</td>
                <td style={{ display: 'flex', gap: '0.5rem', padding: '1rem' }}>
                  <button onClick={() => toast('Calling parent...')} title="Call Parent"><FaPhone /></button>
                  <button onClick={() => {
                    setSelectedStudent(r);
                    setShowCabModal(true);
                  }} title="Search Cabs"><FaTaxi /></button>
                  <button onClick={() => handleDelete(r.id)} style={{ color: '#ff4d4d' }} title="Delete"><FaTrash /></button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showModal && (
        <div className="modal-overlay" style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.8)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
          <div className="glass-card" style={{ width: '500px', backgroundColor: '#12121a' }}>
            <h3>New Medical Record</h3>
            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: '1rem' }}>
              <input type="text" placeholder="Student Name" required onChange={e => setFormData({...formData, student_name: e.target.value})} className="form-input" />
              <div style={{ display: 'flex', gap: '1rem' }}>
                <input type="text" placeholder="Branch" required style={{ flex: 1 }} onChange={e => setFormData({...formData, branch: e.target.value})} />
                <input type="number" placeholder="Year" required style={{ width: '80px' }} onChange={e => setFormData({...formData, year: parseInt(e.target.value)})} />
              </div>
              <input type="text" placeholder="Issue / Symptoms" required onChange={e => setFormData({...formData, issue: e.target.value})} />
              <select onChange={e => setFormData({...formData, severity: e.target.value})}>
                <option value="low">Low Severity</option>
                <option value="medium">Medium Severity</option>
                <option value="high">High Severity</option>
                <option value="critical">Critical</option>
              </select>
              <input type="text" placeholder="Parent Contact" onChange={e => setFormData({...formData, parent_contact: e.target.value})} />
              <textarea placeholder="Destination Address (for automatic cab booking)" onChange={e => setFormData({...formData, address: e.target.value})} style={{ background: '#0a0a0f', border: '1px solid #333', padding: '0.8rem', borderRadius: '8px', color: 'white' }} />
              <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                <button type="submit" className="btn-primary" style={{ flex: 1 }}>Add Record</button>
                <button type="button" onClick={() => setShowModal(false)} style={{ background: 'transparent', color: 'white' }}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}
      {showCabModal && (
        <div className="modal-overlay" style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.85)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1100 }}>
          <div className="glass-card" style={{ width: '400px', backgroundColor: '#12121a', textAlign: 'center' }}>
            <div style={{ background: 'rgba(255,255,255,0.05)', padding: '1rem', borderRadius: '12px', marginBottom: '1.5rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                <span>Destination:</span>
                <span style={{ color: 'var(--accent-primary)', fontWeight: 500 }}>{selectedStudent?.address?.substring(0, 25)}...</span>
              </div>
              {calcLoading ? (
                <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Calculating estimates...</div>
              ) : estimates ? (
                <div style={{ display: 'flex', justifyContent: 'space-around', marginTop: '0.5rem' }}>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '0.75rem', opacity: 0.6 }}>Uber Min.</div>
                    <div style={{ color: '#fff', fontSize: '1.1rem', fontWeight: 'bold' }}>{estimates.uber}</div>
                  </div>
                  <div style={{ width: '1px', background: 'rgba(255,255,255,0.1)' }}></div>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '0.75rem', opacity: 0.6 }}>Ola Min.</div>
                    <div style={{ color: '#fff', fontSize: '1.1rem', fontWeight: 'bold' }}>{estimates.ola}</div>
                  </div>
                </div>
              ) : (
                <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Add address to see estimates</div>
              )}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <button className="btn-primary" onClick={() => handleCabSearch('Uber')} style={{ background: '#000', border: '1px solid #333' }}>Uber</button>
              <button className="btn-primary" onClick={() => handleCabSearch('Ola')} style={{ background: '#f5d414', color: '#000' }}>Ola</button>
              <button className="btn-primary" onClick={() => handleCabSearch('Rapido')} style={{ background: '#ffcc00', color: '#000' }}>Rapido</button>
              <button className="btn-primary" onClick={() => handleCabSearch('')} style={{ background: 'var(--card-bg)' }}>General</button>
            </div>
            
            <button onClick={() => setShowCabModal(false)} style={{ marginTop: '1.5rem', background: 'transparent', color: 'var(--text-secondary)', border: 'none', cursor: 'pointer' }}>Cancel</button>
          </div>
        </div>
      )}
    </div>
  );
};

export default Medical;
