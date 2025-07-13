from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import json

app = FastAPI(title="EchoV2 Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:1420", "http://127.0.0.1:1420"],  # Tauri dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    prompt: str

class ChatResponse(BaseModel):
    response: str

@app.get("/")
async def root():
    return {"message": "EchoV2 Backend is running"}

@app.get("/health")
async def health_check():
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            return {"status": "healthy", "ollama": "connected"}
        else:
            return {"status": "unhealthy", "ollama": "disconnected"}
    except requests.exceptions.RequestException:
        return {"status": "unhealthy", "ollama": "disconnected"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        ollama_payload = {
            "model": "mistral",
            "prompt": request.prompt,
            "stream": False
        }
        
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=ollama_payload,
            timeout=60
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=500, 
                detail=f"Ollama API error: {response.status_code}"
            )
        
        result = response.json()
        return ChatResponse(response=result.get("response", "No response from model"))
        
    except requests.exceptions.ConnectionError:
        raise HTTPException(
            status_code=503, 
            detail="Cannot connect to Ollama. Make sure Ollama is running on localhost:11434"
        )
    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=504, 
            detail="Request to Ollama timed out"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Internal server error: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)