from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification
import os

# --- 1. Load your fine-tuned NER model ---
model_path = os.path.abspath("./ner-bot-model-v1")
print(f"Loading NER model from: {model_path}")

# Explicitly load the tokenizer and model to bypass caching
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForTokenClassification.from_pretrained(model_path)

# Create the NER pipeline
ner_pipeline = pipeline(
    "token-classification",
    model=model,
    tokenizer=tokenizer,
    aggregation_strategy="simple"  # This strategy groups word pieces
)

# --- 2. Test with new sentences ---
print("\n--- Testing NER Model ---")

text1 = "can you send $500 to Alex"
result1 = ner_pipeline(text1)
print(f"\nText: '{text1}'")
print(f"Entities: {result1}")


text2 = "I need to pay my electricity bill"
result2 = ner_pipeline(text2)
print(f"\nText: '{text2}'")
print(f"Entities: {result2}")


text3 = "how much money is in my checking account"
result3 = ner_pipeline(text3)
print(f"\nText: '{text3}'")
print(f"Entities: {result3}")

text4 = "move 1000 from savings to checking"
result4 = ner_pipeline(text4)
print(f"\nText: '{text4}'")
print(f"Entities: {result4}")