import os
import json
import random
import requests
from google.cloud import storage
from tqdm import tqdm

# Configuration
GCS_BUCKET_NAME = 'juanmodeltry2'  # Replace with your GCS bucket name if different
GCS_METADATA_PATH = 'metadata.json'  # Path to metadata.json within the bucket
GCS_DESTINATION_FOLDER = 'gifs/'  # Destination folder in the bucket for GIFs
LOCAL_DOWNLOAD_FOLDER = 'downloaded_gifs/'  # Temporary local folder
SAMPLE_SIZE = 1000
TRAIN_SPLIT = 800
VAL_SPLIT = 100
TEST_SPLIT = 100

# Split files
TRAIN_SPLIT_FILE = 'train.txt'
VAL_SPLIT_FILE = 'val.txt'
TEST_SPLIT_FILE = 'test.txt'

def ensure_dir(directory):
    """Ensure that a directory exists."""
    if not os.path.exists(directory):
        os.makedirs(directory)

def download_file_from_gcs(bucket, source_blob_name, destination_file_name):
    """Download a file from GCS to a local destination."""
    blob = bucket.blob(source_blob_name)
    if not blob.exists():
        raise FileNotFoundError(f"{source_blob_name} not found in bucket {bucket.name}.")
    blob.download_to_filename(destination_file_name)
    print(f"Downloaded {source_blob_name} to {destination_file_name}")

def load_metadata(json_path):
    """Load metadata from a local JSON file."""
    with open(json_path, 'r') as f:
        data = json.load(f)
    return data

def sample_gifs(data, sample_size):
    """Randomly sample a specified number of GIFs."""
    return random.sample(data, sample_size)

def split_gifs(sampled_gifs, train, val, test):
    """Split sampled GIFs into train, val, and test sets."""
    train_gifs = sampled_gifs[:train]
    val_gifs = sampled_gifs[train:train+val]
    test_gifs = sampled_gifs[train+val:train+val+test]
    return train_gifs, val_gifs, test_gifs

def download_gif(url, dest_path):
    """Download a GIF from a URL to a local path."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        with open(dest_path, 'wb') as f:
            f.write(response.content)
        return True
    except Exception as e:
        print(f"Failed to download {url}: {e}")
        return False

def upload_to_gcs(bucket, source_file, destination_blob):
    """Upload a local file to GCS."""
    try:
        blob = bucket.blob(destination_blob)
        blob.upload_from_filename(source_file)
        return True
    except Exception as e:
        print(f"Failed to upload {source_file} to {destination_blob}: {e}")
        return False

def write_split_file(split_file, gif_filenames):
    """Write a list of GIF filenames to a split text file."""
    with open(split_file, 'w') as f:
        for filename in gif_filenames:
            f.write(f"{filename}\n")

def main():
    # Step 1: Setup local directories
    ensure_dir(LOCAL_DOWNLOAD_FOLDER)

    # Step 2: Initialize GCS client and bucket
    print("Initializing Google Cloud Storage client...")
    client = storage.Client()
    bucket = client.bucket(GCS_BUCKET_NAME)
    if not bucket.exists():
        print(f"Bucket {GCS_BUCKET_NAME} does not exist.")
        return

    # Step 3: Download metadata.json from GCS
    print("Downloading metadata.json from GCS...")
    local_metadata_path = os.path.join('.', 'metadata.json')
    download_file_from_gcs(bucket, GCS_METADATA_PATH, local_metadata_path)

    # Step 4: Load metadata
    print("Loading metadata...")
    metadata = load_metadata(local_metadata_path)
    print(f"Total GIFs available in metadata: {len(metadata)}")
    
    if len(metadata) < SAMPLE_SIZE:
        print(f"Not enough GIFs in metadata. Required: {SAMPLE_SIZE}, Available: {len(metadata)}")
        return

    # Step 5: Sample GIFs
    print(f"Sampling {SAMPLE_SIZE} GIFs...")
    sampled_gifs = sample_gifs(metadata, SAMPLE_SIZE)

    # Step 6: Split GIFs
    train_gifs, val_gifs, test_gifs = split_gifs(sampled_gifs, TRAIN_SPLIT, VAL_SPLIT, TEST_SPLIT)
    print(f"Training GIFs: {len(train_gifs)}, Validation GIFs: {len(val_gifs)}, Testing GIFs: {len(test_gifs)}")

    # Step 7: Upload all GIFs to 'gifs/' folder in GCS
    print("Uploading GIFs to GCS...")
    for gif in tqdm(sampled_gifs, desc="Uploading GIFs"):
        gif_id = gif['id']
        url = gif['url']
        gif_filename = f"{gif_id}.gif"
        local_path = os.path.join(LOCAL_DOWNLOAD_FOLDER, gif_filename)
        gcs_path = os.path.join(GCS_DESTINATION_FOLDER, gif_filename)

        # Download GIF locally
        success = download_gif(url, local_path)
        if not success:
            continue  # Skip to next GIF if download failed

        # Upload GIF to GCS
        success = upload_to_gcs(bucket, local_path, gcs_path)
        if success:
            pass  # GIF uploaded successfully
        else:
            print(f"Failed to upload {gif_filename} to GCS.")

        # Remove local file after upload to save space
        os.remove(local_path)

    # Step 8: Write split files
    print("Writing split text files...")
    train_filenames = [f"{gif['id']}.gif" for gif in train_gifs]
    val_filenames = [f"{gif['id']}.gif" for gif in val_gifs]
    test_filenames = [f"{gif['id']}.gif" for gif in test_gifs]

    write_split_file(TRAIN_SPLIT_FILE, train_filenames)
    write_split_file(VAL_SPLIT_FILE, val_filenames)
    write_split_file(TEST_SPLIT_FILE, test_filenames)

    # Step 9: Upload split files to main bucket folder
    print("Uploading split text files to GCS...")
    split_files = {
        'train.txt': TRAIN_SPLIT_FILE,
        'val.txt': VAL_SPLIT_FILE,
        'test.txt': TEST_SPLIT_FILE
    }

    for split_name, split_file in split_files.items():
        gcs_split_path = split_file  # Upload directly to the main bucket folder
        success = upload_to_gcs(bucket, split_file, gcs_split_path)
        if success:
            os.remove(split_file)  # Remove local split file after upload
            print(f"Uploaded and removed {split_file}")
        else:
            print(f"Failed to upload {split_file} to GCS.")

    # Cleanup: Remove local metadata file
    os.remove(local_metadata_path)

    print("All tasks completed successfully!")

if __name__ == "__main__":
    main()
