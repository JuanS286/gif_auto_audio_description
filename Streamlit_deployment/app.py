import torch
from transformers import BlipProcessor, BlipForConditionalGeneration, T5Tokenizer, T5ForConditionalGeneration
from PIL import Image
import requests
from io import BytesIO
import imageio
import numpy as np
import streamlit as st
from gtts import gTTS
import os


# Paths to the model files
t5_model_path = r'C:\Users\aljes\Downloads\Capstone_project_deployment\t5_model.pth'
blip_model_path = r'C:\Users\aljes\Downloads\Capstone_project_deployment\blip_model.pth'

# Set device
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# Load BLIP model and processor
blip_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
blip_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base").to(device)

# Load BLIP model weights with map_location
blip_model.load_state_dict(torch.load(blip_model_path, map_location=device))
blip_model.eval()  # Set the model to evaluation mode

# Load T5 model and tokenizer
t5_tokenizer = T5Tokenizer.from_pretrained("t5-base")
t5_model = T5ForConditionalGeneration.from_pretrained("t5-base").to(device)

# Load T5 model weights with map_location
t5_model.load_state_dict(torch.load(t5_model_path, map_location=device))
t5_model.eval()  # Set the model to evaluation mode

def generate_gif_description(
    gif_url,
    num_frames=5,
    frame_size=(256, 256),
    max_length=128,
    max_target_length=150,
    num_beams=4,
    device=device
):
    """
    Processes an unseen GIF to generate a description.
    """
    # Step 1: Download GIF
    try:
        response = requests.get(gif_url, timeout=10)
        response.raise_for_status()
        gif_bytes = BytesIO(response.content)
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to download GIF: {e}"}

    # Step 2: Extract frames from the GIF
    try:
        gif = imageio.mimread(gif_bytes, memtest=False)
        total_frames = len(gif)
        if total_frames == 0:
            return {"error": "No frames found in the GIF."}
        interval = max(total_frames // num_frames, 1)
        selected_frames = [gif[i] for i in range(0, total_frames, interval)][:num_frames]
    except Exception as e:
        return {"error": f"Error extracting frames from GIF: {e}"}

    # Ensure padding for missing frames
    while len(selected_frames) < num_frames:
        selected_frames.append(np.zeros((frame_size[1], frame_size[0], 3), dtype=np.uint8))
    selected_frames = selected_frames[:num_frames]

    # Step 3: Generate captions for each frame using BLIP
    captions = []
    for frame in selected_frames:
        try:
            img = Image.fromarray(frame).convert('RGB')
            inputs = blip_processor(images=img, return_tensors="pt").to(device)
            with torch.no_grad():
                outputs = blip_model.generate(**inputs, max_length=50)
            captions.append(blip_processor.tokenizer.decode(outputs[0], skip_special_tokens=True))
        except Exception as e:
            captions.append("")

    # Step 4: Concatenate captions for T5 input
    concatenated_captions = " ".join(captions)

    # Step 5: Use T5 to summarize the concatenated captions
    try:
        inputs = t5_tokenizer(
            concatenated_captions, return_tensors="pt", max_length=max_length, truncation=True
        ).to(device)
        with torch.no_grad():
            summary_ids = t5_model.generate(
                inputs["input_ids"],
                max_length=max_target_length,
                num_beams=num_beams,
                early_stopping=True,
            )
        description = t5_tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        return {"description": description, "captions": captions}
    except Exception as e:
        return {"error": f"Failed to generate description: {e}"}

def main():
    st.set_page_config(page_title="GIF Description Generator", page_icon="✨", layout="wide")
    st.markdown(
        "<h1 style='text-align: center; color: #4CAF50;'>GIF Description Generator</h1>",
        unsafe_allow_html=True,
    )
    st.write("Provide a GIF URL, and the app will generate a detailed description.")

    gif_url = st.text_input("Enter the URL of the GIF:", placeholder="Paste the GIF link here")
    if st.button("Generate Description", use_container_width=True):
        if not gif_url:
            st.error("Please provide a GIF URL.")
        else:
            with st.spinner("Generating description... Please wait!"):
                result = generate_gif_description(gif_url, device=device)

            if "error" in result:
                st.error(result["error"])
            else:
                st.success("Description generated successfully!")
                
                # Display the description
                description = result["description"]
                st.subheader("Generated Description")
                st.markdown(
                    f"<div style=padding: 10px; border-radius: 5px;'>"
                    f"<strong>{description}</strong>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

                # Text-to-Speech Conversion
                if st.button("Convert Description to Speech"):
                    if description:
                        tts = gTTS(description, lang='en')
                        audio_file = "output.mp3"
                        tts.save(audio_file)
                        st.success("Audio generated successfully!")

                        # Embed audio player
                        audio_bytes = open(audio_file, "rb").read()
                        st.audio(audio_bytes, format="audio/mp3")
                    else:
                        st.warning("No description available for conversion.")

if __name__ == "__main__":
    main()