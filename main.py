# backend/main.py
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import tempfile
import os
import subprocess
from typing import Dict, Any

app = FastAPI(title="Creator AI Co-Pilot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def call_ollama(prompt: str) -> str:
    """Call Ollama with LLaMA-3 model"""
    try:
        result = subprocess.run(
            ['ollama', 'run', 'llama3'],
            input=prompt.encode(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60  # 60 second timeout
        )
        if result.stderr:
            print("Ollama logs:", result.stderr.decode())
        return result.stdout.decode().strip()
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="AI analysis timed out")
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Ollama not found. Make sure it's installed and running.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {str(e)}")

def analyze_comments_text(comments_text: str) -> Dict[str, Any]:
    """Analyze comments and return structured results"""
    prompt = f"""You're a content strategist for a creator. Analyze these viewer comments and provide insights:

COMMENTS:
{comments_text}

Please provide your response in this exact format:

VIEWER THEMES:
1. [Theme 1]
2. [Theme 2] 
3. [Theme 3]

CONTENT IDEAS:
1. [Content idea 1]
2. [Content idea 2]
3. [Content idea 3]

Keep each theme and idea concise but specific. Focus on actionable insights."""

    try:
        ai_response = call_ollama(prompt)
        
        # Parse the response to extract themes and ideas
        lines = ai_response.split('\n')
        themes = []
        ideas = []
        current_section = None
        
        for line in lines:
            line = line.strip()
            if 'VIEWER THEMES:' in line.upper():
                current_section = 'themes'
                continue
            elif 'CONTENT IDEAS:' in line.upper():
                current_section = 'ideas'
                continue
            elif line and (line.startswith('1.') or line.startswith('2.') or line.startswith('3.')):
                content = line[2:].strip()  # Remove "1. " prefix
                if current_section == 'themes':
                    themes.append(content)
                elif current_section == 'ideas':
                    ideas.append(content)
        
        return {
            "raw_response": ai_response,
            "themes": themes if themes else ["AI analysis completed - check raw response"],
            "content_ideas": ideas if ideas else ["AI analysis completed - check raw response"],
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/")
async def root():
    return {"message": "Creator AI Co-Pilot API", "status": "running"}

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test Ollama connection
        test_response = call_ollama("Say hello")
        return {
            "status": "healthy",
            "ollama_status": "connected",
            "test_response": test_response[:50] + "..." if len(test_response) > 50 else test_response
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "ollama_status": "disconnected",
            "error": str(e)
        }

@app.post("/api/analyze-comments")
async def analyze_comments_file(file: UploadFile = File(...)):
    """Analyze comments from uploaded file"""
    
    # Validate file type
    if not file.filename.endswith(('.txt', '.csv')):
        raise HTTPException(status_code=400, detail="Please upload a .txt or .csv file")
    
    try:
        # Read file content
        content = await file.read()
        comments_text = content.decode('utf-8')
        
        if not comments_text.strip():
            raise HTTPException(status_code=400, detail="File appears to be empty")
        
        # Analyze comments
        result = analyze_comments_text(comments_text)
        result["filename"] = file.filename
        result["comment_count"] = len(comments_text.split('\n'))
        
        return result
        
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Could not read file. Please ensure it's a valid text file.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

class TextAnalysisRequest(BaseModel):
    comments: str

@app.post("/api/analyze-text")
async def analyze_comments_text_endpoint(request: TextAnalysisRequest):
    """Analyze comments from direct text input"""
    
    if not request.comments.strip():
        raise HTTPException(status_code=400, detail="Comments text cannot be empty")
    
    try:
        result = analyze_comments_text(request.comments)
        result["comment_count"] = len(request.comments.split('\n'))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Creator AI Co-Pilot API...")
    print("📝 Make sure Ollama is running: ollama serve")
    print("🤖 Make sure LLaMA-3 is installed: ollama pull llama3")
    uvicorn.run(app, host="0.0.0.0", port=8000)