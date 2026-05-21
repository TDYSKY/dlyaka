"""
Use ChatGPT without any API key in your code.

Setup:
  pip install dlyaka openai
  dlyaka add openai sk-...

Run:
  python examples/chatgpt_example.py
"""
from dlyaka.providers.gpt import get_client

client = get_client()  # prompts for master password

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello! Tell me a fun fact."}],
)
print(response.choices[0].message.content)
