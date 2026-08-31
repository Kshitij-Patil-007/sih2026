"""
Audit Trail Logger
Logs every routing decision and model call - explicitly required by judges
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List
import json

DB_PATH = Path(__file__).parent.parent / "sih_sessions.db"


def log_event(query_id: str, event_type: str, task: Optional[str] = None,
              model_used: Optional[str] = None, parameters: Optional[Dict] = None,
              details: Optional[str] = None):
    """
    Log an audit event for traceability

    Args:
        query_id: Query this event belongs to
        event_type: Type of event (routing, model_call, preprocessing, error)
        task: Task type determined by router (vqa, caption, change_vqa, etc.)
        model_used: Which model was invoked (gemini, blip2-lora, fusion-model)
        parameters: Dict of parameters passed to the model
        details: Any additional context
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO audit_trail (query_id, timestamp, event_type, task, model_used, parameters, details)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        query_id,
        datetime.utcnow().isoformat(),
        event_type,
        task,
        model_used,
        json.dumps(parameters) if parameters else None,
        details
    ))

    conn.commit()
    conn.close()


def log_routing_decision(query_id: str, query_text: str, task: str,
                         image_count: int, modalities: List[str], reasoning: str):
    """Log when the router classifies a query"""
    log_event(
        query_id=query_id,
        event_type="routing",
        task=task,
        parameters={
            "query_text": query_text,
            "image_count": image_count,
            "modalities": modalities
        },
        details=f"Router decision: {reasoning}"
    )


def log_model_call(query_id: str, model_name: str, task: str,
                   input_params: Dict, success: bool, error: Optional[str] = None):
    """Log when a model is invoked"""
    log_event(
        query_id=query_id,
        event_type="model_call",
        task=task,
        model_used=model_name,
        parameters=input_params,
        details=f"Success: {success}" + (f" | Error: {error}" if error else "")
    )


def log_preprocessing(query_id: str, operation: str, details: str):
    """Log preprocessing steps (GeoTIFF conversion, RGB composite, etc.)"""
    log_event(
        query_id=query_id,
        event_type="preprocessing",
        details=f"{operation}: {details}"
    )


def log_confidence_estimation(query_id: str, model: str, method: str, confidence: float):
    """Log how confidence score was estimated (important for Gemini heuristic)"""
    log_event(
        query_id=query_id,
        event_type="confidence_estimation",
        model_used=model,
        parameters={"method": method, "confidence": confidence},
        details=f"Confidence estimated using {method}"
    )


def get_audit_trail(query_id: str) -> List[Dict]:
    """
    Retrieve complete audit trail for a query
    Returns list sorted by timestamp
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT timestamp, event_type, task, model_used, parameters, details
        FROM audit_trail
        WHERE query_id = ?
        ORDER BY timestamp ASC
    """, (query_id,))

    trail = []
    for row in cursor.fetchall():
        entry = dict(row)
        if entry['parameters']:
            entry['parameters'] = json.loads(entry['parameters'])
        trail.append(entry)

    conn.close()
    return trail


def format_audit_trail_for_ui(query_id: str) -> List[Dict]:
    """
    Format audit trail for frontend display
    Returns simplified, human-readable entries
    """
    trail = get_audit_trail(query_id)
    formatted = []

    for entry in trail:
        formatted_entry = {
            "timestamp": entry["timestamp"],
            "step": entry["event_type"].replace("_", " ").title()
        }

        # Add relevant details based on event type
        if entry["event_type"] == "routing":
            formatted_entry["description"] = f"Classified as '{entry['task']}' task"
            if entry["parameters"]:
                params = entry["parameters"]
                formatted_entry["metadata"] = f"{params.get('image_count', 0)} image(s), modalities: {', '.join(params.get('modalities', []))}"

        elif entry["event_type"] == "model_call":
            formatted_entry["description"] = f"Called {entry['model_used']} for {entry['task']}"
            formatted_entry["metadata"] = entry["details"]

        elif entry["event_type"] == "preprocessing":
            formatted_entry["description"] = entry["details"]

        elif entry["event_type"] == "confidence_estimation":
            formatted_entry["description"] = f"Confidence: {entry['parameters'].get('confidence', 0):.2f}"
            formatted_entry["metadata"] = f"Method: {entry['parameters'].get('method', 'unknown')}"

        formatted.append(formatted_entry)

    return formatted
