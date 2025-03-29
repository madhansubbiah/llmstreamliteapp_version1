import os
import requests
import json
import streamlit as st
from dotenv import load_dotenv
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain_core.runnables import Runnable  # Import Runnable from the correct module

# Load environment variables from the .env file
load_dotenv()

# Suppress warnings for verification
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Set up Streamlit app
st.title("Ask Your Question")
st.write("Type your question below:")

# Initialize memory in session state for persistent storage
if 'memory' not in st.session_state:
    st.session_state.memory = ConversationBufferMemory()

# Retrieve the Groq API key from the environment variable
groq_api_key = os.getenv("API_KEY")  # Ensure you set this in your .env file

class GroqLLM(Runnable):
    def __init__(self, api_key):
        self.api_key = api_key
        self.url = "https://api.groq.com/openai/v1/chat/completions"

    def invoke(self, inputs):
        # Extract messages from inputs
        messages = inputs[0]  # Assuming you're passing a list of messages
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "llama-3.3-70b-versatile",
            "messages": messages,
            "temperature": 1,
            "max_completion_tokens": 1024,
            "top_p": 1,
            "stream": True,
        }

        # Disable SSL verification (for testing purposes only)
        response = requests.post(self.url, headers=headers, json=data, stream=True, verify=False)

        if response.status_code == 200:
            collected_content = ""
            for line in response.iter_lines():
                if line:
                    line_content = line.decode('utf-8').lstrip("data: ").strip()
                    if line_content == "[DONE]":
                        break
                    try:
                        json_line = json.loads(line_content)
                        if 'choices' in json_line and json_line['choices']:
                            collected_content += json_line['choices'][0]['delta'].get('content', '')
                    except json.JSONDecodeError:
                        continue
            return collected_content
        else:
            raise Exception(f"API call failed: {response.text}")

# Initialize the LLM
llm = GroqLLM(api_key=groq_api_key)

# Initialize the conversation chain with memory and the GroqLLM instance
conversation = ConversationChain(memory=st.session_state.memory, llm=llm)

# Input text area for user's question
user_question = st.text_area("Question", placeholder="Type your question here...")

# Button to submit the question
if st.button("Submit"):
    if not groq_api_key:
        st.error("Groq API key is not set. Please check your environment variables.")
    else:
        try:
            with st.spinner("Fetching response..."):
                # Load previous context from memory
                loaded_memory = st.session_state.memory.load_memory_variables({"context": True})  # Pass required argument
                previous_context = loaded_memory.get("history", "")

                # Prepare a fresh user message for this interaction
                user_message = user_question

                # Combine the previous context and the current user message
                combined_messages = [{"role": "user", "content": user_message}]
                
                # If there is a previous context, include it
                if previous_context:
                    combined_messages.insert(0, {"role": "assistant", "content": previous_context})

                # Get the response
                response = conversation.llm.invoke([combined_messages])  # Call the GroqLLM via invoke method

                # Now save both the user message and model response to memory
                st.session_state.memory.save_context({"input": user_message}, {"output": response})

                # Display the response
                st.write("**Response:**")
                st.write(response)

        except Exception as e:
            st.error(f"Error during prediction: {str(e)}")  # Improved error handling
