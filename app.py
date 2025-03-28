import os
import requests
import json
import streamlit as st
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Suppress warnings for verification
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Streamlit app
st.title("Ask Your Question")
st.write("Type your question below:")

# Input text area for user's question
user_question = st.text_area("Question", placeholder="Type your question here...")

# Button to submit the question
if st.button("Submit"):
    api_key = os.getenv("api_key")
    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": user_question}],
        "temperature": 1,
        "max_completion_tokens": 1024,
        "top_p": 1,
        "stream": True,
    }

    try:
        response = requests.post(url, headers=headers, json=data, verify=False, stream=True)
        collected_content = ""
        
        # Processing the streamed response line by line
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

        st.write("**Response:**")
        st.write(collected_content)  # Display the collected response
    except requests.exceptions.RequestException as e:
        st.error(f"Error during API call: {e}")  # Show error message
