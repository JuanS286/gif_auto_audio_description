import streamlit as st
import torch
from transformers import BlipProcessor, BlipForConditionalGeneration, T5Tokenizer, T5ForConditionalGeneration
from PIL import Image
import requests
from io import BytesIO
import imageio
import numpy as np
from gtts import gTTS
import base64

# Paths to the model files
t5_model_path = r'C:\Users\aljes\Downloads\Capstone_project_deployment\t5_model.pth'
blip_model_path = r'C:\Users\aljes\Downloads\Capstone_project_deployment\blip_model.pth'

# Set device
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# Load BLIP model and processor
blip_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
blip_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base").to(device)

blip_model.load_state_dict(torch.load(blip_model_path, map_location=device))
blip_model.eval()  # Set the model to evaluation mode

# Load T5 model and tokenizer
t5_tokenizer = T5Tokenizer.from_pretrained("t5-base")
t5_model = T5ForConditionalGeneration.from_pretrained("t5-base").to(device)

t5_model.load_state_dict(torch.load(t5_model_path, map_location=device))
t5_model.eval()  # Set the model to evaluation mode


def generate_gif_description(gif_path, num_frames=5, frame_size=(256, 256), max_length=128, max_target_length=150, num_beams=4):
    """Processes an unseen GIF to generate a description."""
    try:
        gif = imageio.mimread(gif_path)
        total_frames = len(gif)
        if total_frames == 0:
            return {"error": "No frames found in the GIF."}

        interval = max(total_frames // num_frames, 1)
        selected_frames = [gif[i] for i in range(0, total_frames, interval)][:num_frames]

        # Ensure padding for missing frames
        while len(selected_frames) < num_frames:
            selected_frames.append(np.zeros((frame_size[1], frame_size[0], 3), dtype=np.uint8))
        selected_frames = selected_frames[:num_frames]

        # Generate captions for each frame using BLIP
        captions = []
        for frame in selected_frames:
            img = Image.fromarray(frame).convert('RGB')
            inputs = blip_processor(images=img, return_tensors="pt").to(device)
            with torch.no_grad():
                outputs = blip_model.generate(**inputs, max_length=50)
            captions.append(blip_processor.tokenizer.decode(outputs[0], skip_special_tokens=True))

        # Concatenate captions for T5 input
        concatenated_captions = " ".join(captions)

        # Use T5 to summarize the concatenated captions
        inputs = t5_tokenizer(concatenated_captions, return_tensors="pt", max_length=max_length, truncation=True).to(device)
        with torch.no_grad():
            summary_ids = t5_model.generate(
                inputs["input_ids"], max_length=max_target_length, num_beams=num_beams, early_stopping=True
            )
        description = t5_tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        return {"description": description, "captions": captions}
    except Exception as e:
        return {"error": f"Error processing GIF: {e}"}


def main():
    st.set_page_config(page_title="GIF Description Generator", page_icon="✨", layout="wide")
    st.markdown("<h1 style='text-align: center; color: #4CAF50;'>GIF Description Generator</h1>", unsafe_allow_html=True)
    st.write("Upload a GIF or provide a GIF URL to generate a detailed description.")

    # Choose input method
    input_method = st.radio("Select input method:", ["Upload GIF", "Paste GIF URL"], index=0)

    gif_path = None
    if input_method == "Upload GIF":
        uploaded_file = st.file_uploader("Upload your GIF file:", type=["gif"])
        if uploaded_file:
            gif_path = BytesIO(uploaded_file.read())
            st.image(uploaded_file, caption="Uploaded GIF", use_column_width=True, output_format="auto")
    else:
        gif_url = st.text_input("Enter the URL of the GIF:", placeholder="Paste the GIF link here")
        if gif_url:
            try:
                response = requests.get(gif_url, timeout=10)
                response.raise_for_status()
                gif_path = BytesIO(response.content)
                st.image(gif_url, caption="GIF from URL", use_column_width=True, output_format="auto")
            except Exception as e:
                st.error(f"Error fetching GIF from URL: {e}")

    if st.button("Generate Description"):
        if not gif_path:
            st.error("Please upload a GIF or provide a valid URL.")
        else:
            with st.spinner("Generating description... Please wait!"):
                result = generate_gif_description(gif_path)

            if "error" in result:
                st.error(result["error"])
            else:
                st.success("Description generated successfully!")
                description = result["description"]
                st.subheader("Description")
                st.code(description, language="text")

                # Generate audio from the description
                tts = gTTS(description, lang="en")
                audio_buffer = BytesIO()
                tts.write_to_fp(audio_buffer)
                audio_buffer.seek(0)

                # Encode audio to base64
                audio_base64 = base64.b64encode(audio_buffer.getvalue()).decode("utf-8")
                st.subheader("Play Description Audio")
                st.markdown(
                    f"""
                    <audio controls>
                        <source src="data:audio/mpeg;base64,{audio_base64}" type="audio/mpeg">
                        Your browser does not support the audio element.
                    </audio>
                    """,
                    unsafe_allow_html=True,
                )


if __name__ == "__main__":
    main()
