# app.py
import streamlit as st
from datetime import datetime, timedelta,timezone
import requests
import time
import uuid
import smtplib
from email.message import EmailMessage
from PIL import Image,UnidentifiedImageError


icon =Image.open("assets/dkut_logo.ico")
st.set_page_config(page_title="DEKAI", layout="wide", initial_sidebar_state="collapsed",page_icon=icon)
st.sidebar.image("assets/dkut_logo.ico", width=350)
query_params = st.query_params

if "token" in query_params:
    st.session_state.logged_in = True
    st.session_state.user = {
        "access_token": query_params["token"],
        "email": query_params.get("email"),
        "name": query_params.get("name"),
    }


# -------------------------
# Styling 
# -------------------------
st.markdown(
    """
<style>

textarea {
        text-transform: none !important;
        autocorrect: off !important;
        autocapitalize: off !important;
        spellcheck: false !important;
    }
/* page background */
.main > div.block-container{padding-left:1rem; padding-right:1rem;}
body { background: #F7FBFA; }

/* Chat bubbles */
.dekai-user {
  background: #2f5dd9;
  color: white;
  padding: 10px 14px;
  border-radius: 16px;
  max-width: 78%;
  margin-left: auto;
  margin-bottom: 8px;
}
.link {
    color: #1e88e5;
    text-decoration: none;
    cursor: pointer;
 }
.link:hover {
    text-decoration: underline
}

.dekai-assistant {
  background: #eef2f3;
  color: #0f172a;
  padding: 10px 14px;
  border-radius: 16px;
  max-width: 78%;
  margin-right: auto;
  margin-bottom: 8px;
}
.small-muted { font-size:12px; color:#6b7280; }
.header {
  display:flex;
  align-items:center;
  justify-content:space-between;
  padding: 8px 0;
}
.kbd {
  font-size:12px;
  color:#6b7280;
}
.chat-area {
  height: 64vh;
  overflow-y: auto;
  padding: 12px;
}
.input-area {
  padding: 8px;
}
.menu-item { padding: 10px 6px; }
.green-bg { background: #0a7a3b; color: white; padding: 8px; border-radius: 4px; }
</style>

<script>
 window.addEventListener('message', (event) => {
        if (event.data.type === 'NAV_SIGNUP') {
            window.parent.location.reload();
        }
    });

window.addEventListener('message', (event) => {
        if (event.data.type === 'NAV_SIGNUP') {
            const streamlitDoc = window.parent.document;
            streamlitDoc.dispatchEvent(new CustomEvent('streamlit:setComponentValue', {detail: {value: 'Sign Up'}}));
        }
    });
</script>
""",
    unsafe_allow_html=True,
)

def send_bug_email(subject, body):
    msg = EmailMessage()
    msg["From"] = "dekai-bug-reporter"
    msg["To"] = DEKAI_EMAIL
    msg["Subject"] = f"[DEKAI Bug Report] {subject}"
    msg.set_content(body)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(
                st.secrets["EMAIL_USER"],
                st.secrets["EMAIL_PASSWORD"]
            )
            server.send_message(msg)
    except Exception as e:
        print("")
        st.error("Failed to send the bug report. Please try again later.")
        st.exception(e)


# -------------------------
# Helpers & defaults
# -------------------------
# Backend API URL - use environment variable or Streamlit secrets
BACKEND_API = st.secrets.get("BACKEND_API_URL", "https://pressonit-dekai.hf.space") 
MAX_HISTORY_SHOWN = 50
DEKAI_EMAIL="prestonwachiramwas@gmail.com"
def init_state():
    if "page" not in st.session_state:
        st.session_state.page = "splash"
    if "messages" not in st.session_state:
        st.session_state.messages = []  # list of dicts: {id, role, text, ts}
    if "history" not in st.session_state:
        st.session_state.history = []   # saved conversations
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "user" not in st.session_state:
        st.session_state.user = {"name": None, "email": None}
    if "page" not in st.session_state:
        st.session_state.page = "Sign In"
    if "input_buffer" not in st.session_state:
        st.session_state.input_buffer = ""
    if "show_upload" not in st.session_state: 
        st.session_state.show_upload = False
    if "processing_message" not in st.session_state:
        st.session_state.processing_message = None  # Track if we're waiting for a reply

init_state()

