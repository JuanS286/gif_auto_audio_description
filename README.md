```
# **WhatTheGif?**

This project aims to enhance inclusivity and accessibility in digital content by generating accurate and meaningful textual and audio descriptions for GIFs. The tool utilizes advanced machine learning models and cloud technologies to automate the process of making GIFs accessible to visually impaired users.

## **Project Overview**

*   **Goal:**  The primary goal is to develop a system that automatically generates descriptions for GIFs, making them accessible to visually impaired users. The tool provides descriptions in both text and audio formats and offers bilingual support (English and French) for a broader audience.
*   **Motivation**: In our visually driven digital landscape, millions of visually impaired individuals are often excluded from experiencing content such as GIFs due to a lack of accessible descriptions.

## **Features**

*   **Seamless Accessibility**: The tool converts GIFs into descriptive text and audio, enabling visually impaired users to understand and engage with the content.
*   **Multi-Model Pipeline**: WhatTheGif? employs the BLIP model for frame-level captioning and the T5 model for cohesive narrative generation from the individual captions, ensuring high-quality descriptions that capture both the details and the overall context of the GIF.
*   **Bilingual Output**: The application provides descriptions and audio outputs in both English and French to cater to a wider audience and promote inclusivity.
*   **Interactive and Scalable**: The system is built with a user-friendly interface using Streamlit and is deployed on Google Cloud Run. This ensures smooth operation, scalability to handle varying user loads, and easy access for users.

## **Technical Implementation**

*   **Data Pipeline**: The project uses a robust data pipeline that leverages Google Dataproc and Dask for efficient processing and extraction of key frames from large GIF datasets. This pipeline is designed to handle the volume and complexity of GIF data effectively.
*   **Model Fine-tuning**: The BLIP and T5 models are fine-tuned using insights from interpretability tools like SHAP and LIME. This fine-tuning process significantly improves the accuracy and relevance of the generated descriptions, ensuring a high-quality output.
*   **Deployment**: The application is containerized using Docker and deployed on Google Cloud Run for scalability and reliability. The Streamlit interface provides a user-friendly way to interact with the system.
*   **Accessibility Enhancements**: Bilingual support and audio playback of captions using Google Text-to-Speech are implemented to cater to diverse accessibility needs and provide a more inclusive user experience.

## **Results and Evaluation**

*   The models achieved strong performance on standard metrics, indicating the effectiveness of the approach.
*   For instance, the BLIP model, responsible for frame-level captioning, achieved a BERT F1 score or 0.90. This score demonstrate the model's ability to generate accurate and coherent descriptions.

## **Impact and Use Cases**

WhatTheGif? can be integrated into various platforms, including:

*   Social media platforms to make GIFs more accessible.
*   Educational applications to aid visually impaired students in understanding visual content.
*   News websites to enhance accessibility for all users.

## **Future Directions**

The project aims to expand its functionality in the future:

*   **Support for Other Media Types**: Plans include extending the system to provide descriptions for other visual content such as videos, images, and memes, broadening the tool's applicability and impact.
*   **Real-time Accessibility**: The team aims to integrate the tool with platforms like Twitter and YouTube to provide real-time descriptions for GIFs and other visual content, making these platforms more inclusive for visually impaired users.

## **Project's Significance**

WhatTheGif? represents a significant step towards creating a more inclusive digital environment. It tackles the challenge of making visual content accessible to everyone, regardless of their visual abilities and contributes to a more equitable online experience.

## **Getting Started**

Please refer to the documentation and code in the repository for detailed instructions on installation, setup, and usage.

```
