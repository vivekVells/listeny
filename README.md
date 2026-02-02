# Listeny - Voice Assistant

A voice-activated AI assistant that helps with development tasks and project management through natural language commands.

## Features

### Desktop Version (listeny.py)
- **Voice Control**: Click to activate voice capture and issue commands hands-free
- **Wave Animation**: Visual feedback with animated waves when listening
- **AI Integration**: Uses Ollama (gpt-oss:20b) for intelligent responses
- **Claude Code Execution**: Executes development tasks via Claude Code with dangerous skip permissions
- **Text-to-Speech**: Provides verbal feedback and responses
- **Daily Notes**: Take voice notes that are saved to daily markdown files

### Web Version (web_app.py)
- **Web Interface**: Browser-based access from any device
- **Network Accessible**: Use from phone, tablet, or other computers
- **Mobile Friendly**: Responsive design for all screen sizes
- **Real-time Status**: Visual feedback with animated listening indicators
- **Manual Note Entry**: Type notes directly as backup option
- **Same Note Storage**: Compatible with desktop version notes

## Requirements

### Core Requirements (Both Versions)
- Python 3.7+
- Ollama server running at http://localhost:11434 (configure in .env file)
- Microphone access
- SpeechRecognition and PyAudio for voice capture

### Desktop Version (listeny.py)
- Claude Code CLI installed and accessible
- pyttsx3 (for text-to-speech)
- Tkinter (usually comes with Python)

### Web Version (web_app.py)
- Streamlit >=1.28.0
- Web browser with microphone permissions
- Network access for cross-device usage

## Installation

1. Install core dependencies:
```bash
pip install -r requirements.txt
```

2. For web version, install additional dependency:
```bash
pip install streamlit>=1.28.0
```

3. Ensure Ollama is running with the gpt-oss:20b model:
```bash
# Start Ollama server
ollama serve

# Pull the model if not already available
ollama pull gpt-oss:20b
```

4. For desktop version, make sure Claude Code CLI is installed and available in PATH.

5. Test microphone permissions on your system.

## Usage

Listeny is available in two versions:

### Desktop Version (Tkinter)
```bash
python3 listeny.py
```

**How to Use (Desktop):**
1. **Start Listening**: Click the blue circle in the center of the window
2. **Voice Command**: Speak your command clearly when the wave animation appears
3. **Processing**: The app will process your command through Ollama AI
4. **Execution**: If it's a development task, it will execute via Claude Code
5. **Response**: Listen to the verbal response

### Web Version (Streamlit)
```bash
# Install additional dependency
pip install streamlit>=1.28.0

# Run web app (accessible from any device on network)
streamlit run web_app.py --server.port=8501 --server.address=0.0.0.0
```

**Access URLs:**
- **Local**: http://localhost:8501
- **Network**: http://YOUR_LAPTOP_IP:8501
  - Find your IP: `ipconfig getifaddr en0` (macOS) or `ip a` (Linux)

**How to Use (Web):**
1. **Start Listening**: Click the microphone 🎙️ button
2. **Voice Command**: Speak your note command clearly
3. **Visual Feedback**: Watch animated listening indicator
4. **Processing**: Note is processed and saved automatically
5. **Confirmation**: Check status for success message
6. **Manual Entry**: Use text area if voice isn't available

### Web Version Advantages
- **Network Access**: Use from any device (phone, tablet, other computers)
- **Mobile Friendly**: Responsive design for all screen sizes
- **Manual Backup**: Type notes if microphone isn't working
- **Real-time Updates**: Live status and note display
- **No Audio Dependencies**: No TTS/Pyttsx3 required

### Example Commands

- "Create a new Python file called app.py"
- "Run the tests for this project"
- "Build and deploy the application" 
- "Refactor this code to be more efficient"
- "Install these dependencies"
- "Check the git status"
- "Write documentation for this module"
- "Make the login page responsive"
- "Add error handling to the API endpoint"
- "Create a unit test for the user service"

### Note-Taking Commands

Say any of these to save notes to your daily file (works on both desktop and web versions):

- "Note this: meeting with team at 3pm"
- "Remember that I need to review the PR"
- "Take a note: call client tomorrow"
- "Write down: deadline is Friday"
- "Jot down: buy groceries after work"

**Note Storage:**
- All notes are saved to `notes/YYYY-MM-DD.md` with timestamps
- Both desktop and web versions share the same notes directory
- Each day creates a new markdown file with chronological entries
- Files contain date headers and structured note formatting

## Architecture

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐
│   Voice Input   │ -> │  Ollama AI   │ -> │  Claude Code    │
│  (Microphone)   │    │ (gpt-oss:20b)│    │   Execution     │
└─────────────────┘    └──────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐
│ Speech Recognition│    │   AI Response│    │  Command Output │
│                 │    │               │    │                 │
└─────────────────┘    └──────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 ▼
                    ┌─────────────────┐
                    │ Text-to-Speech  │
                    │   (Response)    │
                    └─────────────────┘
```

## Configuration

### Ollama Settings
- **Host**: http://localhost:11434 (configure in .env file)
- **Model**: gpt-oss:20b
- Update the `ollama_client` initialization in `listeny.py` if your setup differs

### Claude Code Integration
- Uses `--dangerously-skip-permissions` flag for seamless command execution
- Commands are detected through keyword analysis (create, make, write, run, execute, build, install, delete, remove)

### System Prompt
Listeny operates with a comprehensive system prompt that defines:
- Its identity as Aditya's personal AI assistant
- Available tools and capabilities
- Command examples and usage patterns
- Safety guidelines and behavioral guidelines

## Files

- `listeny.py` - Desktop application (Tkinter) with voice processing and integrations
- `web_app.py` - Web application (Streamlit) with network accessibility
- `requirements.txt` - Python dependencies
- `project.md` - Project documentation
- `README.md` - This file
- `WEB_README.md` - Web-specific documentation and setup guide
- `notes/` - Directory containing daily note files (auto-created, shared by both versions)

## Development

### Adding New Commands
Commands are automatically detected through keyword analysis. To add support for new command types:

1. Update the `should_execute_with_claude()` method with additional keywords
2. Enhance the system prompt with new command examples
3. Test with the specific command type

### Customizing the UI
The interface uses tkinter with a dark theme:
- Wave animation in `animate_waves()` method
- Color scheme: dark background (#1a1a1a) with blue accent (#4a90e2)
- Responsive 300x400 window size

### Extending AI Capabilities
The Ollama integration can be extended by:
- Switching to different models in the `generate()` call
- Adding conversation history/context
- Implementing custom prompts for specific domains

## Troubleshooting

### Common Issues

1. **Microphone not working**:
   - Check microphone permissions in System Preferences
   - Ensure PyAudio is correctly installed
   - Try using a different microphone

2. **Ollama connection failed**:
   - Verify Ollama server is running at the specified host
   - Check network connectivity to your Ollama server (configured in .env)
   - Ensure the gpt-oss:20b model is pulled

3. **Claude Code not executing**:
   - Verify Claude Code CLI is installed and in PATH
   - Check if the dangerous skip permissions flag is working
   - Review the command detection keywords

4. **Text-to-speech not working**:
   - Ensure pyttsx3 is installed correctly
   - Check system audio settings
   - Try different voice engines if available

### Debug Mode
Add debug prints by modifying the code to output:
- Recognized text from speech recognition
- AI responses from Ollama
- Claude Code execution results

## License

This project is open source. Feel free to modify and distribute according to your needs.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

**Note**: This is a personal assistant project designed for Aditya's workflow. Adapt the system prompt and configurations for your specific use case.