import streamlit as st
import openai
from openai import OpenAI
import subprocess
import os
from dotenv import load_dotenv
import requests

query_params = st.experimental_get_query_params()

# Handle login token if it's present
if "token" in query_params:
    id_token = query_params["token"][0]
    verify_url = "https://identitytoolkit.googleapis.com/v1/accounts:lookup?key=AIzaSyDH6wELsX1BH3ndY2HOMSH6wKrECgNoKe0"
    res = requests.post(verify_url, json={"idToken": id_token})
    if res.status_code == 200:
        user_info = res.json()["users"][0]
        st.session_state.user = {
            "email": user_info["email"],
            "name": user_info.get("displayName", "Anonymous"),
            "uid": user_info["localId"]
        }
    else:
        st.warning("⚠️ Failed to verify login.")

# ✅ Show login button if no user session exists (important!)
if "user" not in st.session_state:
    st.markdown("## 🔐 Please log in to use Khushoo Coach")
    st.link_button("Login with Google", "https://khushoo-checker.netlify.app")
    st.stop()

# Optional: Welcome message after login
st.success(f"👋 Welcome, {st.session_state.user['name']}!")

openai.api_key = os.getenv("OPENAI_API_KEY") # Adjust the path to your .env file
client = OpenAI()

def generate_advice(answers):
    prompt = f"""
You are an Islamic sunni advisor who understands Qur'an, Hadith, Scholars and psychology. A Muslim is preparing for salah. They answered a khushoo checklist with the following responses:

- Feeling rushed: {answers.get('rushed')}
- Bathroom needs: {answers.get('bathroom')}
- Mental distractions: {answers.get('distractions')}
- Time available with full focus: {answers.get('focus_time')} minutes

Based on this, give them strong advice relating to their answers with 1–2 authentic hadiths, and finish with a spiritual motivation (e.g. imagine this is their last prayer, meeting Allah, reward of khushoo, etc). Be compassionate but firm. Keep it under 300 words.
"""
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "You are a wise, spiritual khushoo coach rooted in Islam."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

st.title("🕌 Khushoo Coach")
st.write("🕋 It's almost time for prayer. Let's prepare your heart.")

# Step state manager
if "step" not in st.session_state:
    st.session_state.step = 0
    st.session_state.answers = {}

# Start button
if st.session_state.step == 0:
    if st.button("🧭 Start Khushoo Check"):
        st.session_state.step = 1
        st.rerun()

# Step 1: Are you rushed?
elif st.session_state.step == 1:
    user_input = st.text_input("1️⃣ Are you feeling rushed? Why or why not?")
    if user_input:
        st.session_state.answers["rushed"] = user_input
        st.session_state.step = 2
        st.rerun()


# Step 2: Bathroom
elif st.session_state.step == 2:
    user_input = st.text_input("2️⃣ Do you need to use the bathroom? Be honest.")
    if user_input:
        st.session_state.answers["bathroom"] = user_input
        st.session_state.step = 3
        st.rerun()


# Step 3: Mental distractions
elif st.session_state.step == 3:
    user_input = st.text_input("3️⃣ What thoughts are distracting you right now?")
    if user_input:
        st.session_state.answers["distractions"] = user_input
        st.session_state.step = 4
        st.rerun()


# Step 4: Time availability
elif st.session_state.step == 4:
    user_input = st.text_input("4️⃣ How many minutes can you pray with full focus?")
    if user_input:
        st.session_state.answers["focus_time"] = user_input
        st.session_state.step = 5
        st.rerun()


# Final step: Ready for AI
elif st.session_state.step == 5:
    st.success("✅ All answers received.")
    st.write("Click below to get personalized advice.")
    if st.button("🧠 Get Islamic Advice"):
        st.session_state.step = 6
        st.rerun()


# Step 6: AI response will go here (we do this next)
elif st.session_state.step == 6:
    st.write("🧠 Generating your khushoo advice...")
    advice = generate_advice(st.session_state.answers)
    st.markdown("### 🌙 Your Personalized Advice:")
    st.markdown(advice)
    st.success("🕋 May Allah accept your salah. Stand before Him with presence.")

