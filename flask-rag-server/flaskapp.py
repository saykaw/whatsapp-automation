from flask import Flask, request, jsonify
from langchain_mistralai import ChatMistralAI
from langchain_community.utilities import SQLDatabase
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain.chains import create_sql_query_chain
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.embeddings.sentence_transformer import SentenceTransformerEmbeddings
import os 
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

app = Flask(__name__)

llm = ChatMistralAI(
    model="mistral-large-latest",
    temperature=0,
    max_retries=2,
    api_key=os.getenv("MISTRAL_API_KEY")

)

db_uri = "your_database_uri"
db = SQLDatabase.from_uri(db_uri)
execute_query = QuerySQLDataBaseTool(db=db)
generate_query = create_sql_query_chain(llm, db)
chain = generate_query | execute_query

embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
embedding_db = Chroma(persist_directory="./chroma_db", embedding_function=embedding_function)

# Function to fetch user data dynamically
# def get_user_data(user_name):
#     """Fetch user data from the database based on the provided name."""
#     query = generate_query.invoke({"question": f"Select all data for the user where the name is '{user_name}'"})
#     context = execute_query.run(query)
#     return context

def get_user_data(phone_number):
    """Fetch user data from the database based on the provided name."""
    print("Generating Query")
    query = generate_query.invoke({"question": f"Select all data for the user where the phone_number is '{phone_number}' "})
    print("Query Generated")
    context = execute_query.run(query)
    print("Executing query")
    return context


def get_response(user_query, context, doc_context):
    llm_query_res_template = """
        Answer the question based on the context below. If the question cannot be answered using the information provided, reply with "I don't know". Also, make sure to answer the following questions considering the history of the conversation:
        You are an intelligent virtual financial assistant for Predixion AI, directly engaging with customers about their loan repayments. Your role is to help manage their loan, facilitate payments, and answer financial questions in a clear, professional way. Communicate in a friendly, authoritative manner, addressing the customer directly ("you") with concise responses suitable for WhatsApp.
        Make sure you communicate with the user in such a way that your response should always lead to payment collection.
        Based on the user question, you should respond in a short way. Do not write much; it should be short and precise.

        Instructions:
        1. Use precise financial language and ensure clear, accurate information.
        2. Facilitate payments: If the user is willing to pay the loan then please provide this link '''https://paymentUSER1UDN.com'''. Do not send the link until user requests or user wants to pay the loan.
        3. Offer solutions: If the customer is struggling, provide options like grace periods, payment restructuring, or deadline extensions.
        4. Keep responses short and to the point.
        5. Ensure confidentiality and remind the customer to keep their payment details secure.
        6. You can only extend the loan dates by 10 days if user requests for grace periods or deadline extensions.

        Context: {context}
        Question: {user_query}
        Doc context: {doc_context}
        Answer:
    """

    prompt_query_res_template = ChatPromptTemplate.from_template(llm_query_res_template)
    llm_chain = prompt_query_res_template | llm | StrOutputParser()
    print("Generating LLM Response")

    response = llm_chain.stream({
        "user_query": user_query,
        "context": context,
        "doc_context": doc_context,
    })

    response = ''.join([chunk for chunk in llm_chain.stream({
        "user_query": user_query,
        "context": context,
        "doc_context": doc_context,
    })])


    return response

session_data = {
    "chat_history": [],
    "user_name": None,
    "context": None,
    "doc_context": None
}


# @app.route("/query", methods=["POST"])
# def process_query():
#     data = request.json
#     user_query = data.get("user_query")
    
#     # if session_data["user_name"] is None:
#     #     session_data["user_name"] = user_query
#     #     session_data["context"] = get_user_data(session_data["user_name"])
#     #     response_message = f"Thank you, {session_data['user_name']}. How can I assist you today?"
#     #     session_data["chat_history"].append(AIMessage(content=response_message))
#     #     return jsonify({"response": response_message})

#     session_data["chat_history"].append(HumanMessage(content=user_query))
#     session_data["doc_context"] = embedding_db.similarity_search(user_query)

#     response = get_response(
#         user_query=user_query,
#         chathistory=session_data["chat_history"],
#         context=session_data["context"],
#         doc_context=session_data["doc_context"]
#     )
#     session_data["chat_history"].append(AIMessage(content=response))

#     return jsonify({"response": response})


# @app.route('/query', methods=['POST'])
# def query():
#     data = request.get_json()
#     phone_number = data.get('phone_number')
#     user_query = data.get('user_query')
#     if phone_number not in session_data:
#         session_data[phone_number] = {
#             "chat_history": [],
#             "context": get_user_data(phone_number)
#         }
#     session_data[phone_number]["chat_history"].append(HumanMessage(content=user_query))
#     context = session_data[phone_number]["context"]
#     doc_context = embedding_db.similarity_search(user_query)
#     response = get_response(user_query, session_data[phone_number]["chat_history"], context, doc_context)
#     session_data[phone_number]["chat_history"].append(AIMessage(content=response))
#     return jsonify({"response": response})


@app.route('/')
def home():
    return "Hello World"


@app.route('/query', methods=['POST'])
def query():
    data = request.get_json()
    phone_number = data.get('phone_number')
    user_query = data.get('user_query')
    context = get_user_data(phone_number)
    print("Got Context")
    doc_context = embedding_db.similarity_search(user_query)
    response = get_response(user_query, context, doc_context)
    return jsonify({"response": response})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
