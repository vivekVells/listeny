from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import speech_recognition as sr
import os
from datetime import datetime
from zoneinfo import ZoneInfo
import uvicorn
from typing import Optional
import tempfile
from pydub import AudioSegment
import ollama

# Configure Ollama client to use host from environment variable
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
ollama_client = ollama.Client(host=OLLAMA_HOST)

class NoteRequest(BaseModel):
    text: Optional[str] = None
    action: str

class ListenyAPI:
    def __init__(self):
        # Initialize components
        self.recognizer = sr.Recognizer()

        # Notes directory
        self.notes_dir = os.path.join(os.path.dirname(__file__), 'notes')
        os.makedirs(self.notes_dir, exist_ok=True)

        # Session data
        self.notes_history = []
        self.note_mode = True

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
        chicago_tz = ZoneInfo("America/Chicago")
        today = datetime.now(chicago_tz)
        filename = today.strftime('%Y-%m-%d') + '.md'
        filepath = os.path.join(self.notes_dir, filename)

        timestamp = today.strftime('%H:%M')

        if os.path.exists(filepath):
            with open(filepath, 'a') as f:
                f.write(f"\n- **{timestamp}**: {note_content}")
        else:
            with open(filepath, 'w') as f:
                f.write(f"# Notes for {today.strftime('%A, %B %d, %Y')}\n\n")
                f.write(f"## Daily Notes\n\n")
                f.write(f"- **{timestamp}**: {note_content}")

        # Add to history
        self.notes_history.append({
            'time': timestamp,
            'content': note_content
        })

        return filepath

    async def process_audio(self, audio_file: UploadFile):
        """Process uploaded audio file"""
        try:
            # Save uploaded file to temporary location
            with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as tmp_webm:
                content = await audio_file.read()
                tmp_webm.write(content)
                tmp_webm_path = tmp_webm.name

            # Convert WebM to WAV
            wav_path = tmp_webm_path.replace('.webm', '.wav')

            try:
                # Convert audio using pydub
                audio_segment = AudioSegment.from_file(tmp_webm_path, format="webm")
                audio_segment.export(wav_path, format="wav")

                # Process audio file with speech recognition
                with sr.AudioFile(wav_path) as source:
                    audio = self.recognizer.record(source)

                # Convert speech to text
                text = self.recognizer.recognize_google(audio)

                if self.note_mode:
                    # Note mode - save text directly
                    note_content = text.strip()
                    if note_content:
                        filepath = self.save_note(note_content)
                        result = {"status": "noted", "message": "NOTED!", "text": text}
                    else:
                        result = {"status": "error", "message": "Empty note"}
                else:
                    # Assistant mode - check for note commands
                    if self.is_note_command(text):
                        note_content = self.extract_note(text)
                        filepath = self.save_note(note_content)
                        result = {"status": "noted", "message": "NOTED!", "text": text}
                    else:
                        result = {"status": "error", "message": f"Heard: '{text}' (not a note command)", "text": text}

            finally:
                # Clean up temp files
                if os.path.exists(tmp_webm_path):
                    os.unlink(tmp_webm_path)
                if os.path.exists(wav_path):
                    os.unlink(wav_path)

        except sr.UnknownValueError:
            result = {"status": "error", "message": "Couldn't understand audio"}
        except Exception as e:
            result = {"status": "error", "message": f"Error: {str(e)}"}

        return result

# Initialize the app
listeny = ListenyAPI()
app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Listeny API is running"}

@app.post("/api/upload-audio")
async def upload_audio(audio: UploadFile = File(...)):
    """Accept audio file from browser and process it"""
    return await listeny.process_audio(audio)

@app.post("/api/manual-note")
async def manual_note(request: NoteRequest):
    if request.text:
        filepath = listeny.save_note(request.text)
        return {"status": "noted", "message": "Note saved manually", "content": request.text}
    return {"status": "error", "message": "No note content"}

@app.get("/api/status")
async def get_status():
    return {
        "status": "idle",
        "note_mode": listeny.note_mode,
        "notes_count": len(listeny.notes_history)
    }

@app.get("/api/notes")
async def get_notes():
    # Get today's notes
    chicago_tz = ZoneInfo("America/Chicago")
    today = datetime.now(chicago_tz)
    filename = today.strftime('%Y-%m-%d') + '.md'
    filepath = os.path.join(listeny.notes_dir, filename)

    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            content = f.read()
        return {"notes": content, "filename": filename}

    return {"notes": "", "filename": filename}

@app.post("/api/mode")
async def set_mode(request: NoteRequest):
    if request.action == "note":
        listeny.note_mode = True
    elif request.action == "assistant":
        listeny.note_mode = False

    return {
        "status": "success",
        "note_mode": listeny.note_mode,
        "message": f"Switched to {'Note' if listeny.note_mode else 'Assistant'} mode"
    }

@app.get("/api/summarize-notes")
async def summarize_notes():
    """Get today's notes and summarize them using Ollama"""
    try:
        # Get today's notes
        chicago_tz = ZoneInfo("America/Chicago")
        today = datetime.now(chicago_tz)
        filename = today.strftime('%Y-%m-%d') + '.md'
        filepath = os.path.join(listeny.notes_dir, filename)

        if not os.path.exists(filepath):
            return {
                "status": "error",
                "message": "No notes found for today",
                "summary": "You haven't taken any notes today yet."
            }

        with open(filepath, 'r') as f:
            notes_content = f.read()

        if not notes_content.strip():
            return {
                "status": "error",
                "message": "Notes file is empty",
                "summary": "You haven't taken any notes today yet."
            }

        # Create prompt for Ollama
        prompt = f"""Please summarize the following notes in a concise, natural way that can be read aloud.
Focus on the key points and action items. Keep it brief and conversational.

Notes:
{notes_content}

Summary:"""

        # Call Ollama to summarize
        response = ollama_client.chat(
            model='llama3.2',
            messages=[{
                'role': 'user',
                'content': prompt
            }]
        )

        summary = response['message']['content']

        return {
            "status": "success",
            "summary": summary,
            "notes_count": len(listeny.notes_history)
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Error summarizing notes: {str(e)}",
            "summary": "Sorry, I couldn't summarize your notes right now."
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
