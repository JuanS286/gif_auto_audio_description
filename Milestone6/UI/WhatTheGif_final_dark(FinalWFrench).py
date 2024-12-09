import streamlit as st
from PIL import Image
import requests
from io import BytesIO
import base64
import os
from google.cloud import texttospeech
import validators
from googletrans import Translator  # Import the translator
import base64

# Set up authentication to the service account key file
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'winter-wonder-442806-e3-93ea92747f60.json'

# Cloud Run endpoint URL
API_URL = "https://gif-captioning-app-281207086739.us-central1.run.app/generate_caption"

# Initialize the translator
translator = Translator()

# Function to call Model's function to generate caption from image
def generate_caption(gif_url, gif_file, option):
    if option == "Enter GIF URLs":
        data = {'gif_url': gif_url}
        response = requests.post(API_URL, data=data)
        if response.status_code == 200:
            result = response.json()
            return result.get('generated_description', 'No description found.')
        else:
            st.error(f"Failed to generate caption for URL: {gif_url}. Error: {response.status_code}")
            return None
    else:
        gif_file.seek(0)
        data = {'gif_url': ''}
        files = {'file': (gif_file.name, gif_file, 'image/gif')}
        response = requests.post(API_URL, data=data, files=files)
        if response.status_code == 200:
            result = response.json()
            return result.get('generated_description', 'No description found.')
        else:
            st.error(f"Failed to generate caption for file: {gif_file.name}. Error: {response.status_code}")
            return None

# Function to generate audio from text
def text_to_speech(text, language_code='en-US'):
    client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(language_code=language_code, 
                                              ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL)
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
    response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
    audio_content = BytesIO(response.audio_content)
    audio_content.seek(0)
    return audio_content

# Function to translate text to French
def translate_to_french(text):
    try:
        translated = translator.translate(text, dest='fr')
        return translated.text
    except Exception as e:
        st.error(f"Translation error: {e}")
        return None

# Function to display GIF and audio
def display_results(gif_data, caption, audio_bytes, translated_caption, translated_audio_bytes):
    gif_html = f'<img src="data:image/gif;base64,{base64.b64encode(gif_data).decode()}" alt="GIF" width="25%">'
    st.markdown(gif_html, unsafe_allow_html=True)
    st.write(f"**Generated Caption (EN):** {caption}")
    st.write(f"**Translated Caption (FR):** {translated_caption}")
    
    # Audio outputs with labels
    st.write("**EN Audio:**")
    st.audio(audio_bytes, format='audio/mp3', start_time=0)
    
    st.write("**FR Audio:**")
    st.audio(translated_audio_bytes, format='audio/mp3', start_time=0)

# Function to convert image to base64
def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()

# Set up the Streamlit page configuration
st.set_page_config(page_title="WhatTheGIF?", page_icon="🎤", layout="wide")

# Load the image to get its size
image_path = "WTG.png"
image = Image.open(image_path)

# Get the original width
original_width, _ = image.size

# Center the image using HTML in markdown and set width to 2/3 of the original size
st.markdown(
    f"<div style='text-align: center;'>"
    f"<img src='data:image/png;base64,{image_to_base64(image_path)}' width='{int(original_width * 2 / 3)}' />"
    f"</div>",
    unsafe_allow_html=True
)

# Custom CSS for sidebar and main section
custom_css = """
<style>
body {
    background-color: #121212; /* Dark background */
    color: #e0e0e0; /* Light font for contrast */
    font-size: 20px;
}
.sidebar .sidebar-content {
    background-color: #2e2e2e; /* Slightly lighter sidebar */
    color: #ffffff; /* White font for sidebar */
    font-size: 28px; /* Sidebar font size */
}
.stApp {
    background-color: #121212;
    color: #e0e0e0;
}
h1, h2, h3, h4, h5, h6, label, .stTextInput, .stMarkdown, .stButton, .stRadio {
    color: #e0e0e0; /* Contrast color for headings and text */
    font-size: 28px; /* Larger heading font size */
}
label, .stTextInput, .stMarkdown, .stButton, .stRadio {
    color: #e0e0e0; /* Contrast color for inputs and text */
    font-size: 28px; /* Input and text font size */
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# Sidebar for input
with st.sidebar:
    st.header("Input Options")
    option = st.radio("Choose an input method:", ("Upload GIFs", "Enter GIF URLs"))

    gif_files = []
    gif_urls = []
    valid_urls = []  # Initialize valid URLs list
    invalid_urls = []  # Initialize invalid URLs list

    if option == "Upload GIFs":
        uploaded_files = st.file_uploader("Upload one or more GIF files", type=["gif"], accept_multiple_files=True)
        if uploaded_files:
            gif_files = uploaded_files

    elif option == "Enter GIF URLs":
        urls = st.text_area("Enter one or more GIF URLs (one per line)")
        if urls:
            gif_urls = [url.strip() for url in urls.splitlines() if url.strip()]
            # Validate URLs
            valid_urls = [url for url in gif_urls if validators.url(url)]
            invalid_urls = [url for url in gif_urls if not validators.url(url)]

            if invalid_urls:
                st.warning(f"Invalid URLs detected and will be ignored: {', '.join(invalid_urls)}")

# Main section for results
st.subheader("GIF Captioning and Audio Generation")

if st.button("Generate Captions and Audio"):
    with st.spinner("Processing... Please wait."):
        # Process uploaded files
        for idx, gif_file in enumerate(gif_files):
            st.write(f"Uploaded GIF {idx + 1}...")
            gif_data = gif_file.read()
            caption = generate_caption(None, gif_file, "Upload GIFs")
            if caption:
                translated_caption = translate_to_french(caption)
                audio_bytes = text_to_speech(caption)  # Original caption audio
                translated_audio_bytes = text_to_speech(translated_caption, language_code='fr-FR')  # French audio
                display_results(gif_data, caption, audio_bytes, translated_caption, translated_audio_bytes)

        # Process valid URLs
        for idx, url in enumerate(valid_urls):
            st.write(f"Uploaded GIF URL {idx + 1}...")
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    gif_data = response.content
                    caption = generate_caption(url, None, "Enter GIF URLs")
                    if caption:
                        translated_caption = translate_to_french(caption)  # Translate the caption
                        audio_bytes = text_to_speech(caption)  # Original caption audio
                        translated_audio_bytes = text_to_speech(translated_caption, language_code='fr-FR')  # French audio
                        display_results(gif_data, caption, audio_bytes, translated_caption, translated_audio_bytes)
                else:
                    st.error(f"Failed to fetch GIF from URL: {url}. HTTP Status: {response.status_code}")
            except Exception as e:
                st.error(f"Error fetching GIF from URL: {url}. Error: {e}")