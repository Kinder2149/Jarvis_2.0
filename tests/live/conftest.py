"""
conftest.py pour tests/live/ — rend les fixtures de conftest_jarvis.py
disponibles à pytest (qui ne charge que les fichiers nommés conftest.py).
"""
from tests.live.conftest_jarvis import conv, conv_with_project  # noqa: F401
