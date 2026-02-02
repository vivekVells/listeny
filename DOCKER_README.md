# Listeny - Docker Setup

A complete Docker setup for running Listeny voice assistant with FastAPI backend and React frontend.

## 🐳 Docker Architecture

```
┌─────────────────┐    ┌─────────────────┐
│   Frontend    │    │   Backend     │
│   (React)     │    │   (FastAPI)   │
│   Port: 3000   │    │   Port: 8000   │
└─────────────────┘    └─────────────────┘
         │                       │
         └─────────────┬─────────┘
                       ▼
                ┌─────────────────┐
                │  Docker Host   │
                │   Port: 3000   │
                └─────────────────┘
```

## 🚀 Quick Start

```bash
# Clone and navigate to the directory
cd /path/to/listen.me

# Build and run all services
docker-compose up --build

# Or run in background
docker-compose up --build -d
```

## 🌐 Access URLs

- **Frontend**: http://localhost:3000
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Network**: http://YOUR_LAPTOP_IP:3000

## 🎮 Perfect Keyboard Support

- **SPACEBAR**: Push-to-talk toggle (most natural)
- **R Key**: Start recording
- **S Key**: Stop recording
- **Mouse**: Click RECORD/STOP buttons as backup

## 📁 File Structure

```
listeny/
├── docker-compose.yml          # Main orchestrator
├── Dockerfile.backend         # FastAPI container
├── frontend/
│   ├── Dockerfile.frontend   # React container
│   ├── nginx.conf           # Nginx config
│   ├── package.json         # React dependencies
│   └── src/
│       ├── App.js           # Main React component
│       └── App.css          # Styling
├── backend.py               # FastAPI server
├── requirements.txt          # Python deps
└── notes/                  # Persistent storage (volume)
```

## 🔧 How It Works

### Frontend (React)
- **React SPA** with real-time keyboard capture
- **Axios** for API communication
- **Nginx** serving static files
- **Perfect spacebar support** with visual feedback

### Backend (FastAPI)
- **FastAPI** async endpoints
- **SpeechRecognition** for voice capture
- **CORS** enabled for frontend
- **File storage** in mounted volume

### Docker Services

#### Backend Service
- **Python 3.11-slim** base image
- **PortAudio** for microphone access
- **uvicorn** ASGI server
- **Volume mount** for notes persistence

#### Frontend Service
- **Multi-stage** Node.js build
- **Nginx** Alpine web server
- **API proxy** to backend service
- **Static optimization** with caching

## 🗂️ Persistent Storage

- **Notes volume** mounted at `/app/notes` in backend
- **Host directory** `./notes/` contains all markdown files
- **Docker Compose** creates and manages volume automatically

## 🔍 Development vs Production

### Development
```bash
# Backend only
python3 backend.py

# Frontend only
cd frontend && npm start

# Full stack
docker-compose up --build
```

### Production Deployment
```bash
# Build once
docker-compose build

# Run detached
docker-compose up -d

# View logs
docker-compose logs -f
```

## 🐛 Troubleshooting

### Common Issues

1. **Port conflicts**:
   ```bash
   # Check what's using ports 3000/8000
   lsof -i :3000
   lsof -i :8000
   ```

2. **Permission issues**:
   ```bash
   # Fix volume permissions
   sudo chown -R $USER:$USER ./notes/
   chmod -R 755 ./notes/
   ```

3. **Network access**:
   ```bash
   # Find your IP
   ipconfig getifaddr en0  # macOS
   ip a | grep inet          # Linux
   ```

### Debug Mode
```bash
# Verbose logging
docker-compose up --build --verbose

# Service logs only
docker-compose logs backend
docker-compose logs frontend
```

## 🔄 Updating the App

### Code Changes
```bash
# Rebuild specific service
docker-compose up --build backend

# Or rebuild all
docker-compose up --build --force-recreate
```

### Dependency Updates
```bash
# Backend
pip install -r requirements.txt
docker-compose up --build backend

# Frontend  
npm install
docker-compose up --build frontend
```

## 📊 Performance Notes

- **Startup time**: ~10 seconds total
- **Memory usage**: ~200MB combined
- **Network**: Internal Docker network for security
- **Persistence**: Volume-based, survives container restarts
- **Scalability**: Can be deployed with Docker Swarm/K8s

## 🔒 Security Features

- **CORS** properly configured
- **Nginx** security headers
- **Docker** non-root user
- **Network isolation** with bridge network
- **Volume** permissions controlled

This Docker setup gives you a production-ready voice notes app with perfect keyboard control and persistent storage!