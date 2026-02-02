# Listeny Web Version

A Streamlit-based web interface for the Listeny voice assistant that can be accessed from any device on your network.

## New Features

- **Web Interface**: Accessible from any device via browser
- **Network Access**: Exposed via laptop IP for cross-device usage
- **Visual Feedback**: Animated listening indicators
- **Manual Note Entry**: Type notes directly if voice isn't available
- **Real-time Status**: Shows listening state and processing feedback

## Installation

1. Install additional dependency:
```bash
pip install streamlit>=1.28.0
```

2. Run the web app:
```bash
streamlit run web_app.py --server.port=8501 --server.address=0.0.0.0
```

## Access

- **Local**: http://localhost:8501
- **Network**: http://YOUR_LAPTOP_IP:8501
  (Find your laptop IP by running `ipconfig getifaddr en0` on macOS or `ip a` on Linux)

## Usage

1. Click the microphone 🎙️ button to start voice recognition
2. Speak your note command clearly
3. Wait for processing and confirmation
4. Notes are automatically saved to daily markdown files
5. Use manual note entry as backup option

## Note Commands

- "Note this: meeting with team at 3pm"
- "Remember that I need to review the PR" 
- "Take a note: call client tomorrow"
- "Write down: deadline is Friday"
- "Jot down: buy groceries after work"

## Differences from Desktop Version

- **No Text-to-Speech**: Web version focuses on visual feedback
- **Network Accessible**: Can be used from any device on your network
- **Manual Entry**: Text input as backup to voice commands
- **Real-time UI**: Streamlit provides live updates
- **Mobile Friendly**: Responsive design works on phones/tablets

## Notes Storage

All notes are still saved to the same `notes/` directory with the same YYYY-MM-DD.md format, ensuring compatibility between desktop and web versions.