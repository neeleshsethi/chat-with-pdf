import streamlit as st




def get_response(test):
    return "Hello, this is a test response from the server"



def main():

    st.title("Amazon Q helper")
    st.info("This is a demo of a Streamlit app for Amazon Q helper")
    if "messages" not in st.session_state:
      #  st.session_state['messages'] = []
        st.session_state.messages = []
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    
    prompt = st.chat_input("What is up?")

    if prompt:
        with st.chat_message("user"):
            st.markdown(prompt)

        st.session_state.messages.append({"role": "user", "content": prompt})

        reponse = "This is my answer"

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = "This is response"
            message_placeholder.markdown(full_response)
      

        st.session_state.messages.append({"role": "assistant", "content": reponse})

     

if __name__ == "__main__":
    main()



