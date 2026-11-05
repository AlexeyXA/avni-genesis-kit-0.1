"""Deterministic example agent. Replace this with your own run(payload)."""

def run(payload):
    text = payload.get("text", "")
    return {"answer": f"HELLO: {str(text).strip()}"}
