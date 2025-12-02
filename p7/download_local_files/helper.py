from pathlib import Path
from django.utils import timezone
from p7.helpers import parse_file_content
from repository.file import fetch_downloadable_files, update_tsvector


def download_recursive_local_files(service):
    """
    Reads local files from app/data and updates tsvector
    exactly the same way as Dropbox would.
    """
    processed = []
    errors = []
    db_files = fetch_downloadable_files(service)
    
    for f in db_files:
        path = Path(f.path)


        if not path.exists():
            errors.append(f"Missing file: {path}")
            continue

        try:
            content = path.read_bytes()
            parsed_text = parse_file_content(content, f)
            if parsed_text:
                update_tsvector(
                    f,
                    parsed_text,
                    timezone.now(),
                )

                processed.append({
                    "id": f.serviceFileId,
                    "parsed": True,
                })
            else:
                processed.append({
                    "id": f.serviceFileId,
                    "parsed": False,
                })
        except Exception as e:
            errors.append(str(e))

    return processed, errors
