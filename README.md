# Banking Assistant Bot

A Rasa-powered banking assistant that can help with:
- Bill payments
- Loan applications
- Money transfers
- Balance inquiries
- Account information

## Setup

1. Create virtual environment:
```bash
python -m venv venv_latest
venv_latest\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Train the model:
```bash
rasa train
```

4. Run the bot (open 2 terminals):
```bash
# Terminal 1: Start action server
rasa run actions --port 5055

# Terminal 2: Start Rasa shell
rasa shell
```

## Project Structure

- `actions/` - Custom actions code
- `data/` - Training data (NLU, stories)
- `tests/` - Test stories
- `domain.yml` - Bot domain configuration
- `config.yml` - Pipeline configuration
- `endpoints.yml` - Endpoints configuration