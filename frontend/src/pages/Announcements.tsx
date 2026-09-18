import React, { useState, useEffect } from 'react';
import api from '../api';
import toast from 'react-hot-toast';
import { FaPlay, FaTrash, FaVolumeUp } from 'react-icons/fa';

const Announcements = () => {
  const [announcements, setAnnouncements] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');
  const [language, setLanguage] = useState('en');
  const [repeat, setRepeat] = useState(0);

  const languages = [
    { code: 'en', name: 'English' },
    { code: 'hi', name: 'Hindi' },
    { code: 'es', name: 'Spanish' },
    { code: 'fr', name: 'French' },
    { code: 'de', name: 'German' },
    { code: 'ja', name: 'Japanese' },
    { code: 'zh', name: 'Chinese' },
    { code: 'ko', name: 'Korean' },
  ];

  const fetchAnnouncements = async () => {
    setLoading(true);
    try {
      const res = await api.get('announcements/');
      setAnnouncements(res.data);
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message;
      toast.error('Failed to fetch announcements: ' + msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnnouncements();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('announcements/', { message, language, repeat_interval: repeat });
      toast.success('Announcement scheduled');
      setMessage('');
      fetchAnnouncements();
    } catch (err) {
      toast.error('Failed to schedule announcement');
    }
  };

  const handleSpeak = async (id: number) => {
    try {
      toast.loading('Synthesizing speech...', { id: 'tts' });
      const res = await api.post(`announcements/${id}/speak`, {}, { responseType: 'blob' });
      const audioUrl = URL.createObjectURL(res.data);
      const audio = new Audio(audioUrl);
      audio.play();
      toast.success('Playing announcement', { id: 'tts' });
    } catch (err) {
      toast.error('Failed to generate speech');
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await api.delete(`announcements/${id}`);
      toast.success('Announcement removed');
      fetchAnnouncements();
    } catch (err) {
      toast.error('Failed to delete');
    }
  };

  return (
    <div className="announcements-page">
      <h2>Multilingual AI Voice Agent</h2>
      
      <div className="grid-dashboard" style={{ marginTop: '2rem' }}>
        <div className="glass-card">
          <h3 style={{ marginBottom: '1.5rem' }}>Create Message</h3>
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <textarea
              placeholder="Enter your announcement message..."
              required
              style={{ height: '120px', background: 'var(--bg-primary)', color: '#fff', border: '1px solid #333', padding: '1rem' }}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
            />
            <div style={{ display: 'flex', gap: '1rem' }}>
              <select style={{ flex: 1 }} value={language} onChange={(e) => setLanguage(e.target.value)}>
                {languages.map(l => <option key={l.code} value={l.code}>{l.name}</option>)}
              </select>
              <select style={{ width: '150px' }} value={repeat} onChange={(e) => setRepeat(parseInt(e.target.value))}>
                <option value={0}>No Repeat</option>
                <option value={300}>Every 5m</option>
                <option value={3600}>Every 1h</option>
              </select>
            </div>
            <button type="submit" className="btn-primary">
              <FaVolumeUp /> Schedule Announcement
            </button>
          </form>
        </div>

        <div className="glass-card" style={{ display: 'flex', flexDirection: 'column' }}>
          <h3 style={{ marginBottom: '1.5rem' }}>Active Schedule</h3>
          {loading ? <div>Loading...</div> : (
            <div style={{ flex: 1, overflowY: 'auto', maxHeight: '300px' }}>
              {announcements.length === 0 ? <p style={{ color: 'var(--text-secondary)' }}>No active announcements</p> : (
                announcements.map((a) => (
                  <div key={a.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '1rem 0', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                    <div>
                      <div style={{ fontWeight: '700' }}>{a.message}</div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--accent-primary)' }}>
                        {languages.find(l => l.code === a.language)?.name} • {a.repeat_interval > 0 ? `Repeats every ${a.repeat_interval / 60}m` : 'Once'}
                      </div>
                    </div>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      <button onClick={() => handleSpeak(a.id)} style={{ color: 'var(--accent-primary)' }}><FaPlay /></button>
                      <button onClick={() => handleDelete(a.id)} style={{ color: '#ff4d4d' }}><FaTrash /></button>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Announcements;
