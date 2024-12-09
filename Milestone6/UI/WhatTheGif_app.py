# This code works with just one GIF. 
# The GIF can be dragged until the app, upload by browsing the files or writing the GIF URL

import streamlit as st
from PIL import Image
import requests
from io import BytesIO
import base64
import time 
from google.cloud import texttospeech
import asyncio
import os

# Set up authentication to the service account key file
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'winter-wonder-442806-e3-93ea92747f60.json'

# Cloud Run endpoint URL
API_URL = "https://gif-captioning-app-281207086739.us-central1.run.app/generate_caption"

# Function to call Model's function to generate caption from image
def generate_caption(gif_url,gif_file, option):

    if option == "Enter GIF URL":
        # Prepare the form data
        data = {'gif_url': gif_url}
        
        # Send POST request to FastAPI endpoint
        response = requests.post(API_URL, data=data)
        
        # Parse JSON response
        result = response.json()
        generated_description = result.get('generated_description', 'No description found.')

        # Display the generated caption
        #st.success(" Caption generated successfully!")
        st.write("**Generated Description:**")
        st.write(generated_description)
    else:
        # Reset the file pointer to the beginning of the file
        gif_file.seek(0)
        # Prepare the form data with empty gif_url and file
        data = {'gif_url': ''}
        files = {'file': (gif_file.name, gif_file, 'image/gif')}
        
        # Send POST request to FastAPI endpoint with form data and file
        response = requests.post(API_URL, data=data, files=files)
                
        # Parse JSON response
        result = response.json()
        generated_description = result.get('generated_description', 'No description found.')

        # Display the generated caption
        #st.success(" Caption generated successfully!")
        st.write("**Generated Description:**")
        st.write(generated_description)       

    return generated_description



def text_to_speech(text):
    client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(language_code='en-US', ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL)
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)

    response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)

    audio_content = BytesIO(response.audio_content)
    audio_content.seek(0)  # Move to the beginning of the audio content in memory
    return audio_content


# Function to display GIF and audio controls
def display_audio(audio_bytes):
    # Display audio with playback controls
    #audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
    audio_html = f"""
    <audio controls>
        <source src="data:audio/wav;base64,{audio_bytes}" type="audio/wav">
        Your browser does not support the audio element.
    </audio>
    """
    #st.markdown(audio_html, unsafe_allow_html=True)
    st.audio(audio_content)
    #st.write(f"Caption: {caption}")

# Streamlit app setup
st.title("WhatTheGif!")
st.subheader("GIF Captioning and Audio Generation")

# Upload or URL option
option = st.radio("Choose an input method:", ("Upload GIF", "Enter GIF URL"))
url= None
gif_file = None
# Load the image
if option == "Upload GIF":
    gif_file = st.file_uploader("Upload a GIF file", type=["gif"])
    if gif_file:
       image = Image.open(gif_file)
       # new
       gif_bytes = gif_file.getvalue()
       gif_html = f'<img src="data:image/gif;base64,{base64.b64encode(gif_bytes).decode()}" alt="GIF" width="500px">'
       st.markdown(gif_html, unsafe_allow_html=True)

elif option == "Enter GIF URL":
    url = st.text_input("Enter the URL of the GIF")
    if url:
        # Display uploaded GIF
        response = requests.get(url)
        image = Image.open(BytesIO(response.content))
        
        gif_html = f'<img src="{url}" alt="GIF" width="50%">'
        st.markdown(gif_html, unsafe_allow_html=True)
        

# Generate caption and audio on button click
if st.button("Generate Caption and Audio"):
    with st.spinner("Processing... Please wait."):
        # Generate caption and audio
        caption = generate_caption(url,gif_file,option)
        audio_content = text_to_speech(caption)
        display_audio(audio_content)


        
       