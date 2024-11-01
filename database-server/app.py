from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

app = Flask(__name__)

cred = credentials.Certificate("yourServiceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

class Database:
    def init_user(self, chat_id, phone: str):
        doc_ref = db.collection("testing").document(chat_id)
        if not doc_ref.get().exists:
            data = {
                "id": chat_id,
                "phone": phone,
                "messages": [],
            }
            db.collection("testing").document(chat_id).set(data)
        return doc_ref

    def payload(self, text, time):
        return {
            "message": str(text),
            "timestamp": time
        }

    def add_convo(self, ref, msg):
        ref.update({"messages": firestore.ArrayUnion([msg])})

database = Database()


@app.route('/store_message', methods=['POST'])
def store_message():
    data = request.json 
    phone_number = data.get('phone_number')
    user_query = data.get('user_query')
    rag_response = data.get('rag_response')
    chat_id = phone_number 
    ref = database.init_user(chat_id, phone_number)  
    timestamp = datetime.utcnow().isoformat()
    user_msg_payload = database.payload(user_query, timestamp)
    rag_msg_payload = database.payload( rag_response, timestamp)
    database.add_convo(ref, user_msg_payload)
    database.add_convo(ref, rag_msg_payload)
    response_message = "Saved to DB successfully"
    return jsonify({"response": response_message}), 200

if __name__ == '__main__':
    app.run(port=5005)