# -------------------------
# UI: Sidebar 
# -------------------------
with st.sidebar:
    menu = st.selectbox("Menu", ["Chat", "History", "Sign in", "Sign up", "Report a bug", "About", "Logout"])
    # emulate drawer behavior by setting page
    if menu != "Chat":
        st.session_state.page = menu.lower().replace(" ", "_")
    else:
        st.session_state.page = "chat"


    st.markdown("<div style='height:500px;'></div>", unsafe_allow_html=True)  # pushes link down
    #st.markdown("<p style='text-align:center; font-size:14px;'><a href='https://github.com/Pressatit/DEKAI' style='color:#00b4d8;'>Help DEKAI Grow</a></p>",unsafe_allow_html=True)


# -------------------------
# Simple "splash" screen
# -------------------------
def render_splash():
    st.markdown("<div style='text-align:center;padding:60px 0'>", unsafe_allow_html=True)
    st.image("data:image/jpeg;base64,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", width=150)  # placeholder icon
    st.markdown("<h2>Welcome to DEKAI</h2>", unsafe_allow_html=True)
    st.markdown("<div class='small-muted'>Loading your personalized assistant...</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    

# -------------------------
# Chat components
# -------------------------
def add_message(role, text):
    st.session_state.messages.append({"id": str(uuid.uuid4()), "role": role, "text": text, "ts": datetime.now(timezone.utc)})

def call_backend_generate(prompt, temperature=0.7, top_p=0.9, beam_width=1):
    """Call your backend endpoint. Expects JSON response with `text`."""
    if not BACKEND_API:
        # fallback: echo-ish demo
        time.sleep(0.5)
        return f"(demo) I heard: {prompt}"
    try:
        payload = {"prompt": prompt}
        r = requests.post(
                f"{BACKEND_API}/conversation/{st.session_state.current_conversation_id}/generater",
                json=payload,
                headers={"Authorization": f"Bearer {st.session_state.user['access_token']}"}
)
        r.raise_for_status()
        data = r.json()
        # Accept both { "text": "..."} or string
        if isinstance(data, dict):
            return data.get("text") or data.get("reply") or str(data)
        return str(data)
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code == 401:
           return f"System :Sign in to access DEKAI."
        else:
          return f"Error contacting backend: {e}"


import requests

def call_image_backend(uploaded_image):
    import requests

    # 🔁 Rewind the file before reading
    uploaded_image.seek(0)
    image_bytes = uploaded_image.read()

    files = {
        "image": (
            uploaded_image.name,
            image_bytes,
            uploaded_image.type
        )
    }

    try:
        response = requests.post(f"{BACKEND_API}/vision/analyze", files=files)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Image backend failed: {e}")
        return {"error": str(e)}

def render_chat():

    st.markdown("<div class='header'><h3>DEKAI</h3><div class='kbd'>...</div></div>", unsafe_allow_html=True)
    # --- Require login first ---
    if not st.session_state.get("logged_in", False):
        render_splash()
        st.warning("You must sign in first to access DEKAI.")
        return
   
    # --- Callback to send message safely ---
    def send_message_callback(val:str):
        # 1️⃣ Add user message immediately and rerun to show it
        add_message("user", val)
        
        # Set processing flag with the message content
        st.session_state.processing_message = val
        st.rerun()  # Rerun immediately to show user message

    # --- Messages display area ---
    st.markdown("<div class='chat-area' id='chat-area'>", unsafe_allow_html=True)
    for m in st.session_state.messages[-MAX_HISTORY_SHOWN:]:
     if m["text"]:
        # 1. Clean the text of weird tokens like <s> or [/INST]
        clean_text = m["text"].replace("<s>", "").replace("</s>", "").replace("[/INST]", "").strip()
        
        if clean_text:
            css_class = "dekai-user" if m["role"] == "user" else "dekai-assistant"
            align_style = "right" if m["role"] == "user" else "left"
            
            # 2. Force the text color to be visible (Black for assistant, White for user)
            text_color = "#ffffff" if m["role"] == "user" else "#000000"
            
            st.markdown(
                f"<div style='text-align:{align_style};'>"
                f"<div class='{css_class}' style='color:{text_color}; white-space: pre-wrap;'>"
                f"{clean_text}</div></div>", 
                unsafe_allow_html=True
            )
    
    # Show thinking animation in the chat area if processing
    if st.session_state.get("processing_message"):
        css_class = "dekai-assistant"
        align_style = "left"
        text_color = "#000000"
        st.markdown(
            f"<div style='text-align:{align_style};'>"
            f"<div class='{css_class}' style='color:{text_color}; white-space: pre-wrap;'>"
            f"💭 *Thinking...*</div></div>", 
            unsafe_allow_html=True
        )
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # --- Input area (always visible, even during processing) ---
    with st.container():
      st.markdown("<div class='input-container'>", unsafe_allow_html=True)

      col1, col2 = st.columns([0.1, 0.9])

    # 📎 Upload toggle (OUTSIDE the form)
      with col1:
        if st.button("📎"): 
                st.session_state.show_upload = not st.session_state.show_upload

    # 📨 Message form (ONLY input + submit)
      with col2:
        with st.form(key="chat_form", clear_on_submit=True):
            user_input = st.text_area(
                "Message",
                height=80,
                placeholder="What's on your mind?",
                label_visibility="collapsed",
                # autocomplete="off"
            )

            submitted = st.form_submit_button("Send")

            if submitted and user_input.strip():
                send_message_callback(user_input.strip())

      st.markdown("</div>", unsafe_allow_html=True)
    
    # --- Process pending message if exists (after input area is rendered) ---
    if st.session_state.get("processing_message"):
        user_message = st.session_state.processing_message
        # Keep flag set during processing so thinking animation shows
        # We'll clear it after we get the reply
        
        # --- LOGIC SEPARATION ---#
        if st.session_state.get("current_conversation_id"):
            convo_id = st.session_state.current_conversation_id
        else:
            try:
                response = requests.post(
                    f"{BACKEND_API}/conversation",
                    headers={"Authorization": f"Bearer {st.session_state.user['access_token']}"}
                )
                response.raise_for_status()
                data = response.json()
                convo_id = data.get("conversation_id")
                st.session_state.current_conversation_id = convo_id
            except Exception as e:
                st.error(f"Failed to create conversation: {e}")
                # Don't return, just continue - input area is already rendered

        # Store user message in backend
        try:
            requests.post(
                f"{BACKEND_API}/conversation/{convo_id}/messages",
                json={"sender": "user", "content": user_message},
                headers={"Authorization": f"Bearer {st.session_state.user['access_token']}"}
            )
        except Exception as e:
            st.error(f"Failed to store user message: {e}")

        # Get reply from backend (thinking animation is shown in messages area)
        reply = call_backend_generate(user_message)

        # Add assistant reply (this will clear the thinking animation on next rerun)
        add_message("assistant", reply)

        # Store assistant message in backend
        try:
            requests.post(
                f"{BACKEND_API}conversation/{convo_id}/messages",
                json={"sender": "assistant", "content": reply},
                headers={"Authorization": f"Bearer {st.session_state.user['access_token']}"}
            )
        except Exception as e:
            st.error(f"Failed to store assistant message: {e}")

        st.session_state.history.append({
            "ts": datetime.now(timezone.utc),
            "user": user_message,
            "assistant": reply
        })
        # Clear processing flag now that we have the reply
        st.session_state.processing_message = None
        st.rerun()  # Rerun to show the assistant reply

    # --- Optional Sections ---
     if st.session_state.show_upload:
      with st.expander("📷 Upload Image for Recognition", expanded=True):
        # 📱 added accept_file_types and let Streamlit handle basic extensions natively
          uploaded_image = st.file_uploader(
             "Choose an image or take a photo...",
             type=["jpg", "jpeg", "png"],
             key="vision_uploader"
        )

        # Track state across blocks
        is_valid_image = False
        
        if uploaded_image is not None:
            try:
                # Attempt to open and verify the image structure dynamically
                image = Image.open(uploaded_image)
                image.verify()  # Deep structural check for corruption
                
                # Re-open after verify() because verify() closes the file pointer stream
                image = Image.open(uploaded_image)
                st.image(image, caption="Selected image", width=300)
                is_valid_image = True
                
            except UnidentifiedImageError:
                st.error("❌ The file extension might match, but the internal data is corrupted or not a valid image.")
            except Exception as e:
                # Catch-all for permission errors, empty files, truncation, etc.
                st.error(f"❌ Structural file error: {str(e)}")

        # 🔒 The button disables completely if no image is uploaded OR if an error was caught above
        submit_disabled = not is_valid_image

        if st.button("Analyze Image", disabled=submit_disabled):
            with st.spinner("Analyzing campus landmark..."):
                result = call_image_backend(uploaded_image)
                if result and "error" not in result:
                    st.success("Analysis complete!")
                    st.write(result)
                else:
                    error_msg = result.get("error", "Unknown backend processing error.")
                    st.error(f"❌ Analysis failed: {error_msg}")

# -------------------------
# History screen
# -------------------------
def render_history():
    # -------------------------
    # Ensure user is logged in
    # -------------------------
    st.title("History")
    if not st.session_state.get("logged_in", False):
        st.warning("You must sign in first to access DEKAI.")
        return

    user_token = st.session_state.user['access_token']
    if not user_token:
        st.error("No authentication token found. Please log in again.")
        return

    
    search_query = st.text_input("Search conversations...")

    # Fetch user conversations
    try:
        headers = {"Authorization": f"Bearer {user_token}"}
        r = requests.get(f"{BACKEND_API}/conversation/my", headers=headers, timeout=10)
        r.raise_for_status()
        conversations = r.json()  # expect list of dicts: {id, title, created_at}
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code == 401:
           st.warning("Sign In to view conversations")
        else:
          return f"Error contacting backend: {e}"

    # Filter by search query
    if search_query:
        conversations = [c for c in conversations if search_query.lower() in c['title'].lower()]

    if not conversations:
        st.info("No conversations found.")
        return

   
    # Two-column layout: left=conversation list, right=messages
    left_col, right_col = st.columns([1, 3])
    
    # Left column: display conversations
    with st.sidebar:
     with left_col:
        st.subheader("Conversations")
        # store selected conversation id in session_state
        selected_conv_id = st.session_state.get("selected_conv_id")

        for conv in conversations:
            conv_label = f"{conv['title']} ({datetime.fromisoformat(conv['started_at']).strftime('%b %d, %Y')})"
            if st.button(conv_label, key=f"conv_{conv['conversation_id']}"):
                st.session_state.selected_conv_id = conv['conversation_id']
    
    # Right column: display messages
    selected_conv_id = st.session_state.get("selected_conv_id")
    with right_col:
        if selected_conv_id:
            # fetch messages for the conversation
            try:
                r = requests.get(f"{BACKEND_API}/message/{selected_conv_id}/messages", headers=headers, timeout=10)
                r.raise_for_status()
                messages = r.json()  # expect list of dicts: {role, content, ts}
            except Exception as e:
                st.error(f"Error fetching messages: {e}")
                return

            if not messages:
                st.info("No messages in this conversation yet.")
                return

            # group messages by relative date
            now = datetime.now(timezone.utc)
            def rel_bucket(created_at):
            
               if isinstance(created_at, str):
                ts = datetime.fromisoformat(created_at)
               elif isinstance(created_at, datetime):
                ts = created_at
               else:
                return "Older"

               now = datetime.now(timezone.utc)

               if ts.date() == now.date():
                 return "Today"
               elif ts.date() >= (now - timedelta(days=7)).date():
                return "This week"
               elif ts.date() >= (now - timedelta(days=30)).date():
                return "This month"
               return "Older"
        
            buckets = {}
            for m in messages[-MAX_HISTORY_SHOWN:]:
                bucket = rel_bucket(
                   datetime.fromisoformat(m["created_at"])
                   if isinstance(m["created_at"], str)
                   else m["created_at"]
                   )
                buckets.setdefault(bucket, []).append(m)

            for bucket in ["Today", "This week", "This month", "Older"]:
                items = buckets.get(bucket, [])
                if not items:
                    continue
                st.subheader(bucket)
                for msg in items:
                    role_label = "You" if msg['sender'] == "user" else "DEKAI"
                    bubble_color = "#2f5dd9" if msg['sender']=="user" else "#eef2f3"
                    text_color = "white" if msg['sender']=="user" else "#0f172a"
                    st.markdown(
                        f"<div style='background:{bubble_color}; color:{text_color}; padding:10px; border-radius:12px; margin-bottom:4px; max-width:80%;'>{role_label}: {msg['content']}</div>",
                        unsafe_allow_html=True
                    )
            else:
             st.info("Select a conversation on the left to see messages.")
    
# -------------------------
# Auth forms
# -------------------------
def render_signin():
    st.title("Sign in")
    email = st.text_input("Enter email", key="signin_email")
    pwd = st.text_input("Password", type="password", key="signin_pwd")
    
    if st.markdown("<p style='color:#1e88e5;cursor:pointer;' onclick='window.parent.postMessage({type:\"signup\"}, \"*\")'>Don't have an account? <b>Sign Up</b></p>", unsafe_allow_html=True):
       pass   
    if st.button("Sign in"):
        if not email or not pwd:
            st.error("All fields are required!")
            return
        else:
            
         payload = {
            "username": email,  # OAuth2 expects 'username'
            "password": pwd
         }
         r = requests.post(f"{BACKEND_API}/auth/login", data=payload)  # 'data' sends form-data
         if r.status_code == 200:
            data = r.json()
            st.session_state.logged_in = True
            st.session_state.user = {
                "name": email.split("@")[0],
                "email": email,
                "access_token": data["access_token"] 
}
            st.success("Logged in successfully!")
            st.session_state.page = "chat"
         else:
            st.error(r.json().get("detail", "Invalid credentials"))
    st.markdown("<p style='text-align:right; font-size:13px;'><a href='#' style='color:#00b4d8;'>Forgotten password?</a></p>",unsafe_allow_html=True)
    st.write("— or —")
    if st.button("Continue with Google"):
        backend_url = st.secrets.get("BACKEND_API_URL", "https://pressonit-dekai.hf.space")
        st.markdown(
        f"""
        <meta http-equiv="refresh" content="0; url={backend_url}/auth/google/login">
        """,
        unsafe_allow_html=True
    )
def render_signup():
    st.title("Sign up")
    email = st.text_input("Enter email", key="signup_email")
    name = st.text_input("Enter name", key="signup_name")
    pwd = st.text_input("Password", type="password", key="signup_pwd")
    st.markdown("Already have an account?",unsafe_allow_html=True)

    if st.button("Sign up"):
        if not email or not name or not pwd:
            st.error("All fields are required!")
            return
        
        # Call FastAPI backend
        try:
            response = requests.post(
                f"{BACKEND_API}/auth/signup",
                json={"email": email, "name": name, "password": pwd},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                st.success(f"Account created for {data['name']} • Please log in!")
                st.session_state.user = {"name": data['name'], "email": data['email']}
                st.session_state.page = "chat"
            else:
                st.error(response.json().get("detail", "Signup failed"))
        except Exception as e:
            st.error(f"Error connecting to backend: {e}")

    st.write("— or —")
    if st.button("Continue with Google (Sign up)"):
        backend_url = st.secrets.get("BACKEND_API_URL", "https://pressonit-dekai.hf.space")
        st.markdown(
        f"""
        <meta http-equiv="refresh" content="0; url={backend_url}/auth/google/login">
        """,
        unsafe_allow_html=True
    )
        
def render_logout():
    st.title("Log out")
    if not st.session_state.get("logged_in", False):
        st.warning("You must sign in first to access DEKAI.")
        return
    
    
    if st.button("Log out"):
        st.success(f"Logged out successfully")
        st.session_state.clear()
        
def render_about():
    st.title("About DEKAI")
    st.markdown("<b>DEKAI </b> is an intelligent campus assistant designed to help users easily access information about Dedan Kimathi University of Technology.<br> It allows students, staff, and visitors to ask questions about campus-related services, locations, and general university information in natural language and receive clear, relevant responses.<br> DEKAI also features <b>image recognition </b> capabilities that enable users to identify and learn about campus landmarks by simply taking or uploading a photo.<br> Built with usability and reliability in mind, DEKAI aims to simplify navigation, reduce information barriers, and improve the overall campus experience.",unsafe_allow_html=True)
        
def render_report_a_bug():
    st.title("Report a Bug")

    st.write(
        "Found something not working as expected? Let us know and we’ll take a look."
    )

    if "bug_sent" not in st.session_state:
        st.session_state.bug_sent = False

    if not st.session_state.bug_sent:
        with st.form("bug_report_form"):
            st.text_input("To", value=DEKAI_EMAIL, disabled=True)
            subject = st.text_input("Subject", placeholder="Briefly describe the issue")
            message = st.text_area(
                "Message",
                placeholder="Explain what happened, what you expected, and any steps to reproduce the bug.",
                height=200,
            )

            submitted = st.form_submit_button("📨 Send Report")

        if submitted:
            if not subject or not message:
                st.warning("Please fill in both the subject and message.")
            else:
                send_bug_email(subject, message)
                st.session_state.bug_sent = True
                st.rerun()

    else:
        st.success(
            "✅ Thank you for reporting the issue! Our team will review the bug and work on a fix as soon as possible."
        )
# -------------------------
# Router
# -------------------------
page = st.session_state.get("page", "splash")

if page == "splash":
    render_splash()

elif page == "chat":
    render_chat()

elif page == "history":
    render_history()

elif page == "sign_in":
    render_signin()

elif page == "sign_up":
    render_signup()

elif page == "about":
    render_about()

elif page == "logout":
    render_logout()

elif page =="report_a_bug":
    render_report_a_bug()


else:
    st.title(page.replace("_", " ").title())
    st.write("Placeholder for:", page)


# -------------------------
# Footer / quick actions
# -------------------------
st.markdown("---")
c1, c2, c3 = st.columns([1,6,1])
with c2:
    st.markdown("<div style='text-align:center;' class='small-muted'> • DEKAI may Hallucinate. Make sure to factcheck • </div>", unsafe_allow_html=True)

