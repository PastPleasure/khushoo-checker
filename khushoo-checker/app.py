import streamlit as st
import openai
from openai import OpenAI
import os
import requests
import pyrebase
from datetime import datetime, timedelta


firebase_config = st.secrets("firebase")
firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
db = firebase.database()

if "user" not in st.session_state:
    st.title("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        try:
            user = auth.sign_in_with_email_and_password(email, password)
            st.session_state.user = user
            st.session_state["user_email"] = email
            st.success(f"Logged in as {email}")
            st.rerun()
        except Exception as e:
            st.error(f"Login failed: {e}")
    st.stop()
else:
    st.info(f"Logged in as {st.session_state.user['user_email']}")

def get_prayer_times(city, country):
    try:
        url = f"https://api.aladhan.com/v1/timingsByCity?city={city}&country={country}&method=2"
        response = requests.get(url)
        data = response.json()
        return data["data"]["timings"]
    except Exception as e:
        st.error(f"Error fetching prayer times: {e}")
        return {}

def get_reminder_times(timings):
    reminder_times = {}
    for prayer, time_str in timings.items():
        time_str = time_str[:5]  # Only "HH:MM"
        try:
            prayer_time = datetime.strptime(time_str, "%H:%M")
        except ValueError:
            prayer_time = datetime.strptime(time_str, "%H:%M:%S")
        reminder_time = prayer_time - timedelta(minutes=5)
        reminder_times[prayer] = reminder_time.strftime("%H:%M")
    return reminder_times


        

if "user_email" in st.session_state:
    st.title("Prayer Times")
    user_email = st.session_state["user_email"]
    user_id = user_email.replace(".", "-")
    user_profile = db.child("users").child(user_id).get().val()
    if user_profile is None or "city" not in user_profile or "country" not in user_profile:
        st.info("Please enter your location details. This is required for reminders.")
        city = st.text_input("Enter your city")
        country = st.text_input("Enter your country")
        if st.button("Save Location"):
            if not city or not country:
                st.error("Please enter both city and country.")
            else:
                db.child("users").child(user_id).set({"city": city, "country": country, "email": user_email})
                st.success("Location saved successfully.")
                st.rerun()
        st.stop()
    else:
        city = user_profile["city"]
        country = user_profile["country"]
        st.success(f"Your saved location: {city}, {country}")

        timings = get_prayer_times(city, country)
        st.write("Todays prayer times:")
        for prayer, time in timings.items():
            st.write(f"{prayer}: {time}")



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

