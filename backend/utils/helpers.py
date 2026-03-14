from datetime import datetime

def format_timestamp(dt: datetime = None) -> str:
    """Return ISO format timestamp with Z suffix"""
    if dt is None:
        dt = datetime.utcnow()
    return dt.isoformat() + "Z"