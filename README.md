# Gemini Chat with Streamlit Interface

An advanced conversational AI web app built with Streamlit and Google's Gemini API. This application supports dynamic system prompts, document uploads for contextual grounding, model selection, and secure manual API key input via the sidebar.

---

## ⚙️ Features

- 💬 Real-time chat with Gemini models via streaming.
- 🧠 Customizable system prompt for assistant behavior.
- 📄 Upload `.pdf` or `.docx` files to inform responses.
- 🔐 Sidebar API key input (overrides `.env`).
- 🔁 Reset chat with a single click.
- 🧠 Session-persistent chat memory.

---

## 📦 Dependencies

Dependencies are managed automatically by `uv`. No manual `pip install` is required.

Ensure you have [uv](https://github.com/astral-sh/uv) installed:

```bash
pip install uv
```

---

## 🔐 API Key Configuration

You can provide the **Gemini API key** in two ways:

1. **Sidebar Input** *(takes precedence)*  
   Enter your key in the "Gemini API Key" field in the app's sidebar.

2. **`.env` File** *(fallback if sidebar input is empty)*  
   Duplicate the included `.env.sample` file and rename it to `.env`.  
   Then add your API key:

   ```env
   GEMINI_API_KEY=your_actual_api_key_here
   ```

---

## 📁 Uploading Reference Material

Enhance the assistant’s contextual understanding by uploading documents:

- **Supported Formats**:
  - `.pdf` — parsed with PyMuPDF
  - `.docx` — parsed with python-docx

Content is injected into the system prompt as reference text.

---

## ▶️ Running the App

Ensure you've prepared your `.env` file.  
Then run the application using:

```bash
uv run --env-file .env streamlit run main.py
```

> Replace `main.py` with your actual script filename if different.

`uv` will automatically install all dependencies defined in the project.

---

## ⚠️ Security Notice

Uploaded content is sent to Google's Gemini API. Do **not** upload sensitive or confidential information.

---

## 📝 Notes

- Make sure `uv` is installed before running the app.
- Copy `.env.sample` → `.env` and update your API key before launch.
- API key input from the sidebar overrides the `.env` value.

---

## 📜 License

MIT — free to use, modify, and distribute with proper credit.

---