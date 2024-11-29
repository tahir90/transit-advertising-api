from fastapi import HTTPException, status

class TransitAPIException(HTTPException):
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail)

class DriverNotFoundException(TransitAPIException):
    def __init__(self, driver_id: str):
        super().__init__(
            detail=f"Driver with ID {driver_id} not found",
            status_code=status.HTTP_404_NOT_FOUND
        )

class SessionNotFoundException(TransitAPIException):
    def __init__(self, session_id: str):
        super().__init__(
            detail=f"Session with ID {session_id} not found",
            status_code=status.HTTP_404_NOT_FOUND
        )