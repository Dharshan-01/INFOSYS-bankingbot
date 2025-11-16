import json
from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForTokenClassification,
    TrainingArguments,
    Trainer,
    DataCollatorForTokenClassification
)
import numpy as np
import evaluate

# --- 1. Define Labels and Mappings ---
# NEW
label_list = ["O", "B-AMOUNT", "I-AMOUNT", "B-RECIPIENT", "I-RECIPIENT", "B-ACCOUNT_TYPE", "I-ACCOUNT_TYPE", "B-BILL_TYPE", "I-BILL_TYPE", "B-BRANCH", "I-BRANCH"]
label2id = {label: i for i, label in enumerate(label_list)}
id2label = {i: label for i, label in enumerate(label_list)}
num_labels = len(label_list)

# --- 2. Load and Prepare Data ---
print("Loading dataset from data/ner_data.json...")
# Use the new, larger dataset
with open("data/ner_data.json", "r") as f:
    raw_data = json.load(f)

# Convert to Hugging Face Dataset
dataset = Dataset.from_list(raw_data)

# --- 3. Tokenization and Label Alignment ---
model_name = "distilbert-base-uncased"
tokenizer = AutoTokenizer.from_pretrained(model_name)

def tokenize_and_align_labels(examples):
    tokenized_inputs = tokenizer(examples["text"], truncation=True, is_split_into_words=False)
    
    all_labels = []
    for i, example in enumerate(examples["text"]):
        word_ids = tokenized_inputs.word_ids(batch_index=i)
        labels = [label2id["O"]] * len(word_ids)
        entities = examples["entities"][i]
        
        for entity in entities:
            entity_start = entity["start"]
            entity_end = entity["end"]
            entity_label = entity["label"]

            start_token_idx = -1
            end_token_idx = -1
            
            for token_idx, word_id in enumerate(word_ids):
                if word_id is None:
                    continue
                
                # This is the corrected line:
                char_span = tokenized_inputs.token_to_chars(i, token_index=token_idx)
                if char_span is None:
                    continue
                
                token_start, token_end = char_span.start, char_span.end
                
                if token_start == entity_start:
                    start_token_idx = token_idx
                
                if token_end == entity_end:
                    end_token_idx = token_idx
                    break 

            if start_token_idx != -1 and end_token_idx != -1:
                labels[start_token_idx] = label2id[f"B-{entity_label}"]
                for idx in range(start_token_idx + 1, end_token_idx + 1):
                    labels[idx] = label2id[f"I-{entity_label}"]
            elif start_token_idx != -1: # Handle entities that are just one token
                 labels[start_token_idx] = label2id[f"B-{entity_label}"]

        all_labels.append(labels)

    tokenized_inputs["labels"] = all_labels
    return tokenized_inputs

print("Tokenizing and aligning labels...")
tokenized_datasets = dataset.map(tokenize_and_align_labels, batched=True, batch_size=2, remove_columns=dataset.column_names)
tokenized_datasets = tokenized_datasets.train_test_split(test_size=0.2)

# --- 4. Load Model and Collator ---
print("Loading pre-trained model...")
model = AutoModelForTokenClassification.from_pretrained(
    model_name,
    num_labels=num_labels,
    id2label=id2label,
    label2id=label2id
)
data_collator = DataCollatorForTokenClassification(tokenizer=tokenizer)

# --- 5. Training ---
seqeval_metric = evaluate.load("seqeval")

def compute_metrics(p):
    predictions, labels = p
    predictions = np.argmax(predictions, axis=2)
    true_predictions = [
        [id2label[p] for (p, l) in zip(prediction, label) if l != -100]
        for prediction, label in zip(predictions, labels)
    ]
    true_labels = [
        [id2label[l] for (p, l) in zip(prediction, label) if l != -100]
        for prediction, label in zip(predictions, labels)
    ]
    results = seqeval_metric.compute(predictions=true_predictions, references=true_labels)
    return {
        "precision": results["overall_precision"],
        "recall": results["overall_recall"],
        "f1": results["overall_f1"],
        "accuracy": results["overall_accuracy"],
    }

# We'll save this model to a new folder
training_args = TrainingArguments(
    output_dir="./ner-bot-model-v1",
    eval_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    num_train_epochs=300,  # Train for 300 epochs
    weight_decay=0.01,
    save_strategy="epoch",
    load_best_model_at_end=True,
    save_total_limit=2,  # <-- THIS LINE SAVES YOUR DISK SPACE
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_datasets["train"],
    eval_dataset=tokenized_datasets["test"],
    tokenizer=tokenizer,
    data_collator=data_collator,
    compute_metrics=compute_metrics,
)

print("Starting NER training...")
trainer.train()

print("Training complete. Saving model...")
trainer.save_model("./ner-bot-model-v1")
print("Model saved to ./ner-bot-model-v1")