"""Saves file metadata and content to the database."""
from repository.models import File
from django.db.models import Q

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
    """Saves file metadata and content to the database.
    
    params:
        sericeId: ID of the service the file belongs to.
        serviceFileId: ID of the file in the external service.
        name: Name of the file.
        extension: File extension.
        downloadable: Boolean indicating if the file is downloadable.
        path: Path of the file in the service.
        link: URL link to the file.
        size: Size of the file in bytes.
        createdAt: Timestamp when the file was created.
        modifiedAt: Timestamp when the file was last modified.
        lastIndexed: Timestamp when the file was last indexed.
        snippet: Text snippet or preview of the file content.
        content: Full text content of the file.
        """
    File.objects.create(
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
    
def search_files_by_name(name_query, user_id):
    """Searches for files by name containing the given query string and user id.

    params:
        name_query: Substring or list/tuple of substrings to search for in file names.
                    If a list/tuple is provided, tokens are combined with OR.
        user_id: User id to restrict results to. (applies as an AND).
    returns:
        QuerySet of File objects matching the search criteria.
    """
    if isinstance(name_query, (list, tuple)):
        q = Q()
        for token in name_query:
            q |= Q(name__icontains=token)
        if not q.children:
            return File.objects.none()
        if user_id is not None:
            q &= Q(serviceId__userId=user_id)
        return File.objects.filter(q)

    # Single string
    q = Q(name__icontains=name_query)
    if user_id is not None:
        q &= Q(serviceId__userId=user_id)
    return File.objects.filter(q)
