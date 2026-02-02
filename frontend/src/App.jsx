import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [status, setStatus] = useState('idle');
  const [mode, setMode] = useState('note');
  const [message, setMessage] = useState('');
  const [manualNote, setManualNote] = useState('');
  const [recording, setRecording] = useState(false);
  const [todayNotes, setTodayNotes] = useState('');
  const [notesCount, setNotesCount] = useState(0);
  const [keyPressed, setKeyPressed] = useState('');
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [summary, setSummary] = useState('');

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const streamRef = useRef(null);
  const spacebarPressedRef = useRef(false);

  // API base URL - use relative URL to leverage nginx proxy
  const API_BASE = '/api';

  // Initialize and get initial data
  useEffect(() => {
    fetchNotes();
    fetchStatus();
  }, []);

  // Set up keyboard listeners
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.code === 'Space' && !e.repeat && !spacebarPressedRef.current) {
        e.preventDefault();
        spacebarPressedRef.current = true;
        if (!recording) {
          startRecording();
        }
      } else if ((e.key === 'r' || e.key === 'R') && !recording) {
        e.preventDefault();
        startRecording();
      } else if ((e.key === 's' || e.key === 'S') && recording) {
        e.preventDefault();
        stopRecording();
      }
    };

    const handleKeyUp = (e) => {
      if (e.code === 'Space') {
        e.preventDefault();
        if (spacebarPressedRef.current && recording) {
          spacebarPressedRef.current = false;
          stopRecording();
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    document.addEventListener('keyup', handleKeyUp);

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('keyup', handleKeyUp);
    };
  }, [recording]);

  const startRecording = async () => {
    try {
      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      // Create MediaRecorder
      const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      // Collect audio data
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      // Start recording
      mediaRecorder.start();
      setRecording(true);
      setMessage('Recording...');
      setStatus('recording');

    } catch (error) {
      console.error('Error accessing microphone:', error);
      setMessage('Error: Could not access microphone. Please grant permission.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && recording) {
      mediaRecorderRef.current.onstop = async () => {
        setMessage('Processing...');

        // Create audio blob
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });

        // Stop all tracks
        if (streamRef.current) {
          streamRef.current.getTracks().forEach(track => track.stop());
        }

        // Send to backend
        await uploadAudio(audioBlob);
      };

      mediaRecorderRef.current.stop();
      setRecording(false);
    }
  };

  const uploadAudio = async (audioBlob) => {
    try {
      const formData = new FormData();
      formData.append('audio', audioBlob, 'recording.webm');

      const response = await axios.post(`${API_BASE}/upload-audio`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.data.status === 'noted') {
        setMessage('✅ NOTED!');
        setStatus('noted');
        setTimeout(() => {
          setStatus('idle');
          setMessage('');
        }, 2000);
        fetchNotes();
      } else {
        setMessage(response.data.message || 'Error processing audio');
        setStatus('error');
      }

    } catch (error) {
      console.error('Error uploading audio:', error);
      setMessage('Error: Failed to process audio');
      setStatus('error');
    }
  };

  const fetchNotes = async () => {
    try {
      const response = await axios.get(`${API_BASE}/notes`);
      setTodayNotes(response.data.notes || '');
      fetchStatus();
    } catch (error) {
      console.error('Error fetching notes:', error);
    }
  };

  const fetchStatus = async () => {
    try {
      const response = await axios.get(`${API_BASE}/status`);
      setNotesCount(response.data.notes_count || 0);
      setMode(response.data.note_mode ? 'note' : 'assistant');
    } catch (error) {
      console.error('Error fetching status:', error);
    }
  };

  const switchMode = async (newMode) => {
    try {
      await axios.post(`${API_BASE}/mode`, { action: newMode });
      setMode(newMode);
      setMessage(`Switched to ${newMode === 'note' ? 'Note' : 'Assistant'} mode`);
    } catch (error) {
      console.error('Error switching mode:', error);
    }
  };

  const addManualNote = async () => {
    if (manualNote.trim()) {
      try {
        await axios.post(`${API_BASE}/manual-note`, { text: manualNote });
        setMessage('Note added successfully!');
        setManualNote('');
        fetchNotes();
      } catch (error) {
        console.error('Error adding manual note:', error);
      }
    }
  };

  const readTodaysNotes = async () => {
    try {
      setMessage('Summarizing your notes...');
      setIsSpeaking(true);

      // Call backend to get summary from Ollama
      const response = await axios.get(`${API_BASE}/summarize-notes`);

      if (response.data.status === 'success') {
        const summaryText = response.data.summary;
        setSummary(summaryText);
        setMessage('Reading summary...');

        // Use Web Speech API to speak the summary
        const utterance = new SpeechSynthesisUtterance(summaryText);
        utterance.rate = 0.9; // Slightly slower for clarity
        utterance.pitch = 1.0;
        utterance.volume = 1.0;

        utterance.onend = () => {
          setIsSpeaking(false);
          setMessage('');
        };

        utterance.onerror = (event) => {
          console.error('Speech synthesis error:', event);
          setIsSpeaking(false);
          setMessage('Error reading summary');
        };

        window.speechSynthesis.speak(utterance);
      } else {
        setMessage(response.data.message || 'No notes to summarize');
        setIsSpeaking(false);
      }
    } catch (error) {
      console.error('Error reading notes:', error);
      setMessage('Error: Could not summarize notes');
      setIsSpeaking(false);
    }
  };

  const stopSpeaking = () => {
    window.speechSynthesis.cancel();
    setIsSpeaking(false);
    setMessage('');
  };

  const formatTodayNotes = (notesText) => {
    if (!notesText) return 'No notes today yet.';

    return notesText.split('\n').map((line, index) => {
      if (line.startsWith('- **')) {
        return (
          <div key={index} style={{
            backgroundColor: '#2a2a2a',
            padding: '10px',
            margin: '5px 0',
            borderRadius: '5px',
            borderLeft: '4px solid #4a90e2'
          }}>
            <span style={{ color: '#4a90e2' }}>{line}</span>
          </div>
        );
      }
      return <div key={index}>{line}</div>;
    });
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>🎙️ Listeny - Voice Notes</h1>
        <div className="mode-indicator">
          <span className={mode === 'note' ? 'note-mode' : 'assistant-mode'}>
            {mode === 'note' ? '📝 Note Mode (Direct)' : '🤖 Assistant Mode (Commands)'}
          </span>
        </div>
      </header>

      <div className="keyboard-hint">
        ⌨️ KEYBOARD: SPACEBAR=Toggle | R=Record | S=Stop
        {keyPressed && (
          <div className="key-feedback">
            🎹 Key: {keyPressed}
          </div>
        )}
      </div>

      <main className="App-main">
        <div className="recording-section">
          <button
            className={`record-button ${recording ? 'recording' : ''}`}
            onClick={recording ? stopRecording : startRecording}
          >
            {recording ? '🔴 STOP RECORDING' : '🎙️ RECORD'}
          </button>
        </div>

        <div className="status-section">
          <h3>Status</h3>
          {status === 'noted' ? (
            <div className="noted-message">
              ✅ NOTED!
            </div>
          ) : recording ? (
            <div className="listening">
              <h3>🎙️ RECORDING...</h3>
              <div className="wave-container">
                <span className="wave">🌊</span>
                <span className="wave" style={{animationDelay: '0.2s'}}>🌊</span>
                <span className="wave" style={{animationDelay: '0.4s'}}>🌊</span>
              </div>
              <p><em>Click STOP or release SPACEBAR</em></p>
            </div>
          ) : (
            <div className="status-box">
              {message || 'Ready to record'}
            </div>
          )}
        </div>

        <section className="instructions-section">
          <h2>📖 How to Use</h2>
          {mode === 'note' ? (
            <div className="instructions">
              <h4>📝 Note Mode (Push-to-Talk)</h4>

              <h5>⌨️ SPACEBAR (Recommended)</h5>
              <ol>
                <li><strong>Press SPACEBAR</strong> → Recording starts</li>
                <li><strong>Speak your note</strong> → "meeting with team at 3pm"</li>
                <li><strong>Release SPACEBAR</strong> → Recording stops</li>
                <li><strong>✅ NOTED!</strong> → Note saved automatically</li>
              </ol>

              <h5>🖱️ Alternative Keys</h5>
              <p><strong>R</strong> to start, <strong>S</strong> to stop</p>

              <h5>🖱️ Mouse Method</h5>
              <ol>
                <li><strong>Click RECORD</strong> → Recording starts</li>
                <li><strong>Speak your note</strong> → Clear speech</li>
                <li><strong>Click STOP</strong> → Recording stops</li>
                <li><strong>✅ NOTED!</strong> → Success message</li>
              </ol>
            </div>
          ) : (
            <div className="instructions">
              <h4>🤖 Assistant Mode</h4>
              <p><strong>Commands work like:</strong></p>
              <ul>
                <li>"Note this: meeting with team at 3pm"</li>
                <li>"Remember that I need to review the PR"</li>
                <li>"Take a note: call client tomorrow"</li>
              </ul>
              <p>Use SPACEBAR or R/S keys to record your command.</p>
            </div>
          )}
        </section>

        <section className="controls-section">
          <h2>⚙️ Controls</h2>
          <div className="mode-buttons">
            <button
              className={mode === 'note' ? 'active' : ''}
              onClick={() => switchMode('note')}
            >
              📝 Note Mode
            </button>
            <button
              className={mode === 'assistant' ? 'active' : ''}
              onClick={() => switchMode('assistant')}
            >
              🤖 Assistant Mode
            </button>
          </div>
        </section>

        <section className="notes-section">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h2>📝 Today's Notes ({notesCount})</h2>
            <button
              onClick={isSpeaking ? stopSpeaking : readTodaysNotes}
              disabled={notesCount === 0 && !isSpeaking}
              style={{
                padding: '10px 20px',
                fontSize: '16px',
                backgroundColor: isSpeaking ? '#e74c3c' : '#3498db',
                color: 'white',
                border: 'none',
                borderRadius: '5px',
                cursor: notesCount === 0 && !isSpeaking ? 'not-allowed' : 'pointer',
                opacity: notesCount === 0 && !isSpeaking ? 0.5 : 1
              }}
            >
              {isSpeaking ? '🔇 Stop Reading' : '🔊 Read Today\'s Notes'}
            </button>
          </div>

          {summary && (
            <div style={{
              backgroundColor: '#2c3e50',
              padding: '15px',
              marginBottom: '15px',
              borderRadius: '8px',
              borderLeft: '4px solid #3498db'
            }}>
              <h3 style={{ color: '#3498db', marginTop: 0 }}>📋 Summary:</h3>
              <p style={{ margin: 0, lineHeight: '1.6' }}>{summary}</p>
            </div>
          )}

          <div className="notes-container">
            {formatTodayNotes(todayNotes)}
          </div>

          <div className="manual-note-section">
            <h3>✍️ Add Note Manually</h3>
            <textarea
              value={manualNote}
              onChange={(e) => setManualNote(e.target.value)}
              placeholder="Enter your note here..."
              rows={3}
            />
            <button onClick={addManualNote}>
              Add Note
            </button>
          </div>
        </section>

        <footer className="App-footer">
          <div className="server-info">
            <h3>🌐 Server Info</h3>
            <p><strong>Local:</strong> http://localhost:3000</p>
            <p><strong>API:</strong> http://localhost:8000</p>
            <p><strong>Network:</strong> http://YOUR_LAPTOP_IP:3000</p>
            <p><strong>Notes:</strong> Saved in backend/notes/ folder</p>
          </div>
        </footer>
      </main>
    </div>
  );
}

export default App;
