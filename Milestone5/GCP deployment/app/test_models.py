# app/test_models.py

import torch
from transformers import BlipForConditionalGeneration, T5ForConditionalGeneration

device = 'cuda' if torch.cuda.is_available() else 'cpu'

try:
    # Load BLIP model
    blip_model = BlipForConditionalGeneration.from_pretrained('Salesforce/blip-image-captioning-base')
    blip_model.load_state_dict(torch.load('models/blip_model.pth', map_location=device))
    blip_model.to(device)
    blip_model.eval()
    print("BLIP model loaded successfully.")

    # Load T5 model
    t5_model = T5ForConditionalGeneration.from_pretrained('t5-base')
    t5_model.load_state_dict(torch.load('models/t5_model.pth', map_location=device))
    t5_model.to(device)
    t5_model.eval()
    print("T5 model loaded successfully.")

except Exception as e:
    print(f"Error loading models: {e}")
