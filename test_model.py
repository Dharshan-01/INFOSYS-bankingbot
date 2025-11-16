from transformers import (
    pipeline, 
    AutoTokenizer, 
    AutoModelForSequenceClassification
)
import os

# --- 1. Load your fine-tuned model (The Explicit Way) ---

# Load from the NEW folder
model_path = os.path.abspath("./banking-bot-model-v1")
print(f"Loading model and tokenizer from: {model_path}")

tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForSequenceClassification.from_pretrained(model_path)

# 2. Create the pipeline using the loaded objects
print("Creating pipeline with loaded model...")
classifier = pipeline(
    "text-classification", 
    model=model, 
    tokenizer=tokenizer
)

# --- 3. Test with new sentences ---
print("\n--- Testing Model ---")

text1 = "how much money do I have?"
result1 = classifier(text1)
print(f"Text: '{text1}' \nPrediction: {result1[0]['label']} (Score: {result1[0]['score']:.4f})")

text2 = "I need to pay my gas bill"
result2 = classifier(text2)
print(f"\nText: '{text2}' \nPrediction: {result2[0]['label']} (Score: {result2[0]['score']:.4f})")

text3 = "my debit card is missing"
result3 = classifier(text3)
print(f"\nText: '{text3}' \nPrediction: {result3[0]['label']} (Score: {result3[0]['score']:.4f})")

text4 = "send money" 
result4 = classifier(text4)
print(f"\nText: '{text4}' \nPrediction: {result4[0]['label']} (Score: {result4[0]['score']:.4f})")