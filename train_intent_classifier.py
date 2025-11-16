import pandas as pd
from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer
)
import numpy as np
import evaluate

# --- 1. Load and Prepare Data ---
print("Loading dataset...")
df = pd.read_csv("data/intents.csv")
labels_list = df["intent"].unique().tolist()
label2id = {label: i for i, label in enumerate(labels_list)}
id2label = {i: label for i, label in enumerate(labels_list)}
print(f"Label mappings created: {label2id}")
df["label"] = df["intent"].map(label2id)
dataset = Dataset.from_pandas(df)
dataset = dataset.train_test_split(test_size=0.2, shuffle=True)

# --- 2. Tokenization ---
model_name = "distilbert-base-uncased"
tokenizer = AutoTokenizer.from_pretrained(model_name)

def tokenize_function(examples):
    return tokenizer(examples["text"], padding="max_length", truncation=True)

print("Tokenizing dataset...")
tokenized_datasets = dataset.map(tokenize_function, batched=True)

# --- 3. Load Model & Configure ---
print("Loading pre-trained model...")
model = AutoModelForSequenceClassification.from_pretrained(
    model_name,
    num_labels=len(labels_list),
    id2label=id2label,
    label2id=label2id
)

# --- 4. Training ---
accuracy_metric = evaluate.load("accuracy")
def compute_metrics(eval_pred):
    predictions, labels = eval_pred
    predictions = np.argmax(predictions, axis=1) 
    return accuracy_metric.compute(predictions=predictions, references=labels)

training_args = TrainingArguments(
    output_dir="./banking-bot-model-v1", # The good folder
    eval_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    num_train_epochs=50,                 # Train for 50 epochs
    weight_decay=0.01,
    save_strategy="epoch",
    load_best_model_at_end=True,
    report_to="none", # Add this if you get the wandb error
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_datasets["train"],
    eval_dataset=tokenized_datasets["test"],
    tokenizer=tokenizer,
    compute_metrics=compute_metrics,
)

print("Starting training...")
trainer.train()

print("Training complete. Saving model...")
trainer.save_model("./banking-bot-model-v1")
print("Model saved to ./banking-bot-model-v1")