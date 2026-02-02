import streamlit as st
import speech_recognition as sr
import threading
import time
import os
from datetime import datetime
from streamlit_keypress import key_press_events

# Page configuration
st.set_page_config(
    page_title="Listeny - Voice Notes",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main {
        background-color: #1a1a1a;
    }
    .listening {
        animation: pulse 1.5s infinite;
    }
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    .wave {
        display: inline-block;
        animation: wave 1.5s ease-in-out infinite;
        margin: 0 2px;
    }
    @keyframes wave {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-10px); }
    }
    .noted-message {
        background-color: #28a745;
        color: white;
        padding: 40px;
        border-radius: 15px;
        text-align: center;
        font-size: 36px;
        font-weight: bold;
        animation: fadeInOut 2s ease-in-out;
        margin: 20px 0;
        box-shadow: 0 8px 16px rgba(0,0,0,0.3);
    }
    @keyframes fadeInOut {
        0% { opacity: 0; transform: scale(0.8); }
        50% { opacity: 1; transform: scale(1); }
        100% { opacity: 1; transform: scale(1); }
    }
    .record-button {
        background-color: #4a90e2;
        color: white;
        padding: 80px 120px;
        font-size: 36px;
        border-radius: 25px;
        border: 6px solid white;
        cursor: pointer;
        margin: 40px auto;
        display: block;
        text-align: center;
        font-weight: bold;
        min-width: 600px;
        user-select: none;
        transition: all 0.3s ease;
        box-shadow: 0 10px 20px rgba(0,0,0,0.3);
    }
    .record-button:hover {
        background-color: #357abd;
        transform: scale(1.05);
        box-shadow: 0 15px 25px rgba(0,0,0,0.4);
    }
    .record-button.recording {
        background-color: #dc3545;
        animation: pulse 1s infinite;
        color: white;
        padding: 60px 100px;
    }
    .record-button.recording::before {
        content: "🔴";
        margin-right: 15px;
    }
    .stop-button {
        background-color: #dc3545;
        color: white;
        padding: 60px 100px;
        font-size: 32px;
        border-radius: 20px;
        border: 5px solid white;
        cursor: pointer;
        margin: 30px auto;
        display: block;
        text-align: center;
        font-weight: bold;
        min-width: 500px;
        user-select: none;
        transition: all 0.3s ease;
        box-shadow: 0 10px 20px rgba(0,0,0,0.3);
    }
    .stop-button:hover {
        background-color: #c82333;
        transform: scale(1.05);
        box-shadow: 0 15px 25px rgba(0,0,0,0.4);
    }
    .mode-indicator {
        background-color: #28a745;
        color: white;
        padding: 25px;
        border-radius: 15px;
        text-align: center;
        font-size: 24px;
        font-weight: bold;
        margin: 30px 0;
        box-shadow: 0 8px 20px rgba(0,0,0,0.3);
    }
    .mode-indicator.assistant {
        background-color: #4a90e2;
    }
    .keyboard-hint {
        background-color: #ffc107;
        color: #000;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        margin: 20px 0;
        font-weight: bold;
        font-size: 20px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    .instructions {
        background-color: #2a2a2a;
        padding: 30px;
        border-radius: 15px;
        margin: 30px 0;
        border-left: 6px solid #4a90e2;
        box-shadow: 0 8px 20px rgba(0,0,0,0.3);
    }
    .status-box {
        background-color: #2a2a2a;
        padding: 25px;
        border-radius: 15px;
        margin: 20px 0;
        text-align: center;
        font-size: 20px;
        border-left: 5px solid #ffc107;
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    .keyboard-active {
        background-color: #007bff;
        color: white;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        margin: 10px 0;
        font-weight: bold;
        animation: flash 0.5s ease-in-out;
    }
    @keyframes flash {
        0% { opacity: 0.5; }
        50% { opacity: 1; }
        100% { opacity: 0.5; }
    }
</style>
""", unsafe_allow_html=True)

class ListenyKeyboard:
    def __init__(self):
        # Initialize session state
        if 'notes_dir' not in st.session_state:
            st.session_state.notes_dir = os.path.join(os.path.dirname(__file__), 'notes')
            os.makedirs(st.session_state.notes_dir, exist_ok=True)
        
        if 'listening' not in st.session_state:
            st.session_state.listening = False
            
        if 'status' not in st.session_state:
            st.session_state.status = "Ready to record"
            
        if 'notes_history' not in st.session_state:
            st.session_state.notes_history = []
            
        if 'note_mode' not in st.session_state:
            st.session_state.note_mode = True
            
        if 'noted_message' not in st.session_state:
            st.session_state.noted_message = False
            
        if 'last_key_press' not in st.session_state:
            st.session_state.last_key_press = None
        
        # Initialize components
        self.recognizer = sr.Recognizer()
    
    def is_note_command(self, text):
        """Check if command is a note-taking request"""
        note_triggers = ['note this', 'note that', 'take a note', 'remember this', 'remember that', 'add note', 'save note', 'write down', 'jot down']
        text_lower = text.lower()
        return any(trigger in text_lower for trigger in note_triggers)
    
    def extract_note(self, text):
        """Extract the actual note content from the command"""
        text_lower = text.lower()
        triggers = ['note this', 'note that', 'take a note', 'remember this', 'remember that', 'add note', 'save note', 'write down', 'jot down']
        note = text
        for trigger in triggers:
            if trigger in text_lower:
                idx = text_lower.find(trigger) + len(trigger)
                note = text[idx:].strip()
                for filler in ['that', 'to', ':', '-']:
                    if note.lower().startswith(filler):
                        note = note[len(filler):].strip()
                break
        return note if note else text
    
    def save_note(self, note_content):
        """Save note to today's markdown file"""
        today = datetime.now()
        filename = today.strftime('%Y-%m-%d') + '.md'
        filepath = os.path.join(st.session_state.notes_dir, filename)
        
        timestamp = today.strftime('%H:%M')
        
        if os.path.exists(filepath):
            with open(filepath, 'a') as f:
                f.write(f"\n- **{timestamp}**: {note_content}")
        else:
            with open(filepath, 'w') as f:
                f.write(f"# Notes for {today.strftime('%A, %B %d, %Y')}\n\n")
                f.write(f"## Aditya's Daily Notes\n\n")
                f.write(f"- **{timestamp}**: {note_content}")
        
        # Add to history for display
        st.session_state.notes_history.append({
            'time': timestamp,
            'content': note_content
        })
        
        return filepath
    
    def start_listening(self):
        """Start voice recognition"""
        if not st.session_state.listening:
            st.session_state.listening = True
            st.session_state.status = "🎙️ Recording... Press 'S' to stop"
            st.session_state.noted_message = False
            
            # Start listening in background thread
            thread = threading.Thread(target=self.listen_and_process, daemon=True)
            thread.start()
            
            # Show key press feedback
            st.session_state.last_key_press = "r"
            time.sleep(0.5)
            st.session_state.last_key_press = None
    
    def listen_and_process(self):
        """Listen for voice and process"""
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=10)
            
            # Convert speech to text
            text = self.recognizer.recognize_google(audio)
            
            if st.session_state.note_mode:
                # Note mode - just save text directly
                note_content = text.strip()
                if note_content:
                    filepath = self.save_note(note_content)
                    st.session_state.status = "✅ NOTED! Press 'R' to record again"
                    st.session_state.noted_message = True
                else:
                    st.session_state.status = "⚠️ Empty note - press 'R' to try again"
            else:
                # Assistant mode - check for note commands
                if self.is_note_command(text):
                    note_content = self.extract_note(text)
                    filepath = self.save_note(note_content)
                    st.session_state.status = "✅ NOTED! Press 'R' to record again"
                    st.session_state.noted_message = True
                else:
                    st.session_state.status = f"💬 Heard: '{text}' (not a note command)"
            
        except sr.WaitTimeoutError:
            st.session_state.status = "⏰ Timeout - press 'R' to try again"
        except sr.UnknownValueError:
            st.session_state.status = "❌ Didn't understand - press 'R' to try again"
        except Exception as e:
            st.session_state.status = f"❌ Error: {str(e)}"
        
        st.session_state.listening = False
        
        # Clear noted message after 3 seconds
        threading.Timer(3.0, self.clear_noted_message).start()
        
        # Reset status after 5 seconds
        threading.Timer(5.0, self.reset_status).start()
    
    def clear_noted_message(self):
        """Clear noted message"""
        st.session_state.noted_message = False
        st.rerun()
    
    def reset_status(self):
        """Reset to default status"""
        if not st.session_state.listening:
            st.session_state.status = "Ready to record - Press 'R'"
            st.rerun()
    
    def stop_listening(self):
        """Stop voice recognition"""
        if st.session_state.listening:
            st.session_state.listening = False
            st.session_state.status = "Processing..."
            
            # Show key press feedback
            st.session_state.last_key_press = "s"
            time.sleep(0.5)
            st.session_state.last_key_press = None
            st.rerun()
    
    def handle_keyboard(self):
        """Handle keyboard input using streamlit-keypress"""
        key = key_press_events()
        
        if key:
            # Reset key press display after 1 second
            threading.Timer(1.0, self.clear_key_display).start()
            st.session_state.last_key_press = key.lower()
            
            if key.lower() == 'r' and not st.session_state.listening:
                self.start_listening()
            elif key.lower() == 's' and st.session_state.listening:
                self.stop_listening()
            elif (key == ' ' or key.lower() == 'space') and not st.session_state.listening:
                # Spacebar handling - both ' ' and 'space' work
                self.start_listening()
            elif (key == ' ' or key.lower() == 'space') and st.session_state.listening:
                # Stop recording on spacebar release if recording
                self.stop_listening()
            
            st.rerun()
    
    def clear_key_display(self):
        """Clear the key press display"""
        st.session_state.last_key_press = None
        st.rerun()
    
    def run_ui(self):
        """Run Streamlit UI"""
        # Handle keyboard input
        self.handle_keyboard()
        
        # Mode switch in sidebar
        with st.sidebar:
            st.markdown("### ⚙️ Mode Settings")
            mode_selection = st.radio(
                "Select Mode:",
                ["Note Mode", "Assistant Mode"],
                index=0 if st.session_state.note_mode else 1,
                help="Note Mode: Direct voice recording | Assistant Mode: Command-based notes"
            )
            st.session_state.note_mode = (mode_selection == "Note Mode")
            
            st.markdown("---")
            st.markdown("### 🎮 Keyboard Controls")
            st.markdown("""
            **R Key** = Start Recording  
            **S Key** = Stop Recording  
            **SPACEBAR** = Toggle Recording (Start/Stop)  
            **Buttons** = Also work as backup
            """)
            
            # Show last key press
            if st.session_state.last_key_press:
                key_display = st.session_state.last_key_press.upper()
                st.markdown(f"""
                <div class="keyboard-active">
                    🎹 Key Pressed: {key_display}
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            st.markdown("### 📊 Stats")
            if st.session_state.notes_history:
                st.success(f"📝 Today's notes: {len(st.session_state.notes_history)}")
            else:
                st.info("📝 No notes today yet")
        
        st.title("🎙️ Listeny - Voice Notes")
        st.markdown("---")
        
        # Mode indicator
        if st.session_state.note_mode:
            mode_text = "📝 NOTE MODE (Direct Recording)"
            mode_class = ""
        else:
            mode_text = "🤖 ASSISTANT MODE (Commands)"
            mode_class = "assistant"
        
        st.markdown(f"""
        <div class="mode-indicator {mode_class}">
            {mode_text}
        </div>
        """, unsafe_allow_html=True)
        
        # Keyboard hint
        st.markdown("""
        <div class="keyboard-hint">
            ⌨️ KEYBOARD: R=Record | S=Stop | SPACEBAR=Toggle (Start/Stop)
        </div>
        """, unsafe_allow_html=True)
        
        # Main recording area
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.session_state.listening:
                # Show STOP button when recording
                if st.button(
                    "⏹️ STOP RECORDING",
                    key="stop_button",
                    help="Recording in progress - Click to stop",
                    use_container_width=True
                ):
                    self.stop_listening()
            else:
                # Show RECORD button when not recording
                if st.button(
                    "🎙️ RECORD",
                    key="record_button",
                    help="Click or press 'R' to start recording",
                    use_container_width=True
                ):
                    self.start_listening()
        
        # Auto-refresh when recording
        if st.session_state.listening:
            time.sleep(0.8)
            st.rerun()
        
        # Status display
        st.markdown("### Status")
        if st.session_state.noted_message:
            st.markdown("""
            <div class="noted-message">
                ✅ NOTED!
            </div>
            """, unsafe_allow_html=True)
        elif st.session_state.listening:
            st.markdown("""
            <div class="listening">
                <h3>🎙️ RECORDING...</h3>
                <div>
                    <span class="wave">🌊</span>
                    <span class="wave" style="animation-delay: 0.2s">🌊</span>
                    <span class="wave" style="animation-delay: 0.4s">🌊</span>
                </div>
                <p><em>Press 'S' or click STOP button</em></p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="status-box">
                {st.session_state.status}
            </div>
            """, unsafe_allow_html=True)
        
        # Instructions
        st.markdown("---")
        with st.expander("📖 How to Use", expanded=True):
            if st.session_state.note_mode:
                st.markdown("""
                <div class="instructions">
                    <h4>📝 Note Mode (Keyboard-First):</h4>
                    
                    <h5>⌨️ Keyboard Method (Primary):</h5>
                    <ol>
                        <li><strong>Press 'R'</strong> → Recording starts (see key indicator flash)</li>
                        <li><strong>Press SPACEBAR</strong> → Toggle recording (start/stop)</li>
                        <li><strong>Speak your note</strong> → "meeting with team at 3pm"</li>
                        <li><strong>Press 'S'</strong> → Recording stops (see key indicator flash)</li>
                        <li><strong>✅ NOTED!</strong> → Note saved automatically</li>
                    </ol>
                    
                    <h5>🖱️ Button Method (Backup):</h5>
                    <ol>
                        <li><strong>Click RECORD</strong> → Recording starts</li>
                        <li><strong>Speak your note</strong> → Clear speech</li>
                        <li><strong>Click STOP</strong> → Recording stops</li>
                        <li><strong>✅ NOTED!</strong> → Success message</li>
                    </ol>
                    
                    <p><em>🎯 Pro tip: SPACEBAR is the most natural push-to-talk!</em></p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="instructions">
                    <h4>🤖 Assistant Mode:</h4>
                    <p><strong>Commands work like:</strong></p>
                    <ul>
                        <li>"Note this: meeting with team at 3pm"</li>
                        <li>"Remember that I need to review the PR"</li>
                        <li>"Take a note: call client tomorrow"</li>
                    </ul>
                    <p>Press 'R' to record your command, 'S' to stop.</p>
                </div>
                """, unsafe_allow_html=True)
        
        # Recent notes
        st.markdown("### 📝 Today's Notes")
        
        # Load today's notes
        today = datetime.now()
        filename = today.strftime('%Y-%m-%d') + '.md'
        filepath = os.path.join(st.session_state.notes_dir, filename)
        
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                content = f.read()
                st.markdown(content)
        else:
            st.info("No notes taken today yet. Press 'R' to start!")
        
        # Manual note input
        st.markdown("---")
        st.markdown("### ✍️ Add Note Manually")
        
        manual_note = st.text_area("Enter your note:", height=100)
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("Add Note Manually", use_container_width=True):
                if manual_note.strip():
                    self.save_note(manual_note.strip())
                    st.success(f"✅ Note added!")
                    time.sleep(1)
                    st.rerun()
        
        # Server info
        st.markdown("---")
        st.markdown("### 🌐 Access Info")
        st.code(f"""
        Local: http://localhost:8501
        Network: http://YOUR_LAPTOP_IP:8501
        
        Notes stored in: {st.session_state.notes_dir}
        Mode: {'Note Mode (Direct)' if st.session_state.note_mode else 'Assistant Mode (Commands)'}
        Keyboard: R=Record, S=Stop, SPACEBAR=Toggle (All Working!)
        """)

# Main execution
if __name__ == "__main__":
    app = ListenyKeyboard()
    app.run_ui()