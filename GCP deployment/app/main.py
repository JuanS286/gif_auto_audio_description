# app/main.py

# app/main.py

import os
import torch
import logging
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from transformers import BlipProcessor, BlipForConditionalGeneration, T5Tokenizer, T5ForConditionalGeneration
from PIL import Image
import imageio
from io import BytesIO
import numpy as np
import requests
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="GIF Captioning API",
    description="Generate captions for GIFs to assist visually impaired users.",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    logger.info("Application is starting up...")
    try:
        # Define device
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        logger.info(f"Using device: {device}")
        
        # Initialize processors and tokenizers
        blip_processor = BlipProcessor.from_pretrained('Salesforce/blip-image-captioning-base')
        t5_tokenizer = T5Tokenizer.from_pretrained('t5-base')
        logger.info("Processors and tokenizers loaded successfully.")
        
        # Initialize model architectures
        blip_model = BlipForConditionalGeneration.from_pretrained('Salesforce/blip-image-captioning-base')
        t5_model = T5ForConditionalGeneration.from_pretrained('t5-base')
        logger.info("Model architectures loaded successfully.")
        
        # Determine the base directory using pathlib
        BASE_DIR = Path(__file__).resolve().parent
        
        # Construct the paths to the model files
        blip_model_path = BASE_DIR / 'models' / 'blip_model.pth'
        t5_model_path = BASE_DIR / 'models' / 't5_model.pth'
        
        # Load trained state_dicts
        blip_model.load_state_dict(torch.load(blip_model_path, map_location=device, weights_only=False))
        t5_model.load_state_dict(torch.load(t5_model_path, map_location=device, weights_only=False))
        logger.info("Model state_dicts loaded successfully.")
        
        # Move models to device
        blip_model.to(device)
        t5_model.to(device)
        logger.info("Models moved to device.")
        
        # Set models to evaluation mode
        blip_model.eval()
        t5_model.eval()
        logger.info("Models set to evaluation mode.")
        
        # Attach models and processors to app state for access in endpoints
        app.state.blip_model = blip_model
        app.state.t5_model = t5_model
        app.state.blip_processor = blip_processor
        app.state.t5_tokenizer = t5_tokenizer
        app.state.device = device
        
        logger.info("Startup process completed successfully.")
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise e

@app.post("/generate_caption", summary="Generate caption for a GIF", response_description="The generated caption and related information")
async def generate_caption(
    gif_url: str = Form(None, description="URL of the GIF to caption"),
    file: UploadFile = File(None, description="Upload a GIF file")
):
    """
    Generate a caption for an uploaded GIF or a GIF from a URL.
    """
    try:
        # Access models and processors from app.state
        blip_model = app.state.blip_model
        t5_model = app.state.t5_model
        blip_processor = app.state.blip_processor
        t5_tokenizer = app.state.t5_tokenizer
        device = app.state.device

        # Step 1: Obtain GIF bytes
        if gif_url:
            response = requests.get(gif_url, timeout=10)
            response.raise_for_status()
            gif_bytes = BytesIO(response.content)
        elif file:
            contents = await file.read()
            gif_bytes = BytesIO(contents)
        else:
            raise HTTPException(status_code=400, detail="Either 'gif_url' or 'file' must be provided.")

        # Step 2: Extract frames from the GIF
        gif = imageio.mimread(gif_bytes, memtest=False)
        total_frames = len(gif)
        num_frames = 5
        if total_frames == 0:
            raise HTTPException(status_code=400, detail="No frames found in the GIF.")
        interval = max(total_frames // num_frames, 1)
        selected_frames = [gif[i] for i in range(0, total_frames, interval)][:num_frames]

        # Step 3: Ensure exactly num_frames by padding if necessary
        while len(selected_frames) < num_frames:
            if selected_frames:
                selected_frames.append(selected_frames[-1])
            else:
                selected_frames.append(np.zeros((256, 256, 3), dtype=np.uint8))
        selected_frames = selected_frames[:num_frames]

        # Step 4: Generate captions using BLIP
        captions = []
        for frame in selected_frames:
            img = Image.fromarray(frame).convert('RGB')
            img_resized = img.resize((256, 256))
            inputs = blip_processor(img_resized, return_tensors="pt").to(device)
            with torch.no_grad():
                outputs = blip_model.generate(**inputs, max_length=50)
            caption = blip_processor.decode(outputs[0], skip_special_tokens=True)
            captions.append(caption)

        # Step 5: Concatenate captions
        concatenated_captions = " ".join(captions)

        # Step 6: Tokenize for T5
        encoding = t5_tokenizer.encode_plus(
            concatenated_captions,
            add_special_tokens=True,
            max_length=128,
            padding='max_length',
            truncation=True,
            return_attention_mask=True,
            return_tensors='pt',
        )
        input_ids = encoding['input_ids'].to(device)
        attention_mask = encoding['attention_mask'].to(device)

        # Step 7: Generate description using T5
        with torch.no_grad():
            outputs = t5_model.generate(
                input_ids=input_ids,
                attention_mask=attention_mask,
                max_length=150,
                num_beams=4,
                early_stopping=True
            )
        generated_description = t5_tokenizer.decode(outputs[0], skip_special_tokens=True)

        return JSONResponse(content={
            'generated_description': generated_description
        })

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Failed to download GIF: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
