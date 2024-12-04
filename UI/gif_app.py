import streamlit as st
from PIL import Image
import requests
from io import BytesIO
import base64
import time

# Placeholder functions for generating caption and audio
def generate_caption(image):
    # Simulate caption generation process
    time.sleep(3)  # Simulate processing time
    return "A sample generated caption for the GIF."

def generate_audio(text):
    # Simulate audio synthesis process
    time.sleep(2)  # Simulate processing time
    audio_data = BytesIO()
    audio_data.write(b"RIFF....")  # Placeholder; replace with actual audio bytes
    audio_data.seek(0)
    return audio_data

# Function to display audio and GIFs
def display_audio_and_caption(gif_data, audio_bytes, caption, index):
    gif_html = f'<img src="data:image/gif;base64,{base64.b64encode(gif_data).decode()}" alt="GIF {index + 1}" style="max-width: 100%; height: auto;">'
    st.markdown(gif_html, unsafe_allow_html=True)

    audio_base64 = base64.b64encode(audio_bytes.read()).decode('utf-8')
    audio_html = f"""
    <audio controls>
        <source src="data:audio/wav;base64,{audio_base64}" type="audio/wav">
        Your browser does not support the audio element.
    </audio>
    """
    st.markdown(audio_html, unsafe_allow_html=True)
    st.write(f"Caption: {caption}")

# Streamlit app setup
st.title("WhatTheGif!")
st.subheader("GIF Captioning and Audio Generation")

# Upload or URL input option
option = st.radio("Choose an input method:", ("Upload GIFs", "Enter GIF URLs"))

images = []  # List to store images

if option == "Upload GIFs":
    uploaded_files = st.file_uploader("Upload one or more GIF files", type=["gif"], accept_multiple_files=True)
    if uploaded_files:
        for file in uploaded_files:
            images.append(file.read())
            #images.append(Image.open(file))

elif option == "Enter GIF URLs":
    urls = st.text_area("Enter one or more GIF URLs (one per line)")
    if urls:
        for url in urls.splitlines():
            try:
                response = requests.get(url.strip())
                if response.status_code == 200:
                    images.append(response.content)
                    #images.append(Image.open(BytesIO(response.content)))
            except Exception as e:
                st.error(f"Failed to load GIF from URL: {url}. Error: {e}")

# Process each GIF
if images:
    if st.button("Generate Captions and Audio"):
        with st.spinner("Processing all GIFs... Please wait."):
            for index, image in enumerate(images):
                st.write(f"Processing GIF {index + 1}...")
                caption = generate_caption(image)
                audio_bytes = generate_audio(caption)
                display_audio_and_caption(image, audio_bytes, caption, index)
else:
    st.info("Please upload or provide at least one GIF.")
