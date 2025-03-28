import os
import requests
import json
import streamlit as st
from dotenv import load_dotenv
import socket

# Load environment variables from .env file
load_dotenv()

# Suppress warnings for verification
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Function to determine if a proxy should be used based on the IP address
def get_proxies():
    # Get the IP address of the machine
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)

    # Define local network IPs (e.g., 127.0.0.1 or any other local IP)
    if local_ip in ["127.0.0.1", "::1"] or local_ip.startswith(("192.", "10.", "172.")):
        proxy = {
            "http": os.getenv("HTTP_PROXY"),
            "https": os.getenv("HTTPS_PROXY")
        }
        return {k: v for k, v in proxy.items() if v}  # Return only if values exist
    return None  # No proxy for production or other environments

# Streamlit app
st.title("Ask Your Question")
st.write("Type your question below:")

# Debugging: Show environment information
st.write("Using proxy:", os.getenv("HTTP_PROXY"))
st.write("Local IP:", socket.gethostbyname(socket.gethostname()))

# Input text area for user's question
user_question = st.text_area("Question", placeholder="Type your question here...")

# Button to submit the question
if st.button("Submit"):
    api_key = os.getenv("API_KEY")  # Ensure the variable matches your .env file
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

    # Get proxy settings
    proxies = get_proxies()
    if proxies:
        st.write("Proxy is being used.")

    # Show loading message while waiting for the response
    with st.spinner("Fetching response..."):
        try:
            response = requests.post(url, headers=headers, json=data, verify=False, stream=True, proxies=proxies)
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
