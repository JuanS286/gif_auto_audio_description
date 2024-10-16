import os
import json

# Define the path to your input dataset file
input_file_path = 'tgif-v2.0.txt'  # Ensure this file is uploaded to your Colab environment

# Define the path to your output data file
output_file_path = 'datafile.json'  # This file will be created in the current directory

# Initialize an empty list to hold all GIF entries
gif_data = []

# Open and read the input dataset file
with open(input_file_path, 'r') as file:
    # Read all lines from the file
    lines = file.readlines()

    # Iterate over each line in the dataset with enumeration for numbering
    for index, line in enumerate(lines, start=1):
        # Strip any leading/trailing whitespace characters (like newline)
        stripped_line = line.strip()

        # Skip empty lines to avoid processing errors
        if not stripped_line:
            print(f"Skipping empty line at line number {index}.")
            continue

        # Split the line into two parts: URL and description
        # Use split with no arguments to split on any whitespace (space, tab, etc.)
        parts = stripped_line.split(None, 2)

        # Check if the line has both URL and description
        if len(parts) != 3:
            print(f"Line {index} is malformed: '{stripped_line}'")
            continue  # Skip this line and move to the next

        # Extract URL and description from the split parts
        id, url, description = parts

        # Validate URL ends with '.gif'
        if not url.lower().endswith('.gif'):
            print(f"Line {index} has invalid GIF URL: '{url}'")
            continue  # Skip invalid GIF URLs

        # Generate a simple unique identifier in the format 'gif_{number}'
        unique_id = f"gif_{id}"

        # Create a dictionary for the current GIF with its unique ID, URL, and description
        gif_entry = {
            "id": unique_id,            # Simple unique identifier (e.g., 'gif_1')
            "url": url,                 # URL of the GIF
            "description": description  # Description of the GIF
        }

        # Append the current GIF's data to the list
        gif_data.append(gif_entry)

        # Optional: Print progress every 1000 entries for large datasets
        if index % 1000 == 0:
            print(f"Processed {index} lines.")

# After processing all lines, write the structured data to the output file
with open(output_file_path, 'w') as outfile:
    # Dump the list of GIF data into the JSON file with indentation for readability
    json.dump(gif_data, outfile, indent=4)

# Final confirmation message with the total number of entries processed
print(f"\nData file '{output_file_path}' has been created with {len(gif_data)} entries.")
