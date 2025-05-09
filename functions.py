import streamlit as st
from google import genai
from google.genai import types
from dotenv import load_dotenv
import fitz  # PyMuPDF
from docx import Document

# Load environment variables from .env
load_dotenv()

# --- Utility Functions ---
def extract_text_from_pdf(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text.strip()

def extract_text_from_docx(file):
    doc = Document(file)
    return "\n".join([para.text for para in doc.paragraphs if para.text.strip()])

def process_document(file):
    if file.type == "application/pdf":
        return extract_text_from_pdf(file)
    elif file.type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
        return extract_text_from_docx(file)

# --- Gemini Setup ---
def setup_gemini_client(api_key: str):
    return genai.Client(api_key=api_key)

def stream_gemini_response(prompt: str, system_prompt: str, api_key: str, model: str):
    client = setup_gemini_client(api_key)
    model = model

    # Include all prior messages for memory backtracking
    contents = [
        types.Content(
            role=msg["role"],
            parts=[types.Part.from_text(text=msg["content"])],
        )
        for msg in st.session_state.messages
    ]

    # Append the current user prompt
    contents.append(
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt)],
        )
    )

    config = types.GenerateContentConfig(
        response_mime_type="text/plain",
        system_instruction=[types.Part.from_text(text=system_prompt)] if system_prompt else None,
    )

    return client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=config,
    )
