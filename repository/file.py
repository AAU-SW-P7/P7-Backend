"""Repository functions for handling File model operations."""
from repository.models import File

def save_file(
    service_id,
    service_file_id,
    name,
    extension,
    downloadable,
    path,
    link,
    size,
    created_at,
    modified_at,
    last_indexed,
    snippet,
    content,
):
    """Saves or updates a file record in the database."""
    File.objects.update_or_create(
        serviceId=service_id,
        serviceFileId=service_file_id,
        name=name,
        extension=extension,
        downloadable=downloadable,
        path=path,
        link=link,
        size=size,
        createdAt=created_at,
        modifiedAt=modified_at,
        lastIndexed=last_indexed,
        snippet=snippet,
        content=content,
    )
