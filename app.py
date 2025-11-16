from flask import Flask, request, jsonify
from flask_cors import CORS
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification, AutoModelForTokenClassification
import os
import google.generativeai as genai
import sqlite3 
import uuid 

# --- 1. CONFIGURE YOUR API KEY ---
# PASTE YOUR KEY HERE!
try:
    genai.configure(api_key="")
    llm_model = genai.GenerativeModel('gemini-2.5-flash')
    print("Gemini LLM configured successfully with 'gemini-2.5-flash'.")
except Exception as e:
    print(f"Error configuring Gemini: {e}")
    print("WARNING: LLM fallback will not work. Check your API key.")
    llm_model = None

# --- 2. SETUP FLASK APP ---
app = Flask(__name__)
CORS(app)
DATABASE_FILE = 'bot_database.db'

# --- 3. DATABASE HELPER FUNCTION ---
def get_db_conn():
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row 
    return conn

# --- 4. LOAD LOCAL MODELS ONCE ---
print("Loading Local Intent Classifier (banking-bot-model-v1)...")
intent_model_path = os.path.abspath("./banking-bot-model-v1")
intent_tokenizer = AutoTokenizer.from_pretrained(intent_model_path)
intent_model = AutoModelForSequenceClassification.from_pretrained(intent_model_path)
intent_classifier = pipeline("text-classification", model=intent_model, tokenizer=intent_tokenizer)

print("Loading Local Entity Recognizer (ner-bot-model-v1)...")
ner_model_path = os.path.abspath("./ner-bot-model-v1")
ner_tokenizer = AutoTokenizer.from_pretrained(ner_model_path)
ner_model = AutoModelForTokenClassification.from_pretrained(ner_model_path)
ner_pipeline = pipeline("token-classification", model=ner_model, tokenizer=ner_tokenizer, aggregation_strategy="simple")

print("All models loaded! API is ready.")

# --- 5. DEFINE THE BOT'S RESPONSES (FOR LOCAL MODEL) ---
# We will pass this whole dictionary to the LLM
bot_responses = {
    "check_balance_guide": "To check your balance securely, you can use our NetBanking app, check your e-passbook, or use any UPI app in the 'Check Balance' section.",
    "check_transactions_guide": "You can see all your recent transactions by checking the 'Mini Statement' or 'e-Passbook' section in your NetBanking or mobile banking app.",
    "find_account_details": "You can find your account number and customer ID printed on the front page of your bank passbook. You can also find it in your NetBanking app profile section.",
    "manage_credentials": "You can change your ATM PIN by visiting any of our nearest ATMs...",
    "block_card_guide": "I can help with that. To confirm, are you blocking the card due to it being lost, stolen, or another reason?",
    "update_kyc": "I can help with that. Are you looking to do a Mini-KYC (online with Aadhar) or a Full KYC?",
    "transfer_funds_guide": "How would you like to transfer the money? By using a Phone Number (UPI), or by using an Account Number (NEFT/IMPS)?",
    "get_transaction_limits": "Our standard daily transaction limits are:\n  - UPI: ₹1,00,000\n  - IMPS: ₹5,00,000...",
    "set_transaction_limits": "To set your personal transaction limits for security, please log in to the NetBanking app...",
    "open_account": "What type of account are you interested in? We offer Savings, Current, and Demat accounts.",
    "get_interest_rates": "I can help with that. Here are our current rates...", # Placeholder, will be replaced by DB query
    "find_ifsc_code": "I can help with that. Which branch's IFSC code do you need?", # Placeholder
    "get_bank_hours": "Our bank branches are open from 10:00 AM to 4:00 PM, Monday to Friday. We are closed on all Saturdays, Sundays, and public holidays.",
    "check_loan_status_guide": "You can check your loan application status by visiting our website...",
    "pay_bill_guide": "You can pay all your bills (electricity, phone, etc.) using the 'Bill Pay' section in our NetBanking app.",
    "general_faq": "Our headquarters is located in Mumbai, India. For more information, please visit the 'About Us' section of our website.",
    "greet": "Hello! How can I help you with your banking questions today?",
    "summarize_conversation": "One moment, please. I will summarize our bank-related conversation for you.",
    "fallback": "I'm sorry, I don't quite understand. Can you rephrase? I can help with account guides, transactions, and bank info."
}

