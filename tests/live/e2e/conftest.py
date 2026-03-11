"""
Configuration pytest pour tests E2E.

Garantit un nouvel event loop par test pour éviter "Event loop is closed".
"""

import pytest
import asyncio


@pytest.fixture(scope="function")
def event_loop():
    """
    Crée un nouvel event loop pour chaque test E2E.
    
    Résout le problème "Event loop is closed" en garantissant que chaque test
    a son propre event loop isolé, évitant la réutilisation d'un event loop fermé
    par le provider Gemini.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()
