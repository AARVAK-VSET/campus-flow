import React, { useState, useEffect, useRef } from 'react';
import api from '../api';
import toast from 'react-hot-toast';
import { FaMicrophone, FaStop, FaRobot, FaCheckCircle, FaTimes } from 'react-icons/fa';

interface VoiceAssistantProps {
  context: string;
  onComplete: (data: any) => void;
  onClose: () => void;
}

const VoiceAssistant: React.FC<VoiceAssistantProps> = ({ context, onComplete, onClose }) => {
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [currentData, setCurrentData] = useState<any>({});
  const [lastQuestion, setLastQuestion] = useState("Namaste! I am Arjun. Click start to begin.");
  const [transcript, setTranscript] = useState("");
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const startConversation = async () => {
    await processTurn("Hello Arjun, I want to add a record.");
  };

  const processTurn = async (input: string) => {
    try {
      setTranscript(input);
      setIsLoading(true);
      const res = await api.post('voice/process', {
        user_input: input,
        current_data: currentData,
        context: context
      });

      const { updated_data, next_question, is_complete, is_confirmed, audio_url } = res.data;
      
      setCurrentData(updated_data);
      setLastQuestion(next_question);
      setIsLoading(false);

      if (is_confirmed) {
        toast.success("Record confirmed! Saving...");
        onComplete(updated_data);
        return;
      }

      playArjunVoice(audio_url);

    } catch (err) {
      setIsLoading(false);
      toast.error("Communication error with Arjun.");
      console.error(err);
    }
  };

  const playArjunVoice = (url: string) => {
    // ... (playArjunVoice logic remains same)
    if (audioRef.current) {
      audioRef.current.pause();
    }
    const fullUrl = `http://localhost:8000${url}`;
    const audio = new Audio(fullUrl);
    audioRef.current = audio;
    
    audio.onplay = () => setIsSpeaking(true);
    audio.onended = () => {
      setIsSpeaking(false);
      startListening(); 
    };
    audio.onerror = () => {
      setIsSpeaking(false);
      toast.error("Failed to play Arjun's voice.");
    };
    audio.play().catch(e => {
      console.warn("Autoplay blocked or playback error", e);
      setIsSpeaking(false);
    });
  };

  const startListening = () => {
    // ... (startListening logic remains same)
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      toast.error("Speech recognition not supported.");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.continuous = false;

    recognition.onstart = () => setIsListening(true);
    recognition.onresult = (event: any) => {
      const text = event.results[0][0].transcript;
      setIsListening(false);
      processTurn(text);
    };
    recognition.onerror = (e: any) => {
      console.error("Speech recognition error", e);
      setIsListening(false);
    };
    recognition.onend = () => setIsListening(false);

    recognition.start();
  };

  return (
    <div className="voice-assistant-overlay" style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      background: 'rgba(0,0,0,0.9)', zIndex: 2000,
      display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center'
    }}>
      <div className="glass-card" style={{ width: '450px', padding: '3rem', textAlign: 'center', position: 'relative' }}>
        <button onClick={onClose} style={{ position: 'absolute', top: '1rem', right: '1rem', background: 'transparent', color: '#ff4d4d', border: 'none', fontSize: '1.2rem' }}>
          <FaTimes />
        </button>

        <div className={`arjun-avatar ${isSpeaking ? 'speaking' : ''} ${isListening ? 'listening' : ''} ${isLoading ? 'loading-ai' : ''}`} style={{
          width: '120px', height: '120px', borderRadius: '50%', background: 'linear-gradient(135deg, #00f2fe 0%, #4facfe 100%)',
          margin: '0 auto 2rem', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '3rem', color: 'white',
          boxShadow: isSpeaking ? '0 0 30px #4facfe' : (isListening ? '0 0 30px #ff4d4d' : '0 10px 20px rgba(0,0,0,0.3)'),
          transition: 'all 0.3s ease'
        }}>
          <FaRobot />
        </div>

        <h2 style={{ color: 'var(--accent-primary)', marginBottom: '0.5rem' }}>Arjun AI</h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1.5rem', fontStyle: 'italic' }}>
          Voice Assistant
        </p>

        <div style={{ minHeight: '80px', margin: '1rem 0', color: 'white', fontSize: '1.1rem', lineHeight: '1.5' }}>
          {isLoading ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', alignItems: 'center' }}>
               <span>Arjun is thinking...</span>
               <div className="thinking-dots"><span>.</span><span>.</span><span>.</span></div>
            </div>
          ) : lastQuestion}
        </div>

        {transcript && (
          <div style={{ color: 'var(--accent-primary)', fontSize: '0.85rem', marginTop: '1rem', opacity: 0.8 }}>
            " {transcript} "
          </div>
        )}

        <div style={{ marginTop: '2.5rem' }}>
          {!isSpeaking && !isListening && !isLoading && (
            <button className="btn-primary" onClick={startConversation} style={{ padding: '0.8rem 2rem' }}>
              START CALL
            </button>
          )}
          
          {isListening && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#ff4d4d', fontWeight: 'bold', justifyContent: 'center' }}>
              <div className="pulse" style={{ width: '10px', height: '10px', background: '#ff4d4d', borderRadius: '50%' }}></div>
              Listening...
            </div>
          )}

          {isLoading && (
            <div style={{ color: 'var(--accent-primary)', fontWeight: 'bold' }}>
              Processing...
            </div>
          )}
        </div>
      </div>

      <style>{`
        .speaking {
          animation: pulse-speaking 1s infinite alternate;
        }
        .listening {
          animation: pulse-listening 1s infinite alternate;
        }
        @keyframes pulse-speaking {
          from { transform: scale(1); box-shadow: 0 0 10px #4facfe; }
          to { transform: scale(1.1); box-shadow: 0 0 40px #4facfe; }
        }
        @keyframes pulse-listening {
          from { transform: scale(1); box-shadow: 0 0 10px #ff4d4d; }
          to { transform: scale(1.1); box-shadow: 0 0 40px #ff4d4d; }
        }
        .thinking-dots span {
          animation: dot-blink 1.4s infinite both;
          font-size: 1.5rem;
          margin: 0 2px;
        }
        .thinking-dots span:nth-child(2) { animation-delay: 0.2s; }
        .thinking-dots span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes dot-blink {
          0% { opacity: 0.2; }
          20% { opacity: 1; }
          100% { opacity: 0.2; }
        }
      `}</style>
    </div>
  );
};

export default VoiceAssistant;
