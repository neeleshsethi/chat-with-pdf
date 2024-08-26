from fastapi import FastAPI, Request,HTTPException
from pydantic import BaseModel
from typing import List
import os
import boto3
import json
from botocore.exceptions import ClientError, BotoCoreError
import logging
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from datetime import datetime
import streamlit as st




app = FastAPI()

# Pydantic model for messages
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    prompt: str
    sessionId: str 
    messages: List[Message] = []

class ChatResponse(BaseModel):
    role: str
    content: str
    sessionId: str 

session = boto3.session.Session()
region = session.region_name
lambda_client = boto3.client('lambda', region_name=region)


# Health check endpoint
@app.get("/health_check")
async def health_check():
    return {"status": "Health check passed"}



# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to Amazon Q helper API. Use the /chat endpoint to interact."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


def invoke_bedrock_lambda(user_prompt, session_id):
    # Prepare the payload
    payload = {
        'body': json.dumps({
            'userPrompt': user_prompt,
            'sessionId': session_id
        })
    }
    
    try:
        # Call the Lambda function
        response = lambda_client.invoke(
            FunctionName=os.getenv('LAMBDA_FUNCTION_NAME'),
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        # Parse the response
        result = json.loads(response['Payload'].read().decode("utf-8"))
        return result
    
    except (ClientError, BotoCoreError) as e:
        logging.error(f"Error invoking Lambda function: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": f"Error invoking Lambda function: {str(e)}"
            })
        }
    
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    user_message = request.prompt
    sessionId = request.sessionId

    if not user_message:
        return {"role": "assistant", "content": "No prompt provided"}

    # Call the Lambda function to get the response from AWS Bedrock
    lambda_response = invoke_bedrock_lambda(user_prompt=user_message, session_id=session_id)

    # Check if the Lambda response contains the generated text
    if 'response' in lambda_response['body']:
        assistant_response = json.loads(lambda_response['body'])['response']
        session_id = json.loads(lambda_response['body'])['sessionId']
    else:
        assistant_response = "An error occurred while processing your request."

    # Append the assistant's response to the session messages
    request.messages.append({"role": "assistant", "content": assistant_response})
    
    return {"role": "assistant", "content": assistant_response,"sessionId":sessionId}

# Health check endpoint
@app.get("/health")
async def health_check():
    # Here, you can add checks to verify the health of dependent services if needed
    return {"status": "Health check passed", "region": region}

# Custom exception handler for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logging.error(f"Validation error: {exc}")
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors()
        }
    )
