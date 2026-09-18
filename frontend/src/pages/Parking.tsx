import React, { useState, useEffect, useRef } from 'react';
import api from '../api';
import ChartCard from '../components/ChartCard';
import toast from 'react-hot-toast';
import { FaCar, FaPlus, FaCheck, FaHistory, FaCamera, FaRobot, FaSearch } from 'react-icons/fa';

const Parking = () => {
  const [records, setRecords] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [insights, setInsights] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [detecting, setDetecting] = useState(false);
  const [carNumber, setCarNumber] = useState('');
  const [slotNumber, setSlotNumber] = useState(1);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchData = async () => {
    try {
      const [resRecords, resDashboard] = await Promise.all([
        api.get('parking/'),
        api.get('parking/analytics'),
      ]);
      setRecords(resRecords.data);
      setStats(resDashboard.data.stats);
      setInsights(resDashboard.data.insights);
    } catch (err) {
      toast.error('Failed to fetch parking data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleEntry = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('parking/', { car_number: carNumber, slot_number: slotNumber });
      toast.success('Car registered successfully');
      setCarNumber('');
      fetchData();
    } catch (err) {
      toast.error('Failed to register entry');
    }
  };

  const handleCheckout = async (id: number) => {
    try {
      await api.put(`parking/${id}`, { status: 'free', time_out: new Date().toISOString() });
      toast.success('Checkout confirmed');
      fetchData();
    } catch (err) {
      toast.error('Checkout failed');
    }
  };

  const handleAIDetect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('image', file);

    setDetecting(true);
    const toastId = toast.loading('AI processing live image...');
    
    try {
      const res = await api.post('parking/detect', formData);
      toast.success(`AI Scan Complete. ${res.data.slots.filter((s:any) => s.status === 'free').length} slots free.`, { id: toastId });
      
      // Auto-register detected occupied slots if not already in records
      // (Simplified: just show the result analysis)
      setInsights(`AI detection complete at ${new Date().toLocaleTimeString()}.\nAnalysis Confidence: ${res.data.confidence * 100}%\nTotal Capacity: 10\nOccupied: ${res.data.slots.filter((s:any) => s.status === 'occupied').length}\nFree: ${res.data.slots.filter((s:any) => s.status === 'free').length}`);
      
    } catch (err) {
      toast.error('AI Processing Failed', { id: toastId });
    } finally {
      setDetecting(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  if (loading) return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '60vh' }}>
      <div className="loader" style={{ border: '4px solid var(--accent-primary)', borderTop: '4px solid transparent', borderRadius: '50%', width: '40px', height: '40px', animation: 'spin 1s linear infinite' }}></div>
      <p style={{ marginTop: '1rem', color: 'var(--accent-primary)' }}>Calibrating Parking Sensors...</p>
    </div>
  );

  return (
    <div className="parking-page" style={{ animation: 'fadeIn 0.5s ease' }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h2><FaRobot style={{ marginRight: '1rem', color: 'var(--accent-primary)' }} />Parking Intelligence</h2>
        <div style={{ display: 'flex', gap: '1rem' }}>
           <input type="file" ref={fileInputRef} hidden accept="image/*" onChange={handleAIDetect} />
           <button onClick={() => fileInputRef.current?.click()} className="btn-primary" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
             <FaCamera /> AI SCAN LIVE
           </button>
        </div>
      </header>

      <div className="grid-dashboard">
        <div className="glass-card" style={{ borderLeft: '4px solid var(--accent-primary)' }}>
          <h3 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <FaPlus size={16} /> Register Entry
          </h3>
          <form onSubmit={handleEntry} style={{ display: 'flex', flexDirection: 'column', gap: '1.2rem' }}>
            <div style={{ position: 'relative' }}>
              <FaCar style={{ position: 'absolute', left: '1rem', top: '1.1rem', opacity: 0.5 }} />
              <input 
                type="text" 
                placeholder="Car Number (e.g. MH12AB1234)" 
                required 
                style={{ paddingLeft: '3rem', width: '100%', background: 'rgba(0,0,0,0.3)' }}
                value={carNumber} 
                onChange={e => setCarNumber(e.target.value)} 
              />
            </div>
            <div style={{ display: 'flex', gap: '1rem' }}>
              <select style={{ flex: 1, padding: '0.8rem', background: 'rgba(0,0,0,0.3)', color: '#fff' }} value={slotNumber} onChange={e => setSlotNumber(parseInt(e.target.value))}>
                {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(s => <option key={s} value={s} style={{ background: '#12121a' }}>Slot #{s}</option>)}
              </select>
              <button type="submit" className="btn-primary" style={{ flex: 1 }}>Check In</button>
            </div>
          </form>

          <div style={{ marginTop: '2.5rem' }}>
            <h3 style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '1.2rem', textTransform: 'uppercase' }}>
               Interactive Parking Map
            </h3>
            <div style={{ 
              display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '0.8rem',
              padding: '1.5rem', background: 'rgba(0,0,0,0.2)', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.05)'
            }}>
              {[1, 2, 3, 4, 10, 9, 8, 7, 6, 5].sort((a,b) => a-b).map(s => {
                const record = records.find(r => r.slot_number === s && r.status === 'occupied');
                const isOccupied = !!record;
                return (
                  <div key={s} 
                    title={isOccupied ? `Occupied by ${record.car_number}` : 'Available'}
                    style={{ 
                      aspectRatio: '1', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', borderRadius: '8px',
                      backgroundColor: isOccupied ? 'rgba(255, 77, 77, 0.15)' : 'rgba(0, 242, 255, 0.05)',
                      border: `2px solid ${isOccupied ? '#ff4d4d' : 'var(--accent-primary)'}`,
                      color: isOccupied ? '#ff4d4d' : 'var(--accent-primary)',
                      position: 'relative', transition: 'all 0.3s ease', cursor: 'default'
                    }}>
                    <span style={{ fontSize: '0.6rem', position: 'absolute', top: '5px', left: '5px' }}>#{s}</span>
                    {isOccupied ? <FaCar size={24} style={{ marginBottom: '2px' }} /> : <FaCheck size={18} style={{ opacity: 0.3 }} />}
                    <div style={{ fontSize: '0.5rem', fontWeight: 'bold' }}>{isOccupied ? 'FULL' : 'FREE'}</div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          {stats && (
            <ChartCard title="Occupancy Demand Trend" type="area" data={stats.hourly} dataKey="count" nameKey="hour" color="var(--accent-primary)" />
          )}
          
          <div className="glass-card" style={{ borderLeft: '4px solid var(--accent-secondary)' }}>
             <h3 style={{ marginBottom: '1rem', color: 'var(--accent-secondary)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
               <FaSearch size={16} /> AI Insight Report
             </h3>
             <div style={{ 
               padding: '1rem', background: 'rgba(0,0,0,0.2)', borderRadius: '8px',
               color: 'var(--text-secondary)', lineHeight: '1.6', fontSize: '0.9rem', whiteSpace: 'pre-wrap', minHeight: '100px'
             }}>
                {insights || 'Calibrating prediction engine based on current occupancy metrics...'}
             </div>
          </div>
        </div>
      </div>

      <div className="glass-card" style={{ marginTop: '2rem', overflow: 'hidden' }}>
        <h3 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <FaHistory /> Intelligence Logs
        </h3>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--accent-primary)', fontSize: '0.85rem' }}>
                <th style={{ padding: '1rem' }}>Car ID</th>
                <th>Bay #</th>
                <th>Check In</th>
                <th>Check Out</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody style={{ fontSize: '0.9rem' }}>
              {records.length === 0 ? (
                <tr><td colSpan={6} style={{ textAlign: 'center', padding: '2rem', opacity: 0.3 }}>No active records in logs.</td></tr>
              ) : records.map((r) => (
                <tr key={r.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)', transition: 'background 0.2s' }} className="table-row">
                  <td style={{ padding: '1rem', fontWeight: 600 }}>{r.car_number}</td>
                  <td>Bay #{r.slot_number}</td>
                  <td>{new Date(r.time_in).toLocaleTimeString()}</td>
                  <td>{r.time_out ? new Date(r.time_out).toLocaleTimeString() : '---'}</td>
                  <td>
                    <span className={`status-badge status-${r.status === 'occupied' ? 'danger' : 'success'}`}>
                      {r.status}
                    </span>
                  </td>
                  <td style={{ padding: '1rem' }}>
                    {r.status === 'occupied' && (
                      <button 
                        onClick={() => handleCheckout(r.id)} 
                        className="btn-primary" 
                        style={{ padding: '0.4rem 0.8rem', fontSize: '0.75rem', background: 'rgba(0, 255, 0, 0.1)', color: '#00ff00', border: '1px solid #00ff00' }}
                      >
                         Release Bay
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <style>{`
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        .table-row:hover { background: rgba(255,255,255,0.02); }
      `}</style>
    </div>
  );
};

export default Parking;
