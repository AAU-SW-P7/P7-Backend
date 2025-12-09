import os
from pathlib import Path
from django.conf import settings
from datetime import datetime, timezone

from p7.helpers import smart_extension
from repository.file import save_file



def update_or_create_local_file(file: dict, service):
    """
    Create or update a local-file record in the same structure used
    by Dropbox/Google.
    """
    full_path = Path(file["path_display"])
    stat = full_path.stat()

    # determine extension like Dropbox version
    extension = smart_extension("local", file["name"], file.get("mime_type"))

    # local files are always downloadable
    downloadable = True

    created_at = datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc)
    modified_at = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)

    # "link" = the local path (or a file:// URL if needed)
    link = str(full_path)

    save_file(
        service_id=service,
        service_file_id=file["id"],
        name=file["name"],
        extension=extension,
        downloadable=downloadable,
        path=str(full_path),
        link=link,
        size=stat.st_size,
        created_at=created_at,
        modified_at=modified_at,
        indexed_at=None,
        snippet=None,
    )


def fetch_recursive_local_files(user_id=None) -> list[dict]:
    """
    Returns a list of file metadata objects for files in app/data,
    shaped similarly to Dropbox's JSON entries.
    """
    root = Path(settings.BASE_DIR) / "data"
    print(root)
    files = []
    if not root.exists():
        return files
    print(f"Scanning local files in: {root}")
    for base, dirs, filenames in os.walk(root):
        for filename in filenames:
            full_path = Path(base) / filename
            stat = full_path.stat()
            extension = smart_extension("local", filename, None)
            created_dt = datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc)
            modified_dt = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
  
            files.append({
                ".tag": "file",
                "id": str(full_path),
                "name": filename,
                "path_display": str(full_path),
                "path_lower": str(full_path).lower(),
                "extension": extension,
                "size": stat.st_size,

                # Dropbox-like fields
                "is_downloadable": True,
                "client_modified": created_dt.isoformat(),
                "server_modified": modified_dt.isoformat(),

                # Simpler local-friendly fields
                "createdAt": created_dt.isoformat(),
                "modifiedAt": modified_dt.isoformat(),
                "downloadable": True,
            })
    return files
