import urllib.request
import json
import os

api_key = os.environ.get("GROQ_API_KEY")
print(f"Key starts with: {api_key[:10]}..." if api_key else "NO KEY SET")

payload = json.dumps({
    "model": "llama-3.1-8b-instant",  # Try smaller model
    "messages": [{"role": "user", "content": "Say hello"}],
    "max_tokens": 10,
}).encode()

req = urllib.request.Request(
    "https://api.groq.com/openai/v1/chat/completions",
    data=payload,
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
)

try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        print("SUCCESS:", json.loads(resp.read().decode()))
except urllib.error.HTTPError as e:
    print(f"HTTP {e.code}: {e.reason}")
    print("Response:", e.read().decode())