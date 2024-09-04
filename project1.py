import streamlit as st
import speech_recognition as sr
import google.generativeai as genai
from gtts import gTTS
import tempfile
import os
import time

# Replace this with your actual Google API key
GOOGLE_API_KEY = "AIzaSyBo3EB3octfgh_s9hN1Yhepu8SECuaZCOo"

# Initialize recognizer
recognizer = sr.Recognizer()

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "text_to_speak" not in st.session_state:
    st.session_state.text_to_speak = ""
if "audio_file" not in st.session_state:
    st.session_state.audio_file = None
if "play_audio" not in st.session_state:
    st.session_state.play_audio = False
if "processing" not in st.session_state:
    st.session_state.processing = False

def llm(text): 
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(text)
    
    if hasattr(response, 'candidate') and hasattr(response.candidate, 'safety_ratings'):
        if response.candidate.safety_ratings:
            return "The response was blocked due to safety reasons."
    
    if hasattr(response, 'text') and response.text:
        return response.text.lower()
    else:
        return "Sorry, I couldn't generate a response. Please try again."

def recognize_speech_from_microphone(listening_placeholder):
    with sr.Microphone() as source:
        listening_placeholder.info("Listening...")
        recognizer.adjust_for_ambient_noise(source)  # Adjust for background noise
        try:
            audio = recognizer.listen(source, timeout=5)
            text = recognizer.recognize_google(audio)
            st.session_state.chat_history.append(f"You: \n{text}")
            listening_placeholder.empty()  # Clear the "Listening..." message
            return text
        except sr.UnknownValueError:
            listening_placeholder.error("Could not understand the audio")
        except sr.RequestError:
            listening_placeholder.error("Could not request results from the service")
        return None

def generate_audio_file(text):
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
        tts = gTTS(text=text, lang='en')
        tts.save(temp_file.name)
        st.session_state.audio_file = temp_file.name

def auto_play_audio():
    # Embed JavaScript for auto-play with a 3-second delay
    st.markdown("""
        <script>
        setTimeout(function(){
            var audio = document.getElementById("audio");
            if (audio) {
                audio.play();
            }
        }, 3000);
        </script>
    """, unsafe_allow_html=True)

# Streamlit app UI
st.title("Speech-to-Speech Application")

# User interaction for recording speech
st.sidebar.header("Controls")
if st.sidebar.button("🎤 Start Talking"):
    listening_placeholder = st.empty()  # Create a placeholder for the "Listening..." message
    recognized_text = recognize_speech_from_microphone(listening_placeholder)
    if recognized_text:
        st.session_state.processing = True
        with st.spinner("Processing..."):
            processed_text = llm(recognized_text)
            st.session_state.chat_history.append(f"Bot: \n{processed_text}")
            st.session_state.text_to_speak = processed_text
            generate_audio_file(processed_text)
            st.session_state.play_audio = True
        st.session_state.processing = False

# Display chat history
st.subheader("Chat History")
for message in st.session_state.chat_history:
    st.code(message)

# Display processing progress
if st.session_state.processing:
    st.progress(100)  # Full progress bar

# Handle audio playback
if st.session_state.audio_file and st.session_state.play_audio:
    st.subheader("Audio Playback")
    st.audio(st.session_state.audio_file, format="audio/mp3")

    # Use JavaScript for auto-play with a 3-second delay
    auto_play_audio()

    # Clean up the temporary file after playback
    time.sleep(3)  # Ensure file is available for playback
    if os.path.exists(st.session_state.audio_file):
        os.remove(st.session_state.audio_file)
        st.session_state.audio_file = None
        st.session_state.play_audio = False
