import React, { useState } from 'react';
import { FaMicrophone, FaStop } from 'react-icons/fa';
import toast from 'react-hot-toast';

interface VoiceButtonProps {
  onResult: (text: string) => void;
  lang?: string;
}

const VoiceButton: React.FC<VoiceButtonProps> = ({ onResult, lang = 'en-US' }) => {
  const [isListening, setIsListening] = useState(false);

  const startListening = () => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      toast.error('Web Speech API is not supported in your browser.');
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = lang;
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onstart = () => {
      setIsListening(true);
      toast('Listening...', { icon: '🎙️' });
    };

    recognition.onresult = (event: any) => {
      const text = event.results[0][0].transcript;
      onResult(text);
      setIsListening(false);
    };

    recognition.onerror = (event: any) => {
      console.error(event.error);
      setIsListening(false);
      toast.error('Voice recognition error.');
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognition.start();
  };

  return (
    <button
      className="btn-primary"
      onClick={startListening}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '0.5rem',
        background: isListening ? '#ff4d4d' : 'var(--accent-primary)',
        padding: '0.5rem 1rem',
        fontSize: '0.9rem',
      }}
    >
      {isListening ? <FaStop /> : <FaMicrophone />}
      {isListening ? 'Listening...' : 'Record Voice Command'}
    </button>
  );
};

export default VoiceButton;
