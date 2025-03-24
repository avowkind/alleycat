"""Knowledge Base Provider.

This module defines the interface for knowledge base providers.

Author: Andrew Watkins <andrew@groat.nz>
"""

from alleycat_core.config.settings import Settings
from alleycat_core.kb.base import KBProvider
from alleycat_core.kb.openai import OpenAIKBFactory


async def get_kb_provider(settings: Settings) -> KBProvider:
    """Get a knowledge base provider based on settings.

    Currently only supports OpenAI.

    Args:
        settings: Application settings.

    Returns:
        A knowledge base provider.

    Raises:
        ValueError: If no provider is available.

    """
    if settings.openai_api_key:
        factory = OpenAIKBFactory()
        return factory.create(api_key=settings.openai_api_key)

    raise ValueError("No KB provider available. Please set OPENAI_API_KEY in your environment.")
