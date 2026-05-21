from typing import Optional

from ..vault import get_key


def get_client(password: Optional[str] = None):
    """Return an authenticated Anthropic client using the stored key.

    Requires: pip install anthropic
    """
    try:
        import anthropic
    except ImportError:
        raise ImportError("Install the Anthropic SDK: pip install anthropic")

    api_key = get_key("anthropic", password)
    return anthropic.Anthropic(api_key=api_key)
