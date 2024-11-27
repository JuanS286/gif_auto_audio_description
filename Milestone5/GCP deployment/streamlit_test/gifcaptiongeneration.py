import streamlit as st
import requests
from PIL import Image
import io

# Replace with your actual Cloud Run endpoint URL
API_URL = "https://gif-captioning-app-281207086739.us-central1.run.app/generate_caption"

def main():
    st.title(" GIF Captioning App")
    st.write("Generate descriptive captions for your GIFs to assist visually impaired users.")

    # Input Method Selection
    input_method = st.radio("Select input method:", ("Enter GIF URL", "Upload GIF File"))

    if input_method == "Enter GIF URL":
        gif_url = st.text_input("Enter the URL of the GIF:")
    else:
        gif_file = st.file_uploader("Upload a GIF file", type=["gif"])

    if st.button("Generate Caption"):
        if input_method == "Enter GIF URL":
            if not gif_url:
                st.error("Please enter a valid GIF URL.")
            else:
                with st.spinner('Generating caption...'):
                    try:
                        # Prepare the form data
                        data = {'gif_url': gif_url}
                        
                        # Send POST request to FastAPI endpoint
                        response = requests.post(API_URL, data=data)
                        
                        # Parse JSON response
                        result = response.json()
                        generated_description = result.get('generated_description', 'No description found.')

                        # Display the generated caption
                        st.success(" Caption generated successfully!")
                        st.write("**Generated Description:**")
                        st.write(generated_description)

                    except requests.exceptions.RequestException as e:
                        st.error(f"Error: {e}")

        else:
            if not gif_file:
                st.error("Please upload a GIF file.")
            else:
                # Read the binary content of the uploaded file
                file_bytes = gif_file.read()
                
                # Display uploaded GIF
                try:
                    image = Image.open(io.BytesIO(file_bytes))
                    st.image(image, caption='Uploaded GIF', use_column_width=True)
                except Exception as e:
                    st.error(f"Error displaying image: {e}")
                    return

                # Reset the file pointer to the beginning of the file
                gif_file.seek(0)

                with st.spinner('Generating caption...'):
                    try:
                        # Prepare the form data with empty gif_url and file
                        data = {'gif_url': ''}
                        files = {'file': (gif_file.name, gif_file, 'image/gif')}
                        
                        # Send POST request to FastAPI endpoint with form data and file
                        response = requests.post(API_URL, data=data, files=files)
                        
                        
                        # Parse JSON response
                        result = response.json()
                        generated_description = result.get('generated_description', 'No description found.')

                        # Display the generated caption
                        st.success(" Caption generated successfully!")
                        st.write("**Generated Description:**")
                        st.write(generated_description)

                    except requests.exceptions.RequestException as e:
                        st.error(f"Error: {e}")

if __name__ == "__main__":
    main()
