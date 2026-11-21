import json

REGISTER = "REGISTER"
HEARTBEAT = "HEARTBEAT"
DISCOVER = "DISCOVER"
SERVICE_REQUEST = "SERVICE_REQUEST"
FOUND = "FOUND"
NOT_FOUND = "NOT_FOUND"
OK = "OK"
SERVICE_RESPONSE = "SERVICE_RESPONSE"
ERROR = "ERROR"

def encode(message):
    return json.dumps(message).encode("utf-8")

def decode(data):
    obj = json.loads(data.decode("utf-8"))
    if not isinstance(obj, dict):
        raise ValueError("Message must be a JSON object")
    return obj