# --- 6. DEFINE NEW, FASTER LLM HELPER FUNCTION ---
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

# Create the list of known local intents for the prompt
known_intents_list = "\n".join([f"- {key}: {value}" for key, value in bot_responses.items() if key != "fallback"])

def get_llm_response(user_text, chat_history_string):
    """
    Gets a response from the Gemini LLM in a single, smart call.
    """
    if not llm_model:
        print("LLM model not loaded. Using fallback.")
        return bot_responses["fallback"]

    prompt = f"""
    You are a "Super Bot", a helpful and polite bank assistant.
    Your job is to triage the user's LATEST message. You have two brains:
    1. A "Local Brain" with pre-written answers for known intents.
    2. A "Cloud Brain" (you) for everything else.

    HERE ARE THE KNOWN LOCAL INTENTS AND THEIR EXACT ANSWERS:
    {known_intents_list}
    ---
    
    HERE IS THE CONVERSATION HISTORY (for context):
    {chat_history_string}
    ---
    
    HERE IS THE USER'S LATEST MESSAGE:
    "{user_text}"
    ---
    
    YOUR TASK:
    1. Analyze the USER'S LATEST MESSAGE: "{user_text}".
    2. **First, check for spelling mistakes.** Is it a typo for a known local intent?
       - Example: If the user says "what is my balanec?", that is a typo for "check_balance_guide".
       - If it IS a typo for a known intent, respond with the **EXACT pre-written answer** from the list above.
    
    3. **If it's NOT a typo,** check if it's "General-Chitchat" (like "hello", "good morning", "what's the weather?").
       - If it IS chitchat, just be friendly and polite (e.g., "Hello! How can I help you today?").
    
    4. **If it's NOT chitchat,** it must be a "New Banking-Related Question" (like "i need a credit card" or "how to apply for a car loan").
       - If it IS a new banking question, give a helpful, general answer.
       - **Strictly** DO NOT ask for personal information (account number, name, etc.).
       - Example response for "i need a credit card": "We offer a variety of credit cards, including travel rewards and cashback options. You can see all our cards and apply on our official bank website under the 'Cards' section."
    
    Provide ONLY the final response to the user.
    """
    
    try:
        response = llm_model.generate_content(prompt, safety_settings=safety_settings)
        return response.text.strip()
    except Exception as e:
        print(f"LLM Error: {e}")
        return bot_responses["fallback"]


