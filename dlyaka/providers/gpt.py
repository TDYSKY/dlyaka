from typing import Optional

from ..vault import get_key


def get_client(password: Optional[str] = None):
    """Return an authenticated OpenAI client using the stored key.

    Requires: pip install openai
    """
    try:
        import openai
    except ImportError:
        raise ImportError("Install the OpenAI SDK: pip install openai")

    api_key = get_key("openai", password)
    return openai.OpenAI(api_key=api_key)
