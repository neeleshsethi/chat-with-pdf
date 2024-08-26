import streamlit as st
from datetime import datetime
import json
import logging
from connections import Connections
from utils import clear_input, show_empty_container, show_footer
from botocore.exceptions import ClientError, BotoCoreError
logger = logging.getLogger(__name__)
logger.setLevel(Connections.log_level)
lambda_client = Connections.lambda_client
import os

def invoke_bedrock_lambda(user_prompt, sessionId):
    # Prepare the payload
    payload = {
        'body': json.dumps({
            'userPrompt': user_prompt,
            'sessionId': sessionId
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
        """
        {
            "statusCode": 200,
            "body": json.dumps({
                "response": generated_text,
                "sessionId": sessionId
            }
        """
        result = json.loads(response['Payload'].read().decode("utf-8"))
        ##
        return result
    
    except (ClientError, BotoCoreError) as e:
        logging.error(f"Error invoking Lambda function: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": f"Error invoking Lambda function: {str(e)}"
            })
        }
    

def header():
    """
    App header setting
    """
    st.set_page_config(
        page_title="Amazon Q Chat Assistant", page_icon=":rock:", layout="centered"
    )
  
    st.header("Amazon Q Helper Demo")
    st.write("Ask me about Amazon")
    st.write("-----")

def initialization():

    if "session_id" not in st.session_state:
        st.session_state.session_id = datetime.now().strftime("%Y%m%d%H%M%S")
        st.session_state.messages = []
    
    if "temp" not in st.session_state:
        st.session_state.temp = ""

    if "cache" not in st.session_state:
        st.session_state.cache = {}

def show_message():
    """
    Show user question and answers
     """
    user_input = st.text_input("# **Question:** 👇", "", key="input")
    new_conversation = st.button("New Conversation", key="clear", on_click=clear_input)
    
    if new_conversation:
        st.session_state.session_id = str(datetime.now()).replace(" ", "_")
        st.session_state.messages = [
            {"role": "system", "content": "You are a helpful assistant that answers questions about Amazon Q ."}
        ]
        st.session_state.user_input = ""

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        sessionId = st.session_state.session_id
        
        with st.spinner("Gathering info ..."):
            vertical_space = show_empty_container()
            vertical_space.empty()
            lambda_response = invoke_bedrock_lambda(st.session_state.messages, sessionId)
              # Check if the Lambda response contains the generated text
            if 'response' in lambda_response['body']:
                assistant_response = json.loads(lambda_response['body'])['response']
                session_id = json.loads(lambda_response['body'])['sessionId']
            else:
                assistant_response = "An error occurred while processing your request."
            logger.debug(f"Output: {lambda_response}")
            
          
            st.session_state.session_id = sessionId
            answer = assistant_response 
            st.session_state.messages.append({"role": "assistant", "content": answer})

    if len(st.session_state.messages) > 1:
        for message in st.session_state.messages[1:]:  # Skip the system message
            with st.chat_message(
                name="human" if message["role"] == "user" else "ai",
                avatar="https://api.dicebear.com/7.x/notionists-neutral/svg?seed=Felix" if message["role"] == "user" else "https://assets-global.website-files.com/62b1b25a5edaf66f5056b068/62d1345ba688202d5bfa6776_aws-sagemaker-eyecatch-e1614129391121.png",
            ):
                st.markdown(message["content"])


def main():
    header()
    initialization()
    show_message()
    show_footer()


if __name__ == "__main__":
    main()



