import spacy
import random
import string
import re
import pandas as pd
from flask import Flask, request, jsonify

# Load pre-trained NLP model for PII detection
nlp = spacy.load("en_core_web_sm")

def generate_token():
    """Generate a unique and secure random token."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=12))

def detect_and_tokenize(text, token_map):
    """Detect PII in text and replace it with a token."""
    doc = nlp(text)

    # Tokenize detected entities (Names, Locations, etc.)
    for ent in doc.ents:
        if ent.label_ in ["PERSON", "ORG", "GPE", "CARDINAL", "PHONE", "DATE"]:
            if ent.text not in token_map:
                token_map[ent.text] = generate_token()
            text = text.replace(ent.text, token_map[ent.text])

    # Additional step: Tokenize Emails using Regex
    email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    emails = re.findall(email_pattern, text)

    for email in emails:
        if email not in token_map:
            token_map[email] = generate_token()
        text = text.replace(email, token_map[email])

    return text, token_map

# Initialize Flask API
app = Flask(__name__)

token_map = {}  # Global token map for persistent tokenization

@app.route('/tokenize', methods=['POST'])
def tokenize_data():
    """API endpoint to tokenize sensitive data."""
    global token_map  # Keep token map persistent across requests

    data = request.json.get("data", "")
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    tokenized_data, updated_map = detect_and_tokenize(data, token_map)
    return jsonify({
        "original": data,
        "tokenized": tokenized_data,
        "token_map": updated_map
    })

@app.route('/detokenize', methods=['POST'])
def detokenize_data():
    """API endpoint to reverse tokenization."""
    data = request.json.get("data", "")
    if not data:
        return jsonify({"error": "No data provided"}), 400

    reversed_text = data
    for key, value in token_map.items():
        reversed_text = reversed_text.replace(value, key)

    return jsonify({"original": reversed_text, "detokenized": data})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
