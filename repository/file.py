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
    """Saves or updates file metadata and content to the database.
    
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
    defaults = {
        "name": name,
        "extension": extension,
        "downloadable": downloadable,
        "path": path,
        "link": link,
        "size": size,
        "createdAt": created_at,
        "modifiedAt": modified_at,
        "lastIndexed": last_indexed,
        "snippet": snippet,
        "content": content,
    }
    File.objects.update_or_create(
        serviceId=service_id,
        serviceFileId=service_file_id,
        defaults=defaults,
    )

def get_files_by_service(service):
    """Retrieves all files associated with a given service.
    
    params:
        service: The service object for which to retrieve files.
    
    returns:
        A list of File objects associated with the service.
    """
    return list(File.objects.filter(serviceId=service.id))