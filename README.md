# Video Caption Generator  
This is a **Streamlit web app** that generates captions and keywords for videos. Users can upload their own video files, enter a YouTube URL, or provide a public video link. I have deployed this on Streamlit, check it out here: https://video-caption-generator-using-vertexai-93hrwz79raiappnehbapn3q.streamlit.app/

---

## How to Run `main.py` Locally  
Note that: The `pytube` package has two files, `cipher.py` and `innertube.py`, that cause errors. A fixed version of `pytube` has already been included in the `src` folder.  

1. **Set Up Google API and Credentials**  
   Place your Google API key and credentials in the `.env` file before running the app.  

2. **Run the App**  
   - Navigate to the folder containing the `main.py` file.  
   - Run the following command in the terminal:  
     ```bash
     python -m streamlit run main.py
     ```  

---

## Project Workflow  

1. **Initialize**  
   - The code first loads your **Google API key** and **Google credentials**.  
   - It initializes the **LLM model** (`gemini-1.5-flash`), which needs a GCS (Google Cloud Storage) URL to process media files.  
   - The code also sets up the **GCS bucket name** and **GCS client**.  

2. **Core Functions**  
   The code then defines the following key functions:  
   - **`upload_to_gcs`**:  
     Uploads a video file to a GCS bucket and returns its GCS URL.  
   - **`download_youtube_video`**:  
     Downloads a YouTube video as a temporary file and returns the file path. (Note: A separate function is used for YouTube URLs because YouTube restricts direct video downloads. This function uses the package 'pytube' to handle the downloads.)  
   - **`generate_caption`**:  
     Generates captions for the video based on the GCS URL.  
   - **`generate_keywords`**:  
     Extracts keywords related to the generated captions.  

3. **Video Processing**  
   - Users can choose to:  
     - Upload a video file.  
     - Provide a YouTube URL.  
     - Enter a public video URL.  
   - For each option:  
     - The app downloads the video as a temporary file.  
     - Then uploads the file to GCS using the `upload_to_gcs` function, which provides a GCS URL. (Note: the temporary file is deleted after it has been uploaded) 
     - The GCS URL is inferred by the LLM to generate captions and keywords using `generate_keywords` and `generate_caption`.  
  
## Extra Notes
- I have created a Cloud Run Function on GCP that clears all the uploaded video files in GCS
- Then I used Cloud Scheduler to run the function everyday at 12.00 A.M. Malaysia Time. 
