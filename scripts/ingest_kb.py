from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import get_settings
from app.rag.pipeline import RAGAssistant


if __name__ == "__main__":
    assistant = RAGAssistant(get_settings())
    result = assistant.ingest(rebuild=True)
    print(result.model_dump_json(indent=2))
