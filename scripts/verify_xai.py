import os
import sys
from openai import OpenAI
from dotenv import load_dotenv

# Load env vars
load_dotenv()

api_key = os.getenv("XAI_API_KEY")
if not api_key:
    print("Error: XAI_API_KEY not found in environment.")
    sys.exit(1)

client = OpenAI(
    api_key=api_key,
    base_url="https://api.x.ai/v1"
)

try:
    print("Testing xAI connection...")
    completion = client.chat.completions.create(
        model="grok-3",
        messages=[
            {"role": "system", "content": "You are a test assistant."},
            {"role": "user", "content": "Say 'Connection Successful'"}
        ]
    )
    print(f"Response: {completion.choices[0].message.content}")
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
