from dataclasses import asdict, dataclass
from typing import Optional


@dataclass
class SeoIssue:
    code: str
    severity: str
    message: str
    check: str
    url: str
    details: Optional[dict] = None

    def to_dict(self) -> dict:
        data = asdict(self)
        if data.get("details") is None:
            data.pop("details", None)
        return data
