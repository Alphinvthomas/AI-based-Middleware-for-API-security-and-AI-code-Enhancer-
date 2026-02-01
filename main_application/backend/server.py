import requests

SERVER_A_URL = "http://localhost:8000"

def fetch_api_source(api_name):
    response = requests.get(f"{SERVER_A_URL}/source/{api_name}")
    response.raise_for_status()
    return response.json()

if __name__ == "__main__":
    api_name = "login"
    data = fetch_api_source(api_name)

    print("API Name:", data["api_name"])
    print("Source Code:\n", data["source_code"])
