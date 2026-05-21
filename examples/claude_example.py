"""
Use Claude without any API key in your code.

Setup:
  pip install dlyaka anthropic
  dlyaka add anthropic sk-ant-...

Run:
  python examples/claude_example.py
"""
from dlyaka.providers.claude import get_client

client = get_client()  # prompts for master password

message = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello! Tell me a fun fact."}],
)
print(message.content[0].text)
