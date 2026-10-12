import dataclasses
from typing import Any

@dataclasses.dataclass
class DictResult:
    message: str
    statusCode: int
    type: str
    context: Any
    data: Any

    @classmethod
    def success_response(cls, message, status_code, types, data, context=None):
        return cls(
            message=message,
            statusCode=status_code,
            type=types,
            context=context,
            data=data
        )

    @classmethod
    def error_response(cls, message, status_code, types, data):
        return cls(
            message=message,
            statusCode=status_code,
            type=types,
            context=None,
            data=data
        )

    def to_dict(self):
        return {
            "message": self.message,
            "statusCode": self.statusCode,
            "type": self.type,
            "context": self.context,
            "data": self.data
        }

