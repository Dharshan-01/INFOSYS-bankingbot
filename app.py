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
    # --- BUG 1 FIX: Use the correct model name ---
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

# --- 3. DATABASE HELPER FUNCTIONS ---
def get_db_conn():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row 
    return conn

def load_local_responses_from_db():
    """Loads the entire knowledge base from the DB into a dictionary."""
    print("Loading Knowledge Base from 'bot_database.db'...")
    try:
        db = get_db_conn()
        # --- NEW FEATURE: Select all 5 columns ---
        rows = db.execute("SELECT intent_name, response_text, response_link, link_text, suggested_questions FROM kb_local_intents").fetchall()
        db.close()
        # --- NEW FEATURE: Store all 5 columns ---
        responses = {
            row['intent_name']: {
                'text': row['response_text'], 
                'link': row['response_link'],
                'link_text': row['link_text'],
                'suggestions': row['suggested_questions'] # Add the suggestions
            } for row in rows
        }
        print(f"SUCCESS: Loaded {len(responses)} local intents from DB.")
        return responses
    except Exception as e:
        print(f"FATAL ERROR: Could not load Knowledge Base from DB. {e}")
        print("Please re-run 'python database_setup.py' and restart.")
        return None

# --- 4. LOAD KNOWLEDGE & MODELS ONCE ---
bot_responses = load_local_responses_from_db() 
if not bot_responses:
    bot_responses = {
        # Fixed the SyntaxError here
        "fallback": {'text': "I'm sorry, my local knowledge base failed to load. Please contact support.", 'link': None, 'link_text': None, 'suggestions': None}
    }

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


# --- 5. DEFINE LLM HELPER FUNCTION (UPGRADED) ---
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

# --- NEW: Create a list of links to "teach" the LLM ---
def build_link_prompt():
    """Builds a string of linkable topics for the LLM."""
    link_list = ""
    for intent, data in bot_responses.items():
        if data.get("link") and data.get("link_text"):
            link_list += f"- Topic: '{intent}' (e.g., questions about {intent.replace('_', ' ')})\n"
            link_list += f"- Link: <a href='{data['link']}' target='_blank'>{data['link_text']}</a>\n\n"
    return link_list

LINK_KNOWLEDGE_FOR_LLM = build_link_prompt()

def get_llm_response(user_text, llm_mode, chat_history_string=""):
    if not llm_model:
        return bot_responses["fallback"]["text"]
    
    prompt = ""
    known_intents_list = "\n".join([f"- {key}: {value['text']}" for key, value in bot_responses.items() if key != "fallback"])

    if llm_mode == "smart_fallback":
        prompt = f"""
        You are a "Super Bot", a helpful and polite bank assistant.
        Your job is to triage the user's LATEST message. You have two brains:
        1. A "Local Brain" with pre-written answers for known intents.
        2. A "Cloud Brain" (you) for everything else.

        HERE ARE THE KNOWN LOCAL INTENTS:
        {known_intents_list}
        ---
        
        --- NEW KNOWLEDGE: HERE IS A LIST OF OUR BANK'S WEBPAGES ---
        {LINK_KNOWLEDGE_FOR_LLM}
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
           - If it IS a typo for a known intent, respond with ONLY the string "LOCAL_INTENT: [intent_name]". (e.g., "LOCAL_INTENT: check_balance_guide")
        
        3. **If it's NOT a typo,** check if it's "General-Chitchat" (like "hello" (which is 'greet'), "good morning", "what's the weather?").
           - If it IS chitchat, just be friendly and polite (e.g., "Hello! How can I help you today?").
        
        4. **If it's NOT chitchat,** it must be a "New Banking-Related Question" (like "i need a credit card" or "how to apply for a car loan").
           - If it IS a new banking question, give a helpful, general answer.
           - **AND** check your "NEW KNOWLEDGE" list. If the question is about one of those topics, you **MUST** include the correct HTML link in your response.
           - Example: If the user asks for a "loan", you MUST add the link for "check_loan_status_guide". If they ask for a "credit card", you MUST add the link for "block_card_guide" (as it's the closest match).
           - **Strictly** DO NOT ask for personal information.
        
        Provide ONLY the final response. If you match a local intent typo, return ONLY the "LOCAL_INTENT: [intent_name]" string.
        """
    elif llm_mode == "summarize":
        prompt = f"You are a bank assistant. Summarize the key bank-related topics from the following conversation.\nConversation History:\n{user_text}"
    
    try:
        if not prompt: 
            print(f"LLM Error: No prompt generated for mode {llm_mode}")
            return bot_responses["fallback"]["text"]
            
        response = llm_model.generate_content(prompt, safety_settings=safety_settings)
        return response.text.strip()
    except Exception as e:
        print(f"LLM Error ({llm_mode}): {e}")
        return bot_responses["fallback"]["text"]


