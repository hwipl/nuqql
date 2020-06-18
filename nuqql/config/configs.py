"""
nuqql configurations
"""

import logging

from typing import Dict, Any

logger = logging.getLogger(__name__)

# configurations
CONFIGS: Dict[str, Any] = {}


def get(name: str) -> Any:
    """
    Get configuration identified by name
    """

    return CONFIGS[name]
