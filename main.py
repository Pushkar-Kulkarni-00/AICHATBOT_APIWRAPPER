from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
import streamlit as st
from dotenv import load_dotenv
from pypdf import PdfReader
import os
import time
import csv
import io

load_dotenv()
apikey = os.getenv("apikey")

st.title('AI CHATBOT')

st.markdown("""
    <style>
    div[data-testid="stFileUploader"] {
        position: fixed;
        bottom: 22px;
        left: 330px;
        width: 44px;
        height: 44px;
        z-index: 1000;
    }
    div[data-testid="stFileUploader"] section {
        padding: 0;
        border: none;
        background: transparent;
    }
    div[data-testid="stFileUploader"] section > div {
        display: none;
    }
    div[data-testid="stFileUploader"] section button {
        width: 44px !important;
        height: 44px !important;
        border-radius: 50% !important;
        padding: 0 !important;
        background-color: #3a3a3a !important;
        color: transparent !important;
        border: none !important;
        cursor: pointer !important;
        font-size: 0 !important;
        position: relative !important;
    }
    div[data-testid="stFileUploader"] section button::after {
        content: "+";
        color: white;
        font-size: 26px;
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
    }
    div[data-testid="stFileUploader"] section button:hover {
        background-color: #555 !important;
    }
    div[data-testid="stFileUploader"] label {
        display: none;
    }
    div[data-testid="stSelectbox"] {
        position: fixed;
        bottom: 70px;
        right: 16px;
        width: 200px;
        z-index: 999;
        background: #1e1e1e;
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)

model_options = {
    "nvidia/nemotron-3-nano-30b-a3b:free": "Nvidia Nemotron Nano",
    "meta-llama/llama-3.1-8b-instruct:free": "LLaMA 3.1 8B",
    "meta-llama/llama-3.3-70b-instruct:free": "LLaMA 3.3 70B",
    "nvidia/nemotron-super-120b-a12b:free": "Nvidia Nemotron",
    "moonshotai/kimi-k2.6:free": "MoonShot AI - Kimi",
    "qwen/qwen3-next-80b-a3b-instruct:free": "Qwen 3",
}

selected_model = st.selectbox(
    "Model",
    options=list(model_options.keys()),
    format_func=lambda x: model_options[x],
    label_visibility="collapsed"
)

uploaded_file = st.file_uploader(
    "+",
    type=["pdf", "png", "jpg", "jpeg", "txt", "csv", "docx"],
    label_visibility="collapsed"
)

def extract_context(file):
    name = file.name.lower()
    
    if name.endswith(".pdf"):
        reader = PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return ("text", f"PDF content:\n{text[:12000]}")

    elif name.endswith(".txt"):
        text = file.read().decode("utf-8", errors="ignore")
        return ("text", f"Text file content:\n{text[:12000]}")

    elif name.endswith(".csv"):
        content = file.read().decode("utf-8", errors="ignore")
        reader = csv.reader(io.StringIO(content))
        rows = []
        for i, row in enumerate(reader):
            rows.append(", ".join(row))
            if i > 200:  # cap at 200 rows
                rows.append("... (truncated)")
                break
        return ("text", f"CSV content:\n" + "\n".join(rows))

    elif name.endswith(".docx"):
        try:
            import docx
            doc = docx.Document(file)
            text = "\n".join([p.text for p in doc.paragraphs])
            return ("text", f"Document content:\n{text[:12000]}")
        except ImportError:
            return ("text", "Error: python-docx not installed. Run: pip install python-docx")

    elif name.endswith((".png", ".jpg", ".jpeg")):
        import base64
        bytes_data = file.read()
        b64 = base64.b64encode(bytes_data).decode()
        ext = name.split(".")[-1]
        media_type = f"image/{'jpeg' if ext == 'jpg' else ext}"
        return ("image", (b64, media_type))

    return ("text", "Unsupported file type.")

file_context = None
file_type = None

if uploaded_file:
    file_type, file_context = extract_context(uploaded_file)
    if file_type == "text":
        st.toast(f"✅ {uploaded_file.name} loaded")
    elif file_type == "image":
        st.toast(f"✅ Image loaded: {uploaded_file.name}")

llm = ChatOpenAI(
    openai_api_base="https://openrouter.ai/api/v1",
    openai_api_key=apikey,
    model_name=selected_model,
    temperature=0.5,
    max_tokens=500,
    streaming=True,
)

if 'messages' not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    st.chat_message(message['role']).markdown(message['content'])

prompt = st.chat_input('Pass your prompt here:')

if prompt:
    st.chat_message('user').markdown(prompt)
    st.session_state.messages.append({'role': 'user', 'content': prompt})

    history = []

    # Inject file context
    if file_type == "text" and file_context:
        history.append(SystemMessage(content=f"Use the following file content to answer questions:\n\n{file_context}"))

    for m in st.session_state.messages:
        if m['role'] == 'user':
            history.append(HumanMessage(content=m['content']))
        else:
            history.append(AIMessage(content=m['content']))

    # For images, replace last HumanMessage with multimodal content
    if file_type == "image" and file_context:
        b64, media_type = file_context
        history[-1] = HumanMessage(content=[
            {"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{b64}"}},
            {"type": "text", "text": prompt}
        ])

    with st.chat_message('assistant'):
        thinking = st.empty()
        thinking.markdown("● ● ●")

        full_response = ""
        first = True

        for attempt in range(3):
            try:
                stream = llm.stream(history)
                for chunk in stream:
                    if first:
                        thinking.empty()
                        first = False
                    full_response += chunk.content
                    thinking.markdown(full_response + "▌")
                break
            except Exception as e:
                if "429" in str(e) and attempt < 2:
                    thinking.markdown(f"● ● ● Rate limited, retrying in 30s... ({attempt+1}/3)")
                    time.sleep(30)
                else:
                    thinking.markdown(f"Error: {str(e)}")
                    break

        thinking.markdown(full_response)

    st.session_state.messages.append({'role': 'assistant', 'content': full_response})