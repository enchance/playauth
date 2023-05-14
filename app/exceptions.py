from typing import Optional, Any, Dict
from fastapi.exceptions import HTTPException






class AppException(HTTPException):
    code = 400
    message = 'FAILED_ATTEMPT'
    
    def __init__(self, status_code: int = None, detail: Any = None,
                 headers: Optional[Dict[str, Any]] = None):
        status_code = status_code or self.code
        detail = detail or self.message
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class PermissionsException(AppException):
    code = 403
    message = 'YOU_SHALL_NOT_PASS'