# --- 7. CREATE THE API ENDPOINT (v4 - The "Fast Bot") ---
@app.route("/chat", methods=["POST"])
def chat():
    db = get_db_conn() 
    
    try:
        data = request.json
        user_text = data["message"]
        session_id = data["session_id"]

        # --- Session Management ---
        if session_id == "new":
            session_id = str(uuid.uuid4()) 
            db.execute("INSERT INTO sessions (session_id, current_state) VALUES (?, NULL)", (session_id,))
            print(f"New session created: {session_id}")
        
        # Save user message to history
        db.execute("INSERT INTO history (session_id, sender, message) VALUES (?, 'user', ?)", (session_id, user_text))

        # --- Get "Memory" (current_state) from DB ---
        state_row = db.execute("SELECT current_state FROM sessions WHERE session_id = ?", (session_id,)).fetchone()
        state = state_row['current_state'] if state_row else None

        response = ""

        # --- Check "Memory" (State Management) FIRST ---
        if state == "awaiting_account_type":
            # (Logic is the same, but now we update the DB)
            if "savings" in user_text.lower():
                response = "To open a Savings account, you will need your PAN and Aadhar card..."
            elif "current" in user_text.lower():
                response = "To open a Current account, you will need your business registration documents..."
            elif "demat" in user_text.lower():
                response = "To open a Demat account, you will need your PAN, Aadhar, and a blank cheque..."
            else:
                response = "I'm sorry, I didn't recognize that account type. We offer Savings, Current, and Demat accounts."
            db.execute("UPDATE sessions SET current_state = NULL WHERE session_id = ?", (session_id,)) 

        elif state == "awaiting_branch_name":
            entities = ner_pipeline(user_text)
            branch_name = user_text # Default
            for entity in entities:
                if entity['entity_group'] == 'BRANCH':
                    branch_name = entity['word']; break
            
            ifsc_row = db.execute("SELECT ifsc_code FROM ifsc_codes WHERE branch_name = ?", (branch_name.lower(),)).fetchone()
            if ifsc_row:
                response = f"The IFSC code for the {branch_name} branch is: {ifsc_row['ifsc_code']}"
            else:
                response = f"I don't have the code for {branch_name}, but you can find all codes on our website."
            db.execute("UPDATE sessions SET current_state = NULL WHERE session_id = ?", (session_id,)) 

        else:
            # --- No "Memory" set -> Run NLU and TRIAGE ---
            intent_result = intent_classifier(user_text)
            top_intent = intent_result[0]['label']
            intent_score = intent_result[0]['score']

            # --- THE NEW "FAST BOT" TRIAGE ---
            if intent_score > 0.7:  # <-- CONFIDENCE THRESHOLD
                # HIGH CONFIDENCE: It's a known bank task. Use local brain.
                print(f"Local Intent: {top_intent} (Score: {intent_score:.2f})")
                
                if top_intent == "get_interest_rates":
                    rates_rows = db.execute("SELECT product_name, rate FROM interest_rates").fetchall()
                    response = "Our current interest rates are:\n"
                    for row in rates_rows:
                        response += f"  - {row['product_name']}: {row['rate']}\n"

                elif top_intent == "find_ifsc_code":
                    entities = ner_pipeline(user_text)
                    branch_name = None
                    for entity in entities:
                        if entity['entity_group'] == 'BRANCH':
                            branch_name = entity['word']; break
                    if branch_name:
                        ifsc_row = db.execute("SELECT ifsc_code FROM ifsc_codes WHERE branch_name = ?", (branch_name.lower(),)).fetchone()
                        if ifsc_row:
                            response = f"The IFSC code for the {branch_name} branch is: {ifsc_row['ifsc_code']}"
                        else:
                            response = f"I don't have the code for {branch_name}."
                    else:
                        response = bot_responses["find_ifsc_code"]
                        db.execute("UPDATE sessions SET current_state = ? WHERE session_id = ?", ("awaiting_branch_name", session_id)) # Set memory

                elif top_intent == "summarize_conversation":
                    history_rows = db.execute("SELECT sender, message FROM history WHERE session_id = ?", (session_id,)).fetchall()
                    if not history_rows:
                        response = "We haven't talked about anything yet!"
                    else:
                        history_text = "\n".join([f"{row['sender']}: {row['message']}" for row in history_rows])
                        # Call the LLM with the *summarize* prompt
                        response = get_llm_response(history_text, "summarize") 

                elif top_intent == "open_account":
                    response = bot_responses["open_account"]
                    db.execute("UPDATE sessions SET current_state = ? WHERE session_id = ?", ("awaiting_account_type", session_id)) # Set memory
                
                else:
                    response = bot_responses.get(top_intent, bot_responses["fallback"])
            
            else:
                # LOW CONFIDENCE: It's chitchat, a typo, OR a new bank task.
                # Send to the LLM for the ONE-SHOT, FAST response.
                print(f"Local Intent failed (Score: {intent_score:.2f}). Sending to LLM...")
                
                # Get chat history for context
                history_rows = db.execute("SELECT sender, message FROM history WHERE session_id = ? ORDER BY timestamp DESC LIMIT 10", (session_id,)).fetchall()
                history_text = "\n".join([f"{row['sender']}: {row['message']}" for row in reversed(history_rows)])
                
                response = get_llm_response(user_text, history_text)

        # --- Save Bot Response to History ---
        db.execute("INSERT INTO history (session_id, sender, message) VALUES (?, 'bot', ?)", (session_id, response))
        db.commit() # Commit all changes
        
        # --- Send Response (with session_id) ---
        return jsonify({"response": response, "session_id": session_id})

    except Exception as e:
        print(f"Error: {e}")
        if 'db' in locals():
            db.close() # Close connection on error
        return jsonify({"response": "I'm sorry, I ran into an error. Please try again.", "session_id": None})
    finally:
        if 'db' in locals():
            db.close() # Always close the connection

# --- 8. RUN THE APP ---
if __name__ == "__main__":
    app.run(debug=True, port=5000)