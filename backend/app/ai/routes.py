import os

from flask import Blueprint, jsonify, request

from app.ai.provider import GeminiProvider
from app.ai.service import ask_assistant
from app.api.errors import APIError
from app.services.common import get_harbour_or_404, parse_id

ai_bp = Blueprint("ai", __name__, url_prefix="/api/ai")


@ai_bp.post("/assistant")
def assistant():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise APIError("A valid JSON object is required.")
    harbour_id = parse_id(payload.get("harbour_id"), "harbour_id")
    message = payload.get("message")
    if not isinstance(message, str) or not message.strip():
        raise APIError("message must be a non-empty string.")
    if len(message) > 2000:
        raise APIError("message must be 2000 characters or fewer.")
    get_harbour_or_404(harbour_id)
    if not os.environ.get("GEMINI_API_KEY", "").strip():
        return jsonify({"available": False, "message": "AI assistant is not configured."})
    return jsonify(ask_assistant(harbour_id, message.strip(), GeminiProvider()))
