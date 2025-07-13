# EchoV2 - Local AI Chat

A minimal MVP desktop application that combines Tauri, React, Python FastAPI, and Ollama for local-first AI conversations.

## Prerequisites

- **Node.js** (v18+)
- **Python** (v3.8+)
- **Rust** (for Tauri)
- **Ollama** (running locally)

## Setup Instructions

### 1. Install Dependencies

```bash
# Install Node.js dependencies
npm install

# Install Python dependencies
cd backend
pip install -r requirements.txt
cd ..
```

### 2. Start Ollama

Make sure Ollama is running with a model:

```bash
# Install and start mistral model (or your preferred model)
ollama pull mistral
ollama run mistral
```

Keep this terminal open. Ollama should be accessible at `http://localhost:11434`.

### 3. Start the Backend

In a new terminal:

```bash
cd backend
uvicorn main:app --reload
```

The FastAPI backend will start at `http://localhost:8000`.

### 4. Start the Frontend

In another terminal:

```bash
npm run tauri:dev
```

This will compile the Tauri app and open the desktop application.

## Usage

1. Type your message in the text area
2. Press Enter or click "Send"
3. The message is sent to the FastAPI backend
4. The backend calls Ollama at localhost:11434
5. The AI response is displayed in the chat window

## Project Structure

```
EchoV2/
├── src/                    # React frontend
│   ├── App.tsx            # Main chat interface
│   ├── components/
│   │   └── ChatWindow.tsx # Chat display component
│   └── styles/
├── src-tauri/             # Tauri (Rust) desktop wrapper
├── backend/               # Python FastAPI backend
│   ├── main.py           # API server with Ollama integration
│   └── requirements.txt
└── package.json          # Node.js dependencies
```

## API Endpoints

- `GET /health` - Check backend and Ollama connectivity
- `POST /chat` - Send a prompt and receive AI response

## Development Commands

```bash
# Frontend development
npm run tauri:dev

# Backend development  
cd backend && uvicorn main:app --reload

# Check backend health
curl http://localhost:8000/health
```

## Troubleshooting

**Frontend can't connect to backend:**
- Ensure FastAPI is running on port 8000
- Check CORS settings in `backend/main.py`

**Backend can't connect to Ollama:**
- Verify Ollama is running: `ollama list`
- Check Ollama is on port 11434: `curl http://localhost:11434/api/tags`
- Try restarting Ollama service

**Tauri build issues:**
- Ensure Rust is installed
- Run `npm install` to get latest Tauri CLI

## License

MIT