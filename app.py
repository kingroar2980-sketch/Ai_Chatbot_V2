import streamlit as st
import google.generativeai as genai
import json
import os

# --- 1. CONFIG & BRANDING ---
st.set_page_config(page_title="AI Specialist", page_icon="🤖", layout="wide")

# --- 2. PREMIUM UI (Green Border & Layout) ---
def apply_custom_styles():
    st.markdown("""
        <style>
        /* Main Background */
        .stApp { background-color: #0E1117; color: white; }
        
        /* THE GREEN BORDER FOCUS */
        .stChatInputContainer { 
            border: 1px solid #333 !important; 
            border-radius: 15px !important;
            margin-bottom: 20px;
        }
        .stChatInputContainer:focus-within { 
            border: 2px solid #4CAF50 !important; 
            box-shadow: 0 0 15px rgba(76, 175, 80, 0.4) !important;
        }

        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: #161b22;
            border-right: 1px solid #333;
        }
        
        /* Hide default headers */
        #MainMenu, footer, header { visibility: hidden; }
        </style>
    """, unsafe_allow_html=True)

apply_custom_styles()

# --- 3. DATA PERSISTENCE ---
DB_FILE = "userdata.json"

def load_mem():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f: return json.load(f)
    return {}

def save_mem(data):
    with open(DB_FILE, "w") as f: json.dump(data, f, indent=4)

# --- 4. AI ENGINE SETUP ---
API_KEY = "AIzaSyALgedTNgmjSUMTep61OgMw1PVLvFiB_d0" 
genai.configure(api_key=API_KEY)

@st.cache_resource
def get_ai_brain():
    try:
        # Dynamically find the best working model for your key
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for choice in ['models/gemini-1.5-flash', 'models/gemini-pro', 'models/gemini-1.5-flash-8b']:
            if choice in models: return genai.GenerativeModel(choice)
        return genai.GenerativeModel(models[0])
    except: return None

brain = get_ai_brain()

# --- 5. LEFT SIDEBAR (SETTINGS) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2103/2103633.png", width=80) # Generic AI Icon
    st.title("Settings")
    st.info("System Status: Online")
    
    st.divider()
    
    if st.button("🗑️ Wipe My Memory", use_container_width=True):
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.session_state.messages = []
        st.success("Memory cleared!")
        st.rerun()

    if st.button("🛑 Stop App", use_container_width=True):
        st.session_state.active = False
        st.rerun()

# --- 6. CHAT LOGIC ---
if "active" not in st.session_state: st.session_state.active = True
if "messages" not in st.session_state:
    st.session_state.messages = []
    mem = load_mem()
    user_name = mem.get("name", "")
    if user_name:
        st.session_state.messages.append({"role": "assistant", "content": f"Hello {user_name}! I remember you. How can I help today?"})
    else:
        st.session_state.messages.append({"role": "assistant", "content": "Hello! I am your AI. What's your name?"})

if not st.session_state.active:
    st.error("Session Terminated. Refresh to restart.")
    st.stop()

# Display Chat
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# User Input & Interaction
if prompt := st.chat_input("Message your AI..."):
    # Show User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    if brain:
        current_data = load_mem()
        
        # This prompt FORCES the AI to pay attention to your name and greetings
        system_instructions = f"""
        You are a helpful and polite AI Assistant. 
        Current Memory of User: {current_data}
        
        GUIDELINES:
        1. If the user introduces themselves (e.g., 'My name is...'), respond warmly and say 'I will remember that!' 
        2. If the user says 'Thank you', respond with a polite 'You're welcome!' or 'Happy to help!'
        3. To store a fact in memory, you MUST append [SAVE: key=value] to the end of your response. 
           Example: 'Nice to meet you John! [SAVE: name=John]'
        """
        
        with st.chat_message("assistant"):
            try:
                # Generate AI response
                response = brain.generate_content([system_instructions, prompt])
                full_reply = response.text
                
                # Logic to parse the [SAVE:] command
                if "[SAVE:" in full_reply:
                    clean_text = full_reply.split("[SAVE:")[0].strip()
                    tag = full_reply.split("[SAVE:")[1].replace("]", "").strip()
                    
                    # Update JSON storage
                    try:
                        k, v = tag.split("=")
                        current_data[k.strip()] = v.strip()
                        save_mem(current_data)
                    except: pass
                    
                    st.markdown(clean_text)
                    st.session_state.messages.append({"role": "assistant", "content": clean_text})
                else:
                    st.markdown(full_reply)
                    st.session_state.messages.append({"role": "assistant", "content": full_reply})
                    
            except Exception as e:
                st.error("AI is busy or key is invalid. Try again in a moment.")
    else:
        st.error("Model Error: Your API key might be restricted or starting up.")