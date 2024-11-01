import schedule
import time
import requests
from datetime import datetime
import streamlit as st
from dotenv import load_dotenv
import os
import threading

load_dotenv()

WHATSAPP_API_TOKEN = os.getenv("WHATSAPP_API_TOKEN")

if 'scheduled_messages' not in st.session_state:
    st.session_state.scheduled_messages = set()

if 'scheduler_thread_started' not in st.session_state:
    st.session_state.scheduler_thread_started = False


def send_whatsapp_message(phone, message_type, content):
    url = f"https://graph.facebook.com/v20.0/377542662119561/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_API_TOKEN}",
        "Content-Type": "application/json"
    }

    if message_type == "Text":
        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "text",
            "text": {
                "body": content["text"]
            }
        }
    elif message_type == "Text + Link":
       payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "text",
            "text": {
                "preview_url": True,
                "body": f'{content["text"]} \n{content["link"]}'
            }
        }
    elif message_type == "Image":
        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "image",
            "image": {
                "link": content["image_url"]
            }
        }
    elif message_type == "Voice":
        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "audio",
            "audio": {
                "link": content["audio_url"]
            }
        }
    elif message_type == "Template":
        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "template",
            "template": {
                "name": content["template_name"],
                "language": {
                    "code": content["language_code"]
                }
            }
        }

    response = requests.post(url, json=payload, headers=headers)
    print(f"Message sent to {phone} at {datetime.now()} - Response: {response.json()}")


def schedule_messages(users):
    for user in users:
        message_id = f"{user['phone']}-{user['message_type']}-{user['time']}"  
        
        if message_id not in st.session_state.scheduled_messages:
            st.session_state.scheduled_messages.add(message_id) 
            schedule.every().day.at(user["time"]).do(send_whatsapp_message, user["phone"], user["message_type"], user["content"])

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)


st.title("WhatsApp Campaign Scheduler")

num_borrowers = st.number_input("Number of Borrowers", min_value=1, max_value=5, value=1)

borrowers = []
for i in range(num_borrowers):
    phone = st.text_input(f"Phone number for Borrower {i+1}", "")
    message_type = st.selectbox(f"Message Type for Borrower {i+1}", ["Text", "Text + Link", "Image", "Voice", "Template"])

    if message_type == "Text":
        text = st.text_area(f"Enter Text for Borrower {i+1}")
        content = {"text": text}
    elif message_type == "Text + Link":
        text = st.text_area(f"Enter Text for Borrower {i+1}")
        link = st.text_input(f"Enter Link for Borrower {i+1}")
        content = {"text": text, "link": link}
    elif message_type == "Image":
        image_url = st.text_input(f"Enter Image URL for Borrower {i+1}")
        content = {"image_url": image_url}
    elif message_type == "Voice":
        audio_url = st.text_input(f"Enter Voice (Audio) URL for Borrower {i+1}")
        content = {"audio_url": audio_url}
    elif message_type == "Template":
        template_name = st.text_input(f"Enter Template Name for Borrower {i+1}")
        language_code = st.text_input(f"Enter Language Code for Borrower {i+1} (e.g., en_US, en_GB)")
        content = {"template_name": template_name, "language_code": language_code}

    

    time_to_send = st.text_input(f"Schedule Time for Borrower {i+1} (24hr format, e.g., 17:00)", "")
    borrowers.append({"phone": phone, "message_type": message_type, "content": content, "time": time_to_send})

if st.button("Schedule Campaign"):
    if all(b["phone"] and b["message_type"] and b["content"] and b["time"] for b in borrowers):
        st.success("Campaign scheduled")
        schedule_messages(borrowers)
        
        if not st.session_state.scheduler_thread_started:
            scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
            scheduler_thread.start()
            st.session_state.scheduler_thread_started = True
    else:
        st.error("Please fill in all fields for each borrower.")
