import os
import streamlit as st
from vertexai.generative_models._generative_models import SafetySetting
from google.cloud import storage
from langchain_core.messages import HumanMessage
from langchain_google_vertexai import ChatVertexAI
import tempfile
import urllib.request
import base64
from dotenv import load_dotenv
load_dotenv()
import shutil

import sys

# Path to pytube package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'pytube'))

from pytube import YouTube

# Get the base64-encoded JSON key from Streamlit secrets
json_key_base64 = st.secrets["google"]["JSON_KEY"]

# Get API from Streamlit secrets
api = st.secrets["google"]["API"]

# Decode the base64 string to json
json_key = base64.b64decode(json_key_base64)

# Save the decoded JSON key to a temporary file
with open("service-account.json", "wb") as f:
    f.write(json_key)

# Get API and credentials
os.environ['GOOGLE_API_KEY'] = api
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "service-account.json"

# Initialize LLM 
llm = ChatVertexAI(model="gemini-1.5-flash")

# GCS Bucket
BUCKET_NAME = "video-temp-ling" 

# Initialize GCS client
client = storage.Client()

# Function to upload video to GCS
def upload_to_gcs(local_file_path, gcs_file_name):
    # Access the GCS bucket
    bucket = client.get_bucket(BUCKET_NAME)
    blob = bucket.blob(f'videos/{gcs_file_name}')
    
    # Upload the file
    blob.upload_from_filename(local_file_path)  # Waits until the upload is finished

    # Return the GCS URL
    gcs_url = f"gs://{BUCKET_NAME}/videos/{gcs_file_name}"
    return gcs_url

# Download YouTube video temporarily from link
def download_youtube_video(youtube_url):
    try:
        yt = YouTube(youtube_url)

        # Get the first stream 
        video_stream = yt.streams.first()

        # Create temporary file
        fd, temp_file_path = tempfile.mkstemp(suffix='.mp4', dir=os.getcwd())
        
        # Download the video to the temporary file
        video_stream.download(output_path=os.path.dirname(temp_file_path), filename=os.path.basename(temp_file_path))
        print(f"Video downloaded to {temp_file_path}")
        
        # Close the temp file
        os.close(fd)

        return temp_file_path

    except Exception as e:
        st.error(f"Invalid YouTube Link")
        return None

# Generate caption based on the video
def generate_caption(video_url):
    # Prompt for the LLM
    media_message = {
        "type": "media",
        "file_uri": video_url,
        "mime_type": "video/mp4",
    }
    text_message = {
        "type": "text",
        "text": "Provide concise captions that describe the key visuals and actions in the video, giving enough context for the user to understand what is happening. Focus on summarizing the main events or scenes without going too much in detail. Do not include dialogue or subtitles unless they are visually important to the scene.",
    }

    # Execute the prompt
    message = HumanMessage(content=[text_message, media_message])
    response = llm.invoke([message])
    return response.content

# Generate keywords from the caption
def generate_keywords(caption):
    # Prompt for the LLM 
    text_message = {
        "type": "text",
        "text": f"Extract as many keywords and related keywords as possible from this caption: {caption}. Provide only the keywords, separated by commas.",
    }

    # Execute the prompt
    message = HumanMessage(content=text_message["text"])
    response = llm.invoke([message])
    return response.content

#===================================================================================================================================
# Streamlit UI
#===================================================================================================================================
st.title("Video Caption Generator")
st.write("Upload a video, provide a YouTube URL, or enter a public server video URL to generate captions and related keywords.")

# Option to choose input method
option = st.radio("Choose input method:", ["Upload a video", "Enter a YouTube URL", "Enter a Public Server Video URL"])

video_url = None

if option == "Upload a video":
    # Upload video file
    uploaded_file = st.file_uploader("Upload your video", type=["mp4", "mov", "avi"])
    if uploaded_file:
        try:
            # Save the uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
                temp_file.write(uploaded_file.read())
                temp_file_path = temp_file.name
            # Upload the file to GCS bucket
            file_name = f"{uploaded_file.name}"
            video_url = upload_to_gcs(temp_file_path, file_name)
            # Remove the temporary file
            os.remove(temp_file_path)
            # st.success(f"Video uploaded successfully!")
            st.video(uploaded_file)
        except Exception as e:
            st.error(f"Error fetching uploaded video: {e}")

elif option == "Enter a YouTube URL":
    # Enter the URL 
    youtube_url = st.text_input("Enter the YouTube URL")
    if youtube_url:
        # Save the YouTube video temporarily
        temp_video_path = download_youtube_video(youtube_url)
        if temp_video_path:
            # Get file name and upload to GCS
            gcs_file_name = os.path.basename(temp_video_path)
            video_url = upload_to_gcs(temp_video_path, gcs_file_name)
            # Remove the temporary file 
            os.remove(temp_video_path)
            # st.success("Video uploaded successfully!")
            st.video(youtube_url)

elif option == "Enter a Public Server Video URL":
    # Enter the URL
    public_url = st.text_input("Enter the Public Server Video URL")
    if public_url:
        try:
            # Save the video temporarily
            temp_video_path = tempfile.mktemp(suffix=".mp4")
            urllib.request.urlretrieve(public_url, temp_video_path)
            # Get file name and upload to GCS
            gcs_file_name = os.path.basename(public_url)
            video_url = upload_to_gcs(temp_video_path, gcs_file_name)
            # Remove the temporary file
            os.remove(temp_video_path)
            # st.success("Video uploaded successfully!")
            st.video(public_url)
        except Exception as e:
            st.error(f"Error fetching video from URL: {e}")

# Display the button (only after the video_url is set)
if video_url:
    if st.button("Generate Caption and Keywords"):
        with st.spinner("Generating caption and keywords..."):
            try:
                # Generate caption
                caption = generate_caption(video_url)
                st.write(f"**Caption**: {caption}")

                # Generate keywords
                keywords = generate_keywords(caption)
                st.write(f"**Keywords**: {keywords}")
            except Exception as e:
                st.error(f"Error: {e}")

