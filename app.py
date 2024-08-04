import streamlit as st
from audio_recorder_streamlit import audio_recorder
import speech_recognition as sr
from gtts import gTTS
import os
import base64
import tempfile
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up OpenAI API key
api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=api_key)

# Initialize chat history and audio responses
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "latest_audio_response" not in st.session_state:
    st.session_state.latest_audio_response = None

def main():
    st.title("🎤 :red[Urdu Voice Assistant |  اردو وائس اسسٹنٹ] 💬🤖")
    st.subheader("This is a chatbot that listens to your query in Urdu and responds in Urdu. |  یہ ایک چیٹ بوٹ ہے جو آپ کی اردو میں کی گئی بات سنتا ہے اور اردو میں جواب دیتا ہے۔", divider='rainbow')

    urdu_recorder = audio_recorder(text='بولیۓ | Speak',icon_size="2x", icon_name="microphone-lines", key="urdu_recorder")

    if urdu_recorder is not None:
        with st.container():
            col1, col2 = st.columns(2)

            with col2:
                # Display the audio file
                st.header('🧑')
                st.audio(urdu_recorder)

                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_urdu_recording:
                    temp_urdu_recording.write(urdu_recorder)
                    temp_urdu_recording_path = temp_urdu_recording.name
                
                # Convert audio file to text
                text = urdu_audio_to_text(temp_urdu_recording_path)
                st.success(text)

                # Add user query to chat history
                st.session_state.chat_history.append({"role": "user", "content": text})

                # Remove the temporary file
                os.remove(temp_urdu_recording_path)

        response_text = llm_model_response(st.session_state.chat_history)

        # Convert the response text to speech and update the latest audio response
        st.session_state.latest_audio_response = response_to_urdu_audio(response_text)

    # Display chat history
    for message in st.session_state.chat_history:
        if message['role'] == 'user':
            st.write(f"**User:** {message['content']}")
        else:
            st.write(f"**Assistant:** {message['content']}")

    # Display the latest audio response in the assistant's column just above the generated text
    if st.session_state.latest_audio_response:
        with st.container():
            col1, col2 = st.columns(2)
            with col1:
                st.header('🤖')
                audio_placeholder = st.empty()  # Create a placeholder for the latest audio response
                audio_placeholder.markdown(st.session_state.latest_audio_response, unsafe_allow_html=True)
                st.info(response_text)

def urdu_audio_to_text(temp_urdu_recording_path):
    # Speech Recognition
    recognizer = sr.Recognizer()
    with sr.AudioFile(temp_urdu_recording_path) as source:
        urdu_recoded_voice = recognizer.record(source)
        try:
            text = recognizer.recognize_google(urdu_recoded_voice, language="ur")
            return text
        except sr.UnknownValueError:
            return "آپ کی آواز واضح نہیں ہے"
        except sr.RequestError:
            return "Sorry, my speech service is down"

def response_to_urdu_audio(text, lang='ur'):
    tts = gTTS(text=text, lang=lang)
    tts_audio_path = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False).name
    tts.save(tts_audio_path)

    # Get the base64 string of the audio file
    audio_base64 = get_audio_base64(tts_audio_path)

    # Autoplay audio using HTML and JavaScript
    audio_html = f"""
    <audio controls autoplay>
        <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
        Your browser does not support the audio element.
    </audio>
    """
    return audio_html

# Function to encode the audio file to base64
def get_audio_base64(file_path):
    with open(file_path, "rb") as audio_file:
        audio_bytes = audio_file.read()
    return base64.b64encode(audio_bytes).decode()

def llm_model_response(chat_history):
    # Keep the original chat history
    chat_history_without_prompt = [msg for msg in chat_history if msg['role'] != 'system']

    prompt = {"role": "system", "content": """Kindly answer this question in Urdu language. 
    Don't use any other language or characters from other languages.
    Use some kind Urdu words in the start and ending of your answer related to the question. 
    Keep your answer short. 
    You can also ask anything related to the topic in Urdu.
    If you don't know the answer or don't understand the question, 
    Respond with 'I did not get what you speak, please try again' in Urdu."""}

    # Use a temporary history including the prompt for generating the response
    temp_history = chat_history_without_prompt + [prompt]

    response = client.chat.completions.create(
        model="gpt-4",
        messages=temp_history
    )

    assistant_message = response.choices[0].message.content.strip()

    # Add assistant response to chat history
    st.session_state.chat_history.append({"role": "assistant", "content": assistant_message})

    return assistant_message

if __name__ == "__main__":
    main()
