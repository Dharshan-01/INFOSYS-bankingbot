from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification, AutoModelForTokenClassification
import os
import json

# --- 1. LOAD BOTH MODELS ---
print("Loading Intent Classifier (banking-bot-model-v1)...")
intent_model_path = os.path.abspath("./banking-bot-model-v1")
intent_tokenizer = AutoTokenizer.from_pretrained(intent_model_path)
intent_model = AutoModelForSequenceClassification.from_pretrained(intent_model_path)
intent_classifier = pipeline("text-classification", model=intent_model, tokenizer=intent_tokenizer)

print("Loading Entity Recognizer (ner-bot-model-v1)...")
ner_model_path = os.path.abspath("./ner-bot-model-v1")
ner_tokenizer = AutoTokenizer.from_pretrained(ner_model_path)
ner_model = AutoModelForTokenClassification.from_pretrained(ner_model_path)
ner_pipeline = pipeline("token-classification", model=ner_model, tokenizer=ner_tokenizer, aggregation_strategy="simple")

print("Bot is ready! Type 'exit' to quit.")

# --- 2. DEFINE THE BOT'S RESPONSES ---
bot_responses = {
    "check_balance_guide": "To check your balance securely, you can use our NetBanking app, check your e-passbook, or use any UPI app in the 'Check Balance' section.",
    "check_transactions_guide": "You can see all your recent transactions by checking the 'Mini Statement' or 'e-Passbook' section in your NetBanking or mobile banking app.",
    "find_account_details": "You can find your account number and customer ID printed on the front page of your bank passbook. You can also find it in your NetBanking app profile section.",
    "manage_credentials": "You can change your ATM PIN by visiting any of our nearest ATMs. You can change your NetBanking password by using the 'Forgot Password' link on the login page and verifying your debit card details.",
    "block_card_guide": "I can help with that. To confirm, are you blocking the card due to it being lost, stolen, or another reason? (This is the start of a multi-turn conversation).",
    "update_kyc": "I can help with that. Are you looking to do a Mini-KYC (online with Aadhar) or a Full KYC?",
    "transfer_funds_guide": "How would you like to transfer the money? By using a Phone Number (UPI), or by using an Account Number (NEFT/IMPS)?",
    "get_transaction_limits": "Our standard daily transaction limits are:\n  - UPI: ₹1,00,000\n  - IMPS: ₹5,00,000\nYou can also check and set your *personal* limits within the 'Security' section of the NetBanking app.",
    "set_transaction_limits": "To set your personal transaction limits for security, please log in to the NetBanking app, go to 'Security & Settings', and select 'Manage Transaction Limits'.",
    "open_account": "What type of account are you interested in? We offer Savings, Current, and Demat accounts.",
    "get_interest_rates": "Our current interest rates are:\n  - Home Loans: Starting from 8.5%\n  - Car Loans: Starting from 9.2%\n  - Savings Account: 3.5%\nWould you like to know the rate for a different loan?",
    "find_ifsc_code": "I can help with that. Which branch's IFSC code do you need?",
    "get_bank_hours": "Our bank branches are open from 10:00 AM to 4:00 PM, Monday to Friday. We are closed on all Saturdays, Sundays, and public holidays.",
    "check_loan_status_guide": "You can check your loan application status by visiting our website, logging in to your loan portal, and entering your application reference number.",
    "pay_bill_guide": "You can pay all your bills (electricity, phone, credit card, etc.) using the 'Bill Pay' or 'BBPS' section in our NetBanking or mobile app.",
    "general_faq": "Our headquarters is located in Mumbai, India. For more information, please visit the 'About Us' section of our website.",
    "greet": "Hello! How can I help you with your banking questions today?",
    "fallback": "I'm sorry, I don't understand that. I can help with questions about account guides, transactions, and bank info."
}

# --- 3. CREATE THE CHATBOT LOOP WITH "MEMORY" ---

# This is the bot's "memory". It starts empty.
current_state = None 

while True:
    try:
        user_text = input("You: ")
        
        if user_text.lower() == 'exit':
            print("Bot: Goodbye!")
            break
        
        response = ""
        
        # --- Check "Memory" (State Management) ---
        # Did the bot just ask a question?
        if current_state == "awaiting_account_type":
            # The user is answering our "open_account" question
            if "savings" in user_text.lower():
                response = "To open a Savings account, you will need your PAN and Aadhar card. You can start the process on our website or visit a branch."
            elif "current" in user_text.lower():
                response = "To open a Current account, you will need your business registration documents. Please visit a branch for assistance."
            elif "demat" in user_text.lower():
                response = "To open a Demat account, you will need your PAN, Aadhar, and a blank cheque. You can start the process on our website."
            else:
                response = "I'm sorry, I didn't recognize that account type. We offer Savings, Current, and Demat accounts."
            current_state = None # Reset memory

        elif current_state == "awaiting_branch_name":
            # The user is answering our "find_ifsc_code" question
            # We can run the NER model on *just this answer*
            entities = ner_pipeline(user_text)
            branch_name = user_text # Use the whole text as a default
            for entity in entities:
                if entity['entity_group'] == 'BRANCH':
                    branch_name = entity['word']
                    break
            
            # This is just a fake lookup for our example
            if "coimbatore" in branch_name.lower():
                response = "The IFSC code for the Coimbatore Main Branch is: FAKE1234567"
            elif "delhi" in branch_name.lower():
                response = "The IFSC code for the Delhi Main Branch is: FAKE7654321"
            else:
                response = f"I don't have the code for {branch_name}, but you can find all codes on our website."
            current_state = None # Reset memory

        else:
            # --- No "Memory" set, so this is a NEW question ---
            # --- NLU (Natural Language Understanding) ---
            
            intent_result = intent_classifier(user_text)
            top_intent = intent_result[0]['label']
            intent_score = intent_result[0]['score']
            entities = ner_pipeline(user_text)

            # --- Dialogue Management (The "Brain") ---
            
            if intent_score < 0.6: # Increased threshold
                response = bot_responses["fallback"]
            
            # Special logic for IFSC code
            elif top_intent == "find_ifsc_code":
                branch_name = None
                for entity in entities:
                    # Look for the NEW 'BRANCH' entity
                    if entity['entity_group'] == 'BRANCH':
                        branch_name = entity['word']
                        break
                
                if branch_name:
                    if "coimbatore" in branch_name.lower():
                        response = "The IFSC code for the Coimbatore Main Branch is: FAKE1234567"
                    else:
                        response = f"I don't have the code for {branch_name}, but you can find all codes on our website."
                else:
                    response = bot_responses["find_ifsc_code"]
                    current_state = "awaiting_branch_name" # Set memory!

            # Special logic for Open Account
            elif top_intent == "open_account":
                response = bot_responses["open_account"]
                current_state = "awaiting_account_type" # Set memory!
            
            # General case: Get the response from our dictionary
            else:
                if top_intent in bot_responses:
                    response = bot_responses[top_intent]
                else:
                    response = bot_responses["fallback"]

        # Send the response
        print(f"Bot: {response}")

    except Exception as e:
        print(f"Error: {e}")
        print("Bot: I'm sorry, I ran into an error. Please try again.")