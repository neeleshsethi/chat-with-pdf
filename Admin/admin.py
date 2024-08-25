from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware
from fastapi.responses import HTMLResponse
import streamlit as st
from streamlit.web.bootstrap import run
import uvicorn
from streamlit.web.server import Server as StreamlitServer
import os

lambda_function_name = os.environ.get('LAMBDA_FUNCTION_NAME')
app = FastAPI()

def run_streamlit():
    st.title("Amazon Q helper")
    st.info("This is a demo of a Streamlit app for Amazon Q helper")
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("What is up?")

    if prompt:
        with st.chat_message("user"):
            st.markdown(prompt)

        st.session_state.messages.append({"role": "user", "content": prompt})

        response = "This is my answer"

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = "This is response"
            message_placeholder.markdown(full_response)
      
        st.session_state.messages.append({"role": "assistant", "content": response})

@app.get("/")
async def root():
    return HTMLResponse(content="<h1>Welcome to the Amazon Q Helper API</h1>")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Mount Streamlit app
streamlit_app = StreamlitServer(run_streamlit).get_app()
app.mount("/streamlit", WSGIMiddleware(streamlit_app))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)