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
    st.title("⚙️ Settings")

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
            st.session_state.reference_text = process_document(uploaded_file)
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
            if msg["role"] == "user":
                st.write(msg["prompt_text"])
                if msg["file_name"]:
                    st.badge(msg["file_name"], icon="📎", color="gray")
            else:
                st.write(msg["content"])

# --- Chat Input (Text) ---
if prompt := st.chat_input(
    "Say something and/or attach a PDF or DOCX file",
    accept_file=True,
    file_type=["pdf", "docx"],
):
    user_display_text = prompt.text
    message_for_history = prompt.text

    if prompt.files:
        uploaded_file = prompt.files[0]
        file_content = process_document(uploaded_file)

        # Add file content to the message saved in history, not to what is displayed
        message_for_history += f"\n\n[Attached file content from '{uploaded_file.name}']:\n{file_content}"

    # Save full version for assistant processing
    st.session_state.messages.append(
        {
            "role": "user", 
            "file_name": uploaded_file.name if prompt.files else None, 
            "prompt_text": prompt.text,
            "content": message_for_history
         }
    )

    # Render minimal UI for user message
    with st.chat_message("user"):
        if prompt.text:
            st.write(prompt.text)
        if prompt.files:
            st.badge(uploaded_file.name, icon="📎", color="gray")

    # Assistant response
    with st.chat_message("assistant"):
        response_area = st.empty()
        full_response = ""
        try:
            for chunk in stream_gemini_response(message_for_history, full_system_prompt, api_key, model):
                full_response += chunk.text
                response_area.markdown(full_response)
        except genai.errors.ServerError as e:
            full_response = "⚠️ The model is currently overloaded or unavailable. Please try again shortly."
            response_area.markdown(full_response)
        except Exception as e:
            full_response = f"❌ An unexpected error occurred: {e}"
            response_area.markdown(full_response)
        finally:
            st.session_state.messages.append({"role": "assistant", "content": full_response})