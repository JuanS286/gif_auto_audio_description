#!/usr/bin/env python3

# Disable skimage data caching and downloading by overriding its internal functions

# Set environment variables for skimage and pooch cache directory to a valid writable location
import os
import tempfile

# Use /tmp directory for skimage and pooch cache (this is writable on Dataproc)
os.environ["SKIMAGE_DATADIR"] = "/tmp/skimage_cache"
os.environ["POOCH_CACHE"] = "/tmp/skimage_cache"

# Create the cache directory (ensure it exists)
os.makedirs("/tmp/skimage_cache", exist_ok=True)

# Prevent skimage from using any data directory (disable caching and downloading of resources)
from skimage.data import data_dir
data_dir = None  # Disable any data directory usage

# Disable downloading of additional resources by making download_all a no-op
from skimage.data import download_all
download_all = lambda: None  # No operation for download_all, effectively disabling it

# Import other libraries
import uuid
import json
import random
import requests
import imageio
import cv2
from PIL import Image
from io import BytesIO
import numpy as np
from skimage.metrics import structural_similarity as ssim
from google.cloud import storage
import tempfile

# Spark libraries
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, udf
from pyspark.sql.types import ArrayType, StringType

# Set up Google Cloud Storage client
storage_client = storage.Client()
bucket_name = 'gif-bucket-1000'
bucket = storage_client.bucket(bucket_name)

# Initialize SparkSession with environment variables
spark = SparkSession.builder \
    .appName("GIFProcessing") \
    .config("spark.executorEnv.SKIMAGE_DATADIR", "/tmp/skimage_cache") \
    .config("spark.executorEnv.POOCH_CACHE", "/tmp/skimage_cache") \
    .getOrCreate()

def resize_and_normalize_frame(frame, target_size=(256, 256)):
    """Resize and normalize the frame while preserving aspect ratio."""
    original_height, original_width = frame.shape[:2]
    aspect_ratio = original_width / original_height

    if aspect_ratio > 1:  # Wider than tall
        new_width = target_size[0]
        new_height = int(target_size[0] / aspect_ratio)
    else:  # Taller than wide or square
        new_width = int(target_size[1] * aspect_ratio)
        new_height = target_size[1]

    resized_frame = cv2.resize(frame, (new_width, new_height))

    # Calculate padding
    delta_w = target_size[0] - new_width
    delta_h = target_size[1] - new_height
    top, bottom = delta_h // 2, delta_h - (delta_h // 2)
    left, right = delta_w // 2, delta_w - (delta_w // 2)

    # Add padding to maintain the target size
    normalized_frame = cv2.copyMakeBorder(resized_frame, top, bottom, left, right, cv2.BORDER_CONSTANT, value=[0, 0, 0])
    normalized_frame = normalized_frame.astype(np.float32) / 255.0

    return normalized_frame

def augment_frame(frame):
    """Apply random data augmentation to the frame."""
    if np.random.rand() < 0.5:
        frame = cv2.flip(frame, 1)  # Horizontal flip
    if np.random.rand() < 0.5:
        rows, cols = frame.shape[:2]
        rotation_angle = np.random.randint(-10, 10)
        M = cv2.getRotationMatrix2D((cols/2, rows/2), rotation_angle, 1)
        frame = cv2.warpAffine(frame, M, (cols, rows))
    return frame

def extract_key_frames(frames, ssim_threshold=0.95, min_scene_change=10, max_key_frames=10):  # Changed max_key_frames
    """Extract key frames based on structural similarity."""
    key_frames = []
    prev_frame = None
    scene_change_counter = 0
    scene_changes = []  # Initialize scene_changes here

    for i, frame in enumerate(frames):
        if not isinstance(frame, np.ndarray):
            print(f"Frame {i}: Not a valid NumPy array.")
            continue

        if frame.size == 0 or len(frame.shape) != 3:
            print(f"Frame {i}: Empty or has invalid dimensions: {frame.shape if isinstance(frame, np.ndarray) else 'N/A'}")
            continue

        gray_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)

        if prev_frame is None:
            key_frames.append(frame)
            prev_frame = gray_frame
            continue

        similarity_score = ssim(prev_frame, gray_frame, data_range=1.0)

        if similarity_score < ssim_threshold:
            scene_change_counter += 1
            if scene_change_counter >= min_scene_change and len(key_frames) < max_key_frames:  # Check max_key_frames
                key_frames.append(frame)
                scene_changes.append(i)  # Add index to scene_changes
                scene_change_counter = 0
        else:
            scene_change_counter = 0

        prev_frame = gray_frame

    # Repeat last frame if less than max_key_frames
    while len(key_frames) < max_key_frames:
        key_frames.append(key_frames[-1])

    return key_frames, scene_changes  # Return scene_changes

def process_gif(gif_file_name):
    """Preprocesses a GIF from GCS and extracts 10 key frames."""
    try:
        # Initialize storage client locally
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)

        gif_blob = bucket.blob(os.path.join('gifs', gif_file_name))
        gif_bytes = gif_blob.download_as_bytes()

        with imageio.get_reader(BytesIO(gif_bytes), 'gif') as reader:
            processed_frames = []
            for frame in reader:
                if frame.shape[-1] == 4:
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2RGB)
                resized_frame = resize_and_normalize_frame(frame)
                augmented_frame = augment_frame(resized_frame)
                processed_frames.append(resized_frame)

        key_frames, _ = extract_key_frames(processed_frames)

        return key_frames

    except Exception as e:
        print(f"Error processing GIF {gif_file_name}: {e}")
        return None

# Define UDF for process_gif function
process_gif_udf = udf(process_gif, ArrayType(StringType()))

def generate_data(file_path):
    """Generates target_frames and target_texts from a text file."""
    try:
        # Initialize storage client locally
        storage_client = storage.Client()
        blob = storage_client.bucket(bucket_name).blob(file_path)
        file_content = blob.download_as_string().decode('utf-8')

        # Create a list to store the data
        data = []
        for line in file_content.splitlines():
            gif_file, description = line.strip().split(': ')
            data.append([gif_file + '.gif', description])

        # Create a Spark DataFrame
        df = spark.createDataFrame(data, ["gif_file", "description"])

        # Apply the UDF to the DataFrame
        df = df.withColumn("key_frames", process_gif_udf(col("gif_file")))

        return df

    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        return None

if __name__ == "__main__":
    # Generate data for each split
    train_df = generate_data('train_with_description.txt')
    test_df = generate_data('test_with_description.txt')
    val_df = generate_data('val_with_description.txt')

    # Save the processed DataFrames
    if train_df is not None:
        train_df.write.mode("overwrite").parquet("gs://gif-bucket-1000/output/train/")
    else:
        print("Error: train_df is None, skipping write.")

    if test_df is not None:
        test_df.write.mode("overwrite").parquet("gs://gif-bucket-1000/output/test/")
    else:
        print("Error: test_df is None, skipping write.")

    if val_df is not None:
        val_df.write.mode("overwrite").parquet("gs://gif-bucket-1000/output/val/")
    else:
        print("Error: val_df is None, skipping write.")