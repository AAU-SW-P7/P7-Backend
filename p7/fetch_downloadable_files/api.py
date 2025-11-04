"""API endpoint to fetch downloadable files for a given service."""
from typing import List

from ninja import Router, Header
from p7.helpers import downloadable_file_extensions
from repository.models import File

fetch_downloadable_files_router = Router()
@fetch_downloadable_files_router.get("/")
def fetch_downloadable_files(service) -> List:
    """
    Return list of File entries for the given user and service.
    """
    
    return list(
        File.objects.filter(
            serviceId=service,
            extension__in=downloadable_file_extensions(),
            downloadable=1,
        )
    )