# --- 6. CREATE THE API ENDPOINT (UPGRADED LOGIC) ---
@app.route("/chat", methods=["POST"])
def chat():
    db = get_db_conn() 
    
    try:
        data = request.json
        user_text = data["message"]
        session_id = data["session_id"]
        
        user_text_lower = user_text.lower() 

        if session_id == "new":
            session_id = str(uuid.uuid4()) 
            db.execute("INSERT INTO sessions (session_id, current_state) VALUES (?, NULL)", (session_id,))
            print(f"New session created: {session_id}")
        
        db.execute("INSERT INTO history (session_id, sender, message) VALUES (?, 'user', ?)", (session_id, user_text))

        state_row = db.execute("SELECT current_state FROM sessions WHERE session_id = ?", (session_id,)).fetchone()
        state = state_row['current_state'] if state_row else None

        response_text = ""
        response_data = {} 
        add_link = False # Flag to control adding the link
        suggestions = [] # <-- NEW FEATURE: Start with empty suggestions

        # --- Check "Memory" (State Management) FIRST ---
        if state == "awaiting_account_type":
            print("Bot state is 'awaiting_account_type'. Checking user response...")
            
            response_data = bot_responses.get("open_account")
            add_link = True # We want to add the link
            
            if "savings" in user_text_lower:
                response_text = "To open a Savings account, you will need your PAN and Aadhar card. You can start the process on our website or visit a branch."
            elif "current" in user_text_lower:
                response_text = "To open a Current account, you will need your business registration documents. Please visit a branch for assistance."
            elif "demat" in user_text_lower:
                response_text = "To open a Demat account, you will need your PAN, Aadhar, and a blank cheque. You can start the process on our website."
            else:
                response_text = "I'm sorry, I didn't recognize that account type. We offer Savings, Current, and Demat accounts."
                add_link = False # Don't add a link if the answer is wrong
            
            db.execute("UPDATE sessions SET current_state = NULL WHERE session_id = ?", (session_id,)) 

        elif state == "awaiting_branch_name":
            print("Bot state is 'awaiting_branch_name'. Checking user response...")
            entities = ner_pipeline(user_text)
            branch_name = user_text # Default
            for entity in entities:
                if entity['entity_group'] == 'BRANCH':
                    branch_name = entity['word']; break
            
            ifsc_row = db.execute("SELECT ifsc_code FROM ifsc_codes WHERE branch_name = ?", (branch_name.lower(),)).fetchone()
            if ifsc_row:
                response_text = f"The IFSC code for the {branch_name} branch is: {ifsc_row['ifsc_code']}"
            else:
                response_text = f"I don't have the code for {branch_name}, but you can find all codes on our website."
            db.execute("UPDATE sessions SET current_state = NULL WHERE session_id = ?", (session_id,)) 

        else:
            # --- No "Memory" set -> Run NLU and TRIAGE ---
            print("Bot state is 'None'. Running NLU...")
            intent_result = intent_classifier(user_text)
            top_intent = intent_result[0]['label']
            intent_score = intent_result[0]['score']

            if intent_score > 0.7:
                print(f"Local Intent: {top_intent} (Score: {intent_score:.2f})")
                
                # --- NEW FEATURE: Get the full response data ---
                response_data = bot_responses.get(top_intent, bot_responses["fallback"])
                response_text = response_data["text"]
                add_link = True # Flag that we want to add a link
                
                # --- NEW FEATURE: Check for and parse suggestions ---
                suggestions_string = response_data.get("suggestions")
                if suggestions_string:
                    suggestions = suggestions_string.split('|')

                # --- Handle special dynamic/multi-step intents ---
                if top_intent == "get_interest_rates":
                    rates_rows = db.execute("SELECT product_name, rate FROM interest_rates").fetchall()
                    response_text = "Our current interest rates are:\n"
                    for row in rates_rows:
                        response_text += f"  - {row['product_name']}: {row['rate']}\n"
                    add_link = False # No link for this dynamic one

                elif top_intent == "find_ifsc_code":
                    entities = ner_pipeline(user_text)
                    branch_name = None
                    for entity in entities:
                        if entity['entity_group'] == 'BRANCH':
                            branch_name = entity['word']; break
                    if branch_name:
                        ifsc_row = db.execute("SELECT ifsc_code FROM ifsc_codes WHERE branch_name = ?", (branch_name.lower(),)).fetchone()
                        if ifsc_row: response_text = f"The IFSC code for the {branch_name} branch is: {ifsc_row['ifsc_code']}"
                        else: response_text = f"I don't have the code for {branch_name}."
                        add_link = False # Already answered
                    else:
                        db.execute("UPDATE sessions SET current_state = ? WHERE session_id = ?", ("awaiting_branch_name", session_id)) # Set memory

                elif top_intent == "summarize_conversation":
                    history_rows = db.execute("SELECT sender, message FROM history WHERE session_id = ?", (session_id,)).fetchall()
                    if not history_rows: response_text = "We haven't talked about anything yet!"
                    else:
                        history_text = "\n".join([f"{row['sender']}: {row['message']}" for row in history_rows])
                        response_text = get_llm_response(history_text, "summarize") 
                    add_link = False

                elif top_intent == "open_account":
                    db.execute("UPDATE sessions SET current_state = ? WHERE session_id = ?", ("awaiting_account_type", session_id)) # Set memory
                
                # (No 'else' needed, default case is handled above)
            
            else:
                # --- LLM Triage (now smarter) ---
                print(f"Local Intent failed (Score: {intent_score:.2f}). Sending to LLM...")
                history_rows = db.execute("SELECT sender, message FROM history WHERE session_id = ? ORDER BY timestamp DESC LIMIT 10", (session_id,)).fetchall()
                history_text = "\n".join([f"{row['sender']}: {row['message']}" for row in reversed(history_rows)])
                
                response_text = get_llm_response(user_text, "smart_fallback", chat_history_string=history_text)

                if response_text.startswith("LOCAL_INTENT:"):
                    intent_name = response_text.split(":")[-1].strip()
                    print(f"LLM corrected typo to: {intent_name}")
                    response_data = bot_responses.get(intent_name, bot_responses["fallback"])
                    response_text = response_data["text"]
                    add_link = True # Flag that we want to add a link
                    # --- NEW FEATURE: Get suggestions for LLM-corrected typos ---
                    suggestions_string = response_data.get("suggestions")
                    if suggestions_string:
                        suggestions = suggestions_string.split('|')
                
                else:
                    add_link = False # The LLM already added the link if needed

        # --- NEW: Centralized Link Logic ---
        if add_link:
            if response_data and response_data.get("link") and response_data.get("link_text"):
                response_text += f"<br><br><a href='{response_data['link']}' target='_blank'>{response_data['link_text']}</a>"


        # --- Save Bot Response to History ---
        db.execute("INSERT INTO history (session_id, sender, message) VALUES (?, 'bot', ?)", (session_id, response_text.split("<br>")[0]))
        db.commit() 
        
        # --- NEW FEATURE: Return suggestions to the frontend ---
        return jsonify({"response": response_text, "session_id": session_id, "suggestions": suggestions})

    except Exception as e:
        print(f"Error: {e}")
        if 'db' in locals():
            db.close()
        return jsonify({"response": "I'm sorry, I ran into an error. Please try again.", "session_id": None, "suggestions": []})
    finally:
        if 'db' in locals():
            db.close() 

# --- 7. RUN THE APP ---
if __name__ == "__main__":
    app.run(debug=True, port=5000)
