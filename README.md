# gif_auto_audio_description

## Project Overview
This project aims to generate audio descriptions for GIFs to enhance accessibility for visually impaired individuals. By using machine learning models, such as BLIP for frame captioning and T5 for aggregation, this solution creates descriptive text for GIFs, which is then converted into audio. This project focuses on leveraging advanced ML and natural language processing to provide more inclusive content on the web.

## Installation and Setup Instructions
Follow these steps to set up the project locally:

1. **Clone the repository**:
   ```sh
   git clone https://github.com/JuanS286/gif_auto_audio_description.git

2. **Navigate to the project directory**:
  cd gif_auto_audio_description

3. **Create a virtual environment (recommended)**:
  python -m venv venv

4. **Activate the virtual environment**:
  venv\Scripts\activate

5. **Install the required dependencies**:
  pip install -r requirements.txt

6. **Set up GCP credentials (if applicable)**:
  This project requires access to a Google Cloud Platform bucket for storing processed GIFs and captions. Ensure your credentials are set   up by following the GCP documentation.

## Big Data Systems
This project utilizes a data pipeline to handle and process large GIF datasets. The pipeline is designed to handle data extraction, captioning, aggregation, and storage using Google Cloud Platform. We also optimize the processing of multi-frame GIFs to improve efficiency and manage computational costs.

## Project Board and Tracking
The project is managed through a GitHub Project Board to ensure visibility and accountability. Each task is tracked under To Do, In Progress, and Done columns to make the workflow clear for all team members.

## Challenges Faced
Data Complexity: Multi-frame GIFs required efficient frame extraction and aggregation.<br>
Overfitting: We addressed overfitting through selective layer freezing and hyperparameter tuning.
Computational Constraints: Managed by reducing the number of frames sampled and optimizing model architecture.
