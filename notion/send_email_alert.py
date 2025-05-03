import os
import json
import smtplib
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))
EMAIL = os.getenv("ALERT_EMAIL_ADDRESS")
PASSWORD = os.getenv("ALERT_EMAIL_PASSWORD")
TO_EMAIL = os.getenv("ALERT_TO_EMAIL")

# Path to your triage log
LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "page_triage_log.json")

# Load last triage entry
def get_latest_high_risk():
    try:
        with open(LOG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            for entry in data:
                if entry["risk"] == "HIGH":
                    return entry
    except Exception as e:
        print("❌ Error reading triage log:", e)
    return None

# Send alert email
def send_email(subject, body):
    msg = MIMEMultipart()
    msg["From"] = EMAIL
    msg["To"] = TO_EMAIL
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL, PASSWORD)
        server.sendmail(EMAIL, TO_EMAIL, msg.as_string())
        server.quit()
        print("✅ Email sent successfully.")
    except Exception as e:
        print("❌ Failed to send email:", e)

# Main execution
if __name__ == "__main__":
    print("📬 Checking for high-risk entries...")
    entry = get_latest_high_risk()
    if entry:
        email_subject = "🚨 High-Risk Journal Alert"
        email_body = (
            f"📅 Time: {entry['timestamp']}\n"
            f"🔍 Severity: {entry['risk']}\n"
            f"🧠 Emotion: {entry['emotion']}\n"
            f"📝 Summary: {entry['summary']}\n\n"
            f"Excerpt:\n{entry['snippet']}"
        )
        send_email(email_subject, email_body)
    else:
        print("📭 No HIGH risk entries found.")
