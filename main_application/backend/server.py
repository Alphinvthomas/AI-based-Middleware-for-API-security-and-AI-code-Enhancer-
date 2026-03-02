import requests
import os
import re
from dotenv import load_dotenv

load_dotenv()  

# 🔐 Use environment variable instead of hardcoding
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

SERVER_A_URL = "http://localhost:8000"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL_NAME = "llama-3.1-8b-instant"


# ---------------------------------------------
# Fetch API Source from Server A
# ---------------------------------------------
def fetch_api_source(api_name):
    response = requests.get(f"{SERVER_A_URL}/source/{api_name}")
    response.raise_for_status()
    return response.json()


# ---------------------------------------------
# Extract numeric score safely
# ---------------------------------------------
def extract_score(text):
    match = re.search(r'\d+', text)
    if match:
        return int(match.group())
    return 0


# ---------------------------------------------
# Get Security Score from LLM
# ---------------------------------------------
def get_security_score(source_code: str):

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = f"""
    You are a cybersecurity expert.
    Analyze the following API source code and give a security score from 1 to 100.
    Only return a number.

    Code:
    {source_code}
    """

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0
    }

    response = requests.post(GROQ_URL, headers=headers, json=payload)

    if response.status_code == 200:
        result = response.json()
        score_text = result["choices"][0]["message"]["content"]
        return extract_score(score_text)
    else:
        print("Score API Error:", response.status_code)
        print("Response:", response.text)
        return None


# ---------------------------------------------
# Generate Secure Code Suggestion
# ---------------------------------------------
def get_secure_code_suggestion(source_code: str):

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = f"""
    You are a senior backend security engineer.

    Rewrite the following API to make it secure.
    Improve:
    - Input validation
    - Authentication logic
    - Proper error handling
    - Avoid hardcoded credentials
    - Follow secure coding best practices

    Return only the improved Python code.

    Code:
    {source_code}
    """

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }

    response = requests.post(GROQ_URL, headers=headers, json=payload)

    if response.status_code == 200:
        result = response.json()
        return result["choices"][0]["message"]["content"].strip()
    else:
        print("Secure Code API Error:", response.status_code)
        print("Response:", response.text)
        return "Secure code generation failed."


# ---------------------------------------------
# Main Execution
# ---------------------------------------------
if __name__ == "__main__":

    if not GROQ_API_KEY:
        print("⚠️ GROQ_API_KEY not set. Please configure environment variable.")
        exit()

    api_name = "login"

    data = fetch_api_source(api_name)
    source_code = data["source_code"]

    print("\n==============================")
    print("API Name:", data["api_name"])
    print("==============================")
    print("Original Source Code:\n")
    print(source_code)

    score = get_security_score(source_code)

    if score is None:
        print("Security scoring failed.")
        exit()

    print("\nSecurity Score:", score)

    if score < 70:
        print("\n⚠️ Security Score below threshold. Generating secure version...\n")
        secure_code = get_secure_code_suggestion(source_code)

        print("Suggested Secure Code:\n")
        print(secure_code)
    else:
        print("\n✅ API security level is acceptable.")