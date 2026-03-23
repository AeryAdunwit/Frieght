from __future__ import annotations

from .intent_router_core import ChatIntent, classify_intent


class IntentRouterService:
    def classify(self, message: str) -> ChatIntent:
        return classify_intent(message)
