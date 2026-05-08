from abc import ABC, abstractmethod
from src.models import ExtractedField, ReviewResult


class OcrAdapter(ABC):
    @abstractmethod
    def extract_fields(self, file_bytes: bytes, material_type: str, file_name: str) -> list[ExtractedField]:
        ...


class ReviewAdapter(ABC):
    @abstractmethod
    def review(
        self,
        task_id: str,
        session_id: str,
        extracted_fields: list[ExtractedField],
        material_types: list[str],
        missing_materials: list[str],
        knowledge_fragments: list,
    ) -> ReviewResult:
        ...
