from __future__ import annotations

"""Compatibility app entrypoint for the new backend scaffold.

This intentionally re-exports the current live FastAPI instance so the project
can adopt the new package structure incrementally without changing runtime
behavior today.
"""

from ..main import app, health_check  # noqa: F401


def create_app():
    return app

