import React, { useState, useEffect } from 'react';
import api from '../api';
import VoiceButton from '../components/VoiceButton';
import ChartCard from '../components/ChartCard';
import toast from 'react-hot-toast';
import { FaPlus, FaTrash, FaFileAlt, FaDownload } from 'react-icons/fa';

const Stationery = () => {
  const [items, setItems] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [insights, setInsights] = useState<string>('');
  const [proposal, setProposal] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [showProposal, setShowProposal] = useState(false);
  const [formData, setFormData] = useState({
    item_name: '',
    price: 0,
    quantity: 0,
    category: '',
    student_demand: 0,
  });

  const fetchData = async () => {
    setLoading(true);
    try {
      // 1. Fetch Items (Priority)
      const resItems = await api.get('stationery/');
      setItems(resItems.data);
      
      // 2. Fetch Analytics (Non-blocking)
      try {
        const resDashboard = await api.get('stationery/analytics');
        setStats(resDashboard.data.stats);
        setInsights(resDashboard.data.insights);
      } catch (analyticsErr: any) {
        console.warn('Stationery analytics failed', analyticsErr);
        toast.error('Inventory analytics unavailable');
      }
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message;
      toast.error('Failed to fetch stationery: ' + msg);
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
      await api.post('stationery/', formData);
      toast.success('Item added');
      setShowModal(false);
      fetchData();
    } catch (err) {
      toast.error('Failed to add item');
    }
  };

  const handleMakeProposal = async () => {
    try {
      toast.loading('Generating AI Proposal...', { id: 'proposal' });
      const res = await api.post('stationery/proposal');
      setProposal(res.data.proposal);
      setShowProposal(true);
      toast.success('Proposal ready!', { id: 'proposal' });
    } catch (err) {
      toast.error('Failed to generate proposal');
    }
  };

  const downloadProposal = () => {
    const element = document.createElement("a");
    const file = new Blob([proposal], {type: 'text/plain'});
    element.href = URL.createObjectURL(file);
    element.download = "procurement_proposal.md";
    document.body.appendChild(element);
    element.click();
  };

  if (loading) return <div style={{ textAlign: 'center', padding: '5rem' }}>Loading Store Dashboard...</div>;

  return (
    <div className="stationery-page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h2>Stationery Store Inventory</h2>
        <div style={{ display: 'flex', gap: '1rem' }}>
          <VoiceButton onResult={(text) => toast.success('Voice parsed: ' + text)} />
          <button className="btn-primary" onClick={handleMakeProposal}>
            <FaFileAlt /> Make Proposal
          </button>
          <button className="btn-primary" onClick={() => setShowModal(true)}>
            <FaPlus /> Add Item
          </button>
        </div>
      </div>

      <div className="grid-dashboard">
        {stats && (
          <>
            <ChartCard title="Top Items by Demand" type="bar" data={stats.top_demand} dataKey="demand" />
            <ChartCard title="Inventory by Category" type="pie" data={stats.by_category} dataKey="count" color="#ff00ff" />
            <div className="glass-card">
              <h3 style={{ marginBottom: '1rem' }}>Market Forecast</h3>
              <div style={{ color: 'var(--text-secondary)', lineHeight: '1.6', fontSize: '0.95rem', whiteSpace: 'pre-wrap' }}>
                {insights || 'Analyzing demand trends...'}
              </div>
            </div>
          </>
        )}
      </div>

      <div className="glass-card" style={{ marginTop: '2rem', overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border-color)', color: '#ff00ff' }}>
              <th style={{ padding: '1rem' }}>Item Name</th>
              <th>Price</th>
              <th>Stock</th>
              <th>Demand Score</th>
              <th>Category</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {items.map((i) => (
              <tr key={i.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <td style={{ padding: '1rem' }}>{i.item_name}</td>
                <td>${i.price}</td>
                <td style={{ color: i.quantity < 10 ? '#ff4d4d' : 'inherit' }}>{i.quantity}</td>
                <td>{i.student_demand}</td>
                <td>{i.category}</td>
                <td style={{ padding: '1rem' }}>
                  <button onClick={async () => { await api.delete(`stationery/${i.id}`); fetchData(); }} style={{ color: '#ff4d4d' }}><FaTrash /></button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showProposal && (
        <div className="modal-overlay" style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.85)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
          <div className="glass-card" style={{ width: '800px', maxHeight: '90vh', overflowY: 'auto', backgroundColor: '#12121a', position: 'relative' }}>
            <button 
              onClick={() => setShowProposal(false)}
              style={{ position: 'absolute', top: '1rem', right: '1rem', background: 'transparent', border: 'none', color: '#666', fontSize: '1.5rem', cursor: 'pointer', zIndex: 10 }}
              title="Close"
            >
              &times;
            </button>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1.5rem', paddingRight: '2rem' }}>
              <h3>AI Procurement Proposal</h3>
              <button onClick={downloadProposal} className="btn-primary" style={{ padding: '0.4rem 1rem', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <FaDownload /> Export MD
              </button>
            </div>
            <textarea
              style={{ width: '100%', height: '450px', background: '#0a0a0f', color: '#fff', border: '1px solid #333', padding: '1rem', fontFamily: 'monospace', borderRadius: '8px' }}
              value={proposal}
              onChange={(e) => setProposal(e.target.value)}
            />
            <div style={{ marginTop: '1.5rem', textAlign: 'right', display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
              <button onClick={() => setShowProposal(false)} className="btn-primary" style={{ background: 'transparent', border: '1px solid #333' }}>Discard</button>
              <button onClick={() => { downloadProposal(); setShowProposal(false); }} className="btn-primary">Export & Close</button>
            </div>
          </div>
        </div>
      )}

      {showModal && (
        <div className="modal-overlay" style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.8)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
          <div className="glass-card" style={{ width: '400px', backgroundColor: '#12121a' }}>
            <h3>Add New Item</h3>
            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: '1rem' }}>
              <input type="text" placeholder="Item Name" required onChange={e => setFormData({...formData, item_name: e.target.value})} />
              <input type="number" step="0.01" placeholder="Price" required onChange={e => setFormData({...formData, price: parseFloat(e.target.value)})} />
              <input type="number" placeholder="Quantity" required onChange={e => setFormData({...formData, quantity: parseInt(e.target.value)})} />
              <input type="text" placeholder="Category" onChange={e => setFormData({...formData, category: e.target.value})} />
              <input type="number" placeholder="Demand Score" onChange={e => setFormData({...formData, student_demand: parseInt(e.target.value)})} />
              <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                <button type="submit" className="btn-primary" style={{ flex: 1 }}>Add Item</button>
                <button type="button" onClick={() => setShowModal(false)} style={{ background: 'transparent', color: 'white' }}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Stationery;
