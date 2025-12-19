import joblib
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline

# 1. Define Training Data (The Local Brain's Knowledge)
# Format: (User Says, Intent)
data = [
    # GREETINGS
    ("hello", "greeting"), ("hi", "greeting"), ("hey vaulty", "greeting"), 
    ("good morning", "greeting"), ("are you there", "greeting"),

    # BRANCHES
    ("where are your branches", "branches"), ("list branches", "branches"),
    ("location of bank", "branches"), ("show me the map", "branches"),

    # BALANCE
    ("check my balance", "balance"), ("how much money do i have", "balance"),
    ("show account balance", "balance"), ("what is my balance", "balance"),
    
    # STAFF
    ("who works here", "staff"), ("list employees", "staff"), ("staff details", "staff")
]

# Separate data
X_train = [text for text, label in data]
y_train = [label for label, text in data]

# 2. Create the Model Pipeline
# CountVectorizer: Converts words to numbers
# MultinomialNB: A fast, efficient classifier for text
model = make_pipeline(CountVectorizer(), MultinomialNB())

# 3. Train the Model
print("🧠 Training Local Brain...")
model.fit(X_train, y_train)

# 4. Save the Brain
joblib.dump(model, "local_brain.pkl")
print("✅ Brain saved as 'local_brain.pkl'. Ready for app.py!")