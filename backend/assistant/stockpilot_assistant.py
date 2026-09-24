"""
StockPilot Assistant

Lightweight RAG-based assistant that interprets analysis results
in natural language. It does NOT replace existing workflows -
it explains what the current page/data means to the user.

Uses:
- Ollama (qwen3:8b) for natural language generation
- PostgreSQL full-text search for knowledge base RAG
- Page context (analysis results, dashboard data) as input
"""

import json
from typing import Dict, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import text

from assistant.ollama_provider import OllamaProvider
from models import KnowledgeBase

SYSTEM_PROMPT = """You are StockPilot Assistant, an AI helper for inventory managers.

Your role:
- Explain analysis results in plain language
- Highlight what matters most (risks, actions needed)
- Answer questions about what the user sees on screen
- Help users find features in the application

Rules:
- Be concise (2-4 sentences max unless asked for detail)
- Focus on actionable insights, not raw numbers
- Never make up data - only use what's provided in the context
- If you don't know, say so
- Do not execute any actions - only explain and advise"""


class StockPilotAssistant:

    def __init__(self, db: Session):
        self.db = db
        self._provider = None

    @property
    def provider(self):
        if self._provider is None:
            self._provider = OllamaProvider()
        return self._provider

    def search_knowledge(self, query: str, limit: int = 3) -> List[Dict]:
        try:
            results = self.db.query(KnowledgeBase).filter(
                KnowledgeBase.key.ilike(f'%{query}%') |
                KnowledgeBase.content.ilike(f'%{query}%')
            ).limit(limit).all()
            return [r.to_dict() for r in results]
        except Exception:
            return []

    def _chat(self, user_msg: str, context: str, max_tokens: int = 300) -> str:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"{context}\n\n{user_msg}"}
        ]
        return self.provider.chat(messages, temperature=0.3, max_tokens=max_tokens)

    def explain_analysis(self, analysis_data: Dict) -> str:
        knowledge = self.search_knowledge('analysis reorder risk')
        kb_context = '\n'.join([f"- {k['key']}: {k['content']}" for k in knowledge])
        context = f"Page: SKU Analysis Results\nData: {json.dumps(analysis_data, default=str)[:2000]}\n\nKnowledge Base:\n{kb_context}"
        return self._chat("Explain these analysis results to an inventory manager. What should they do? Highlight the most important finding.", context)

    def explain_dashboard(self, dashboard_data: Dict) -> str:
        knowledge = self.search_knowledge('dashboard inventory')
        kb_context = '\n'.join([f"- {k['key']}: {k['content']}" for k in knowledge])
        context = f"Page: Inventory Dashboard\nData: {json.dumps(dashboard_data, default=str)[:2000]}\n\nKnowledge Base:\n{kb_context}"
        return self._chat("Summarize the current inventory situation. What needs immediate attention? Keep it brief.", context, 200)

    def explain_forecast(self, forecast_data: Dict) -> str:
        knowledge = self.search_knowledge('forecast ML machine learning')
        kb_context = '\n'.join([f"- {k['key']}: {k['content']}" for k in knowledge])
        context = f"Page: Demand Forecast\nData: {json.dumps(forecast_data, default=str)[:2000]}\n\nKnowledge Base:\n{kb_context}"
        return self._chat("Explain this forecast to a non-technical user. Is ML or statistical being used? What does the confidence level mean?", context)

    def explain_simulation(self, simulation_data: Dict) -> str:
        context = f"Page: Baseline Comparison Simulation\nData: {json.dumps(simulation_data, default=str)[:2000]}"
        return self._chat("Compare the two strategies shown. Which is better and why? Explain in business terms.", context, 250)

    def answer_question(self, question: str, page_context: Optional[Dict] = None) -> str:
        knowledge = self.search_knowledge(question)
        kb_context = '\n'.join([f"- {k['key']}: {k['content']}" for k in knowledge])
        context_str = f"Current page data: {json.dumps(page_context, default=str)[:1500]}\n\n" if page_context else ""
        context = f"""{context_str}Knowledge Base:\n{kb_context}\n\nApp features: Dashboard (overview), Analysis (ML forecast + risk), Simulation (strategy comparison), Auto-Generate PO, Send Alert, Run Reorder Check"""
        return self._chat(question, context)
