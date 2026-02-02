import tkinter as tk
from tkinter import Canvas
import speech_recognition as sr
import pyttsx3
import ollama
import subprocess
import threading
import time
import math
import random
import os
from datetime import datetime

class Listeny:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Listeny")
        self.root.geometry("300x400")
        self.root.configure(bg='#1a1a1a')
        
        # Initialize components
        self.recognizer = sr.Recognizer()
        self.tts_engine = pyttsx3.init()
        self.ollama_client = ollama.Client(host='http://192.168.40.69:11434/')
        
        # Notes directory
        self.notes_dir = os.path.join(os.path.dirname(__file__), 'notes')
        os.makedirs(self.notes_dir, exist_ok=True)
        
        # UI elements
        self.canvas = Canvas(self.root, width=300, height=300, bg='#1a1a1a', highlightthickness=0)
        self.canvas.pack(pady=50)
        
        self.status_label = tk.Label(self.root, text="Click to start listening", fg='white', bg='#1a1a1a', font=('Arial', 12))
        self.status_label.pack()
        
        # Wave animation variables
        self.waves = []
        self.animating = False
        self.listening = False
        
        # Canvas click event
        self.canvas.bind('<Button-1>', self.toggle_listening)
        
        # Welcome message
        threading.Thread(target=self.speak, args=("Hello I am listeny here to listen",), daemon=True).start()
        
    def toggle_listening(self, event):
        if not self.listening:
            self.start_listening()
        else:
            self.stop_listening()
    
    def start_listening(self):
        self.listening = True
        self.status_label.config(text="Listening...")
        self.start_wave_animation()
        
        # Start listening in separate thread
        threading.Thread(target=self.listen_and_process, daemon=True).start()
    
    def stop_listening(self):
        self.listening = False
        self.status_label.config(text="Processing...")
        self.stop_wave_animation()
    
    def start_wave_animation(self):
        self.animating = True
        self.animate_waves()
    
    def stop_wave_animation(self):
        self.animating = False
        self.canvas.delete("all")
        self.waves = []
    
    def animate_waves(self):
        if not self.animating:
            return
        
        self.canvas.delete("all")
        
        # Add new wave occasionally
        if random.random() < 0.1:
            self.waves.append({'radius': 10, 'opacity': 1.0})
        
        # Update and draw waves
        center_x, center_y = 150, 150
        waves_to_remove = []
        
        for i, wave in enumerate(self.waves):
            wave['radius'] += 3
            wave['opacity'] -= 0.02
            
            if wave['opacity'] <= 0:
                waves_to_remove.append(i)
            else:
                color_intensity = int(100 * wave['opacity'])
                color = f'#{color_intensity:02x}{color_intensity+50:02x}{255:02x}'
                self.canvas.create_oval(
                    center_x - wave['radius'], center_y - wave['radius'],
                    center_x + wave['radius'], center_y + wave['radius'],
                    outline=color, width=2
                )
        
        # Remove dead waves
        for i in reversed(waves_to_remove):
            self.waves.pop(i)
        
        # Draw center circle
        self.canvas.create_oval(130, 130, 170, 170, fill='#4a90e2', outline='white', width=2)
        
        if self.animating:
            self.root.after(50, self.animate_waves)
    
    def listen_and_process(self):
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
            # Stop listening animation
            self.root.after(0, self.stop_listening)
            
            # Convert speech to text
            text = self.recognizer.recognize_google(audio)
            print(f"Recognized: {text}")
            
            # Check for note command first
            if self.is_note_command(text):
                note_content = self.extract_note(text)
                self.save_note(note_content)
                response = f"Got it, I've noted that down for you."
            # Execute with Claude Code if needed
            elif self.should_execute_with_claude(text):
                result = self.execute_with_claude(text)
                response = f"Executed: {result}"
            else:
                # Process with Ollama
                response = self.get_ollama_response(text)
                print(f"AI Response: {response}")
            
            # Speak response
            threading.Thread(target=self.speak, args=(response,), daemon=True).start()
            
            # Reset UI
            self.root.after(1000, lambda: self.status_label.config(text="Click to start listening"))
            
        except sr.WaitTimeoutError:
            self.root.after(0, lambda: self.status_label.config(text="Timeout - Click to try again"))
            self.listening = False
            self.stop_wave_animation()
        except sr.UnknownValueError:
            self.root.after(0, lambda: self.status_label.config(text="Didn't understand - Click to try again"))
            self.listening = False
            self.stop_wave_animation()
        except Exception as e:
            print(f"Error: {e}")
            self.root.after(0, lambda: self.status_label.config(text="Error - Click to try again"))
            self.listening = False
            self.stop_wave_animation()
    
    def get_ollama_response(self, text):
        try:
            system_prompt = """You are Listeny, a voice-activated AI assistant for Aditya. You help with tasks, manage projects, and execute commands through voice interaction.

## Capabilities:
- Voice-controlled AI assistant using speech recognition and text-to-speech
- Access to Ollama AI model (gpt-oss:20b) for intelligent responses
- Integration with Claude Code for executing development tasks
- File system operations and project management
- Code generation, debugging, and refactoring
- System command execution through Claude Code

## Tools Available:
1. **Claude Code Integration**: Can execute commands like 'create file', 'write code', 'run tests', 'build project', etc. using --dangerously-skip-permissions mode
2. **Ollama AI**: Advanced reasoning and conversation capabilities
3. **File System**: Read, write, modify files and directories
4. **Speech Recognition**: Convert voice to text commands
5. **Text-to-Speech**: Provide verbal responses
6. **Daily Notes**: Take and save notes to daily markdown files in the notes/ folder

## Command Examples:
- "Create a new Python file called app.py"
- "Run the tests for this project" 
- "Build and deploy the application"
- "Refactor this code to be more efficient"
- "Install these dependencies"
- "Check the git status"
- "Write documentation for this module"

## Note-Taking Commands:
- "Note this: meeting with team at 3pm"
- "Remember that I need to review the PR"
- "Take a note: call client tomorrow"
- "Write down: deadline is Friday"
- "Jot down: buy groceries after work"

## Behavior:
- Always respond as Listeny, Aditya's personal assistant
- Be helpful, concise, and action-oriented
- For development tasks, leverage Claude Code execution
- Provide clear verbal feedback on actions taken
- Ask for clarification if commands are ambiguous
- Prioritize security and safety in all operations

Current working directory: /Users/adityakarnam/Projects/listen.me"""
            
            full_prompt = f"{system_prompt}\n\nUser: {text}\n\nListeny:"
            response = self.ollama_client.generate(
                model='gpt-oss:20b',
                prompt=full_prompt
            )
            return response['response']
        except Exception as e:
            return f"Error getting AI response: {str(e)}"
    
    def is_note_command(self, text):
        """Check if the command is a note-taking request"""
        note_triggers = ['note this', 'note that', 'take a note', 'remember this', 'remember that', 'add note', 'save note', 'write down', 'jot down']
        text_lower = text.lower()
        return any(trigger in text_lower for trigger in note_triggers)
    
    def extract_note(self, text):
        """Extract the actual note content from the command"""
        text_lower = text.lower()
        # Remove trigger phrases to get the actual note
        triggers = ['note this', 'note that', 'take a note', 'remember this', 'remember that', 'add note', 'save note', 'write down', 'jot down']
        note = text
        for trigger in triggers:
            if trigger in text_lower:
                idx = text_lower.find(trigger) + len(trigger)
                note = text[idx:].strip()
                # Remove common filler words at the start
                for filler in ['that', 'to', ':', '-']:
                    if note.lower().startswith(filler):
                        note = note[len(filler):].strip()
                break
        return note if note else text
    
    def save_note(self, note_content):
        """Save note to today's markdown file"""
        today = datetime.now()
        filename = today.strftime('%Y-%m-%d') + '.md'
        filepath = os.path.join(self.notes_dir, filename)
        
        timestamp = today.strftime('%H:%M')
        
        # Check if file exists
        if os.path.exists(filepath):
            # Append to existing file
            with open(filepath, 'a') as f:
                f.write(f"\n- **{timestamp}**: {note_content}")
        else:
            # Create new file with header
            with open(filepath, 'w') as f:
                f.write(f"# Notes for {today.strftime('%A, %B %d, %Y')}\n\n")
                f.write(f"## Aditya's Daily Notes\n\n")
                f.write(f"- **{timestamp}**: {note_content}")
        
        print(f"Note saved to {filepath}")
    
    def should_execute_with_claude(self, text):
        # Simple heuristic - if it contains command-like words
        command_words = ['create', 'make', 'write', 'run', 'execute', 'build', 'install', 'delete', 'remove']
        return any(word in text.lower() for word in command_words)
    
    def execute_with_claude(self, command):
        try:
            # Run claude code with dangerous skip permissions
            result = subprocess.run(
                ['claude', '--dangerously-skip-permissions', command],
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.stdout if result.stdout else result.stderr
        except subprocess.TimeoutExpired:
            return "Command timed out"
        except Exception as e:
            return f"Error executing command: {str(e)}"
    
    def speak(self, text):
        try:
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        except Exception as e:
            print(f"TTS Error: {e}")
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = Listeny()
    app.run()