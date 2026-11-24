
import os
import streamlit as st
from audiorecorder import audiorecorder
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


def audio_recording(key=None):

    audio = audiorecorder(
        "Click to record",
        "Recording...",
        key=key
    )

    return audio


def transcribe_audio(audio):

    if audio is None or len(audio) == 0:
        return None

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError("GROQ_API_KEY is missing from .env")

    client = Groq(api_key=api_key)

    audio_bytes = audio.export(format="wav").read()

    response = client.audio.transcriptions.create(
        file=("audio.wav", audio_bytes),
        model="whisper-large-v3"
    )

    return response.text
