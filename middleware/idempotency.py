from functools import wraps
from flask import request, jsonify
import time

_cache = {}  # {key: (response_data, status_code, timestamp)}
_TTL = 300   # 5 minutes


def _cleanup():
    """Remove expired entries (called lazily, not on every request)."""
    now = time.time()
    expired = [k for k, v in _cache.items() if now - v[2] > _TTL]
    for k in expired:
        del _cache[k]


def idempotent(f):
    """Cache response by X-Idempotency-Key header. Same key = same response."""
    @wraps(f)
    def decorated(*args, **kwargs):
        key = request.headers.get("X-Idempotency-Key")
        if not key:
            return f(*args, **kwargs)

        if key in _cache:
            data, status, ts = _cache[key]
            if time.time() - ts < _TTL:
                return jsonify(data), status

        result = f(*args, **kwargs)

        # Handle both (response, status) and plain response returns
        if isinstance(result, tuple):
            resp, status = result
            data = resp.get_json() if hasattr(resp, "get_json") else resp
        else:
            data = result.get_json() if hasattr(result, "get_json") else result
            status = 200

        _cache[key] = (data, status, time.time())

        # Lazy cleanup every 100 entries
        if len(_cache) > 100:
            _cleanup()

        return jsonify(data), status
    return decorated
