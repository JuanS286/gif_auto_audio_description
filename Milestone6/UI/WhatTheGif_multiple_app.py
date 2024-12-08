import streamlit as st
from PIL import Image
import requests
from io import BytesIO
import base64
import os
from google.cloud import texttospeech

# Set up authentication to the service account key file
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'winter-wonder-442806-e3-93ea92747f60.json'

#Cloud Run endpoint URL
API_URL = "https://gif-captioning-app-281207086739.us-central1.run.app/generate_caption"


# Function to call Model's function to generate caption from image
def generate_caption(gif_url, gif_file, option):
    if option == "Enter GIF URLs":
        # Prepare the form data
        data = {'gif_url': gif_url}
        response = requests.post(API_URL, data=data)
        if response.status_code == 200:
            result = response.json()
            generated_description = result.get('generated_description', 'No description found.')
        else:
            st.error(f"Failed to generate caption for URL: {gif_url}. Error: {response.status_code}")
            generated_description = None
    else:
        gif_file.seek(0)
        data = {'gif_url': ''}
        files = {'file': (gif_file.name, gif_file, 'image/gif')}
        response = requests.post(API_URL, data=data, files=files)
        if response.status_code == 200:
            result = response.json()
            generated_description = result.get('generated_description', 'No description found.')
        else:
            st.error(f"Failed to generate caption for file: {gif_file.name}. Error: {response.status_code}")
            generated_description = None
    return generated_description

# Function to generate audio from text
def text_to_speech(text):
    client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(language_code='en-US', ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL)
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
    response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
    audio_content = BytesIO(response.audio_content)
    audio_content.seek(0)
    return audio_content

# Function to display GIF and audio
def display_results(gif_data, caption, audio_bytes):
    gif_html = f'<img src="data:image/gif;base64,{base64.b64encode(gif_data).decode()}" alt="GIF" width="500px">'
    st.markdown(gif_html, unsafe_allow_html=True)
    st.write(f"**Generated Caption:** {caption}")
    st.audio(audio_bytes)

# Streamlit app setup
st.set_page_config(page_title="WhatTheGIF?", page_icon="🎤", layout="centered")
st.markdown("<h1 style='text-align: center;'>WhatTheGIF? 🎤</h1>", unsafe_allow_html=True)
st.subheader("GIF Captioning and Audio Generation")


#st.title("WhatTheGif!")
#st.subheader("GIF Captioning and Audio Generation")

# Input options
option = st.radio("Choose an input method:", ("Upload GIFs", "Enter GIF URLs"))

gif_files = []
gif_urls = []

if option == "Upload GIFs":
    uploaded_files = st.file_uploader("Upload one or more GIF files", type=["gif"], accept_multiple_files=True)
    if uploaded_files:
        gif_files = uploaded_files

elif option == "Enter GIF URLs":
    urls = st.text_area("Enter one or more GIF URLs (one per line)")
    if urls:
        gif_urls = [url.strip() for url in urls.splitlines() if url.strip()]

# Generate captions and audio
if st.button("Generate Captions and Audio"):
    with st.spinner("Processing... Please wait."):
        # Process uploaded files
        for idx, gif_file in enumerate(gif_files):
            st.write(f"Processing uploaded GIF {idx + 1}...")
            gif_data = gif_file.read()
            caption = generate_caption(None, gif_file, "Upload GIFs")
            if caption:
                audio_bytes = text_to_speech(caption)
                display_results(gif_data, caption, audio_bytes)

        # Process URLs
        for idx, url in enumerate(gif_urls):
            st.write(f"Processing GIF URL {idx + 1}...")
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    gif_data = response.content
                    caption = generate_caption(url, None, "Enter GIF URLs")
                    if caption:
                        audio_bytes = text_to_speech(caption)
                        display_results(gif_data, caption, audio_bytes)
                else:
                    st.error(f"Failed to fetch GIF from URL: {url}. HTTP Status: {response.status_code}")
            except Exception as e:
                st.error(f"Error fetching GIF from URL: {url}. Error: {e}")

