from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Vacancy:
    title: str
    company: str = ""
    url: str = ""
    source: str = ""
    description: str = ""
    employment_type: str = ""
    remote: bool = True
    salary: str = ""
    location: str = ""
    posted: str = ""
    category: str = ""
    score: float = 0.0
    tags: list[str] = field(default_factory=list)
