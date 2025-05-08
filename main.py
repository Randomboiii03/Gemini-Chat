import streamlit as st
import os
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

# --- Streamlit Setup ---
st.set_page_config(page_title="Gemini Chat", layout="wide")

# --- Session State ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "model" not in st.session_state:
    st.session_state.model = "gemini-2.0-flash-lite"  # Default model
if "base_system_prompt" not in st.session_state:
    st.session_state.base_system_prompt = "You are a helpful assistant."
if "reference_text" not in st.session_state:
    st.session_state.reference_text = ""
if "sidebar_api_key" not in st.session_state:
    st.session_state.sidebar_api_key = ""

# --- Sidebar ---
with st.sidebar:
    st.title("Settings")

    # Model Selection
    st.session_state.model = st.selectbox(
        "💬 Select Gemini Model",
        options=["gemini-2.0-flash-lite", "gemini-2.0-flash", "gemini-1.5-flash-8b", "gemini-1.5-flash", "gemini-1.5-pro"],
        index=0,
    )

    # API Key Input (overrides .env)
    st.session_state.sidebar_api_key = st.text_input("🔑 Gemini API Key", type="password")

    # System Prompt
    st.session_state.base_system_prompt = st.text_area(
        "🧠 Base System Prompt", st.session_state.base_system_prompt, height=120
    )

    # File Upload
    uploaded_file = st.file_uploader("📎 Upload PDF or DOCX for Reference", type=["pdf", "docx"])
    if uploaded_file:
        try:
            if uploaded_file.type == "application/pdf":
                st.session_state.reference_text = extract_text_from_pdf(uploaded_file)
            elif uploaded_file.type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
                st.session_state.reference_text = extract_text_from_docx(uploaded_file)
            st.success("✅ Reference file processed.")
        except Exception as e:
            st.error(f"❌ Error reading file: {e}")

    # Reset
    if st.button("🔄 Reset Chat"):
        st.session_state.messages = []

# Model Selection
model = st.session_state.model  

# Determine API Key to Use
api_key = st.session_state.sidebar_api_key or os.environ.get("GEMINI_API_KEY")
if not api_key:
    st.error("❗ No API key provided. Enter one in the sidebar or define GEMINI_API_KEY in .env.")
    st.stop()

# Final system prompt
full_system_prompt = st.session_state.base_system_prompt
if st.session_state.reference_text:
    full_system_prompt += "\n\nReference Material:\n" + st.session_state.reference_text[:5000]

# --- Display Messages ---
with st.container():
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

# --- Chat Input ---
if prompt := st.chat_input("Say something"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        response_area = st.empty()
        full_response = ""
        for chunk in stream_gemini_response(prompt, full_system_prompt, api_key, model):
            full_response += chunk.text
            response_area.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})
