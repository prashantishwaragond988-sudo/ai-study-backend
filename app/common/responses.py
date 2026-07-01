from flask import jsonify


def success_response(data: dict, status_code: int = 200):
    return jsonify({"ok": True, **data}), status_code
