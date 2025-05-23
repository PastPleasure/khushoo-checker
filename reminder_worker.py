import firebase_admin
from firebase_admin import credentials, db
import os
from dotenv import load_dotenv
import requests
from datetime import datetime, timedelta
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import time
#load_dotenv(dotenv_path="")

def send_email(to_email, subject, message):
    try:
        sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
        from_email = os.getenv("FROM_EMAIL")

        email = Mail(
            from_email=from_email,
            to_emails=to_email,
            subject=subject,
            plain_text_content=message,
        )
        response = sg.send(email)
        print(f"[EMAIL SENT] to {to_email} | Status Code: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Could not send email to {to_email}: {e}")

        


def get_prayer_times(city, country):
    try:
        url = f"https://api.aladhan.com/v1/timingsByCity?city={city}&country={country}&method=2"
        response = requests.get(url)
        data = response.json()
        return data["data"]["timings"]
    except Exception as e:
        print(f"[ERROR] Could not fetch prayer times for {city}, {country}: {e}")
        return {}
    
def get_reminder_times(timings):
    reminder_times = {}
    for prayer, time_str in timings.items():
        time_str = time_str[:5]  # Ensure it's "HH:MM"
        try:
            prayer_time = datetime.strptime(time_str, "%H:%M")
        except ValueError:
            continue  # skip invalid time format
        reminder_time = prayer_time - timedelta(minutes=5)
        reminder_times[prayer] = reminder_time.strftime("%H:%M")
    return reminder_times


if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_admin_key.json")
    firebase_admin.initialize_app(cred, {
        "databaseURL": os.getenv("FIREBASE_DB_URL")

    })
def get_all_users():
    users_ref = db.reference("users")
    users = users_ref.get()
    return users

if __name__ == "__main__":
    print("🚀 Reminder Worker Started...")

    while True:
        users = get_all_users()
        now = datetime.now().strftime("%H:%M")

        if users:
            for uid, info in users.items():
                email = info.get("email")
                city = info.get("city")
                country = info.get("country")

                if not city or not country or not email:
                    continue  # skip incomplete user

                prayer_times = get_prayer_times(city, country)
                reminder_times = get_reminder_times(prayer_times)

                for prayer, reminder_time in reminder_times.items():
                    if now == reminder_time:
                        send_email(
                            email,
                            subject=f"🕌 Time to Prepare for {prayer}",
                            message=f"As-salaamu 'alaykum!\n\nIt's almost time for {prayer} prayer. Take a moment to do your Khushoo checklist before standing before Allah.\n\nVisit your Khushoo Coach to prepare now.\n\n🕋 https://your-app-url.com"
                        )

        time.sleep(60)  # Wait one minute before checking again

