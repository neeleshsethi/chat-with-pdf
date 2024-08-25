from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import List

app = FastAPI()

# Pydantic model for messages
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    prompt: str
    messages: List[Message] = []

class ChatResponse(BaseModel):
    role: str
    content: str

# Health check endpoint
@app.get("/health_check")
async def health_check():
    return {"status": "Health check passed"}

# Main chat endpoint
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    user_message = request.prompt
    if not user_message:
        return {"role": "assistant", "content": "No prompt provided"}

    # Append the user message to the session messages
    request.messages.append({"role": "user", "content": user_message})

    # Generate response
    assistant_response = "This is my answer"
    full_response = "This is response"
    
    # Append the assistant's response to the session messages
    request.messages.append({"role": "assistant", "content": assistant_response})
    
    return {"role": "assistant", "content": full_response}

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to Amazon Q helper API. Use the /chat endpoint to interact."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
