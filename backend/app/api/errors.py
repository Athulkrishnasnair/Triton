class APIError(Exception):
    def __init__(self, message, status_code=400, code="invalid_request"):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code


def error_payload(message, code):
    return {"error": {"code": code, "message": message}}
