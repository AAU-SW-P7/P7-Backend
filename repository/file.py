"""Saves file metadata and content to the database."""

from django.db import transaction
from django.db.models import Value, Q
from django.db.models.functions import Coalesce
from django.contrib.postgres.search import SearchVector
from repository.models import File, User


def save_file(
    service_id,  # may be an int (Service.pk) or a Service instance
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
    *,
    ts_config='simple'  # allow overriding the FTS config if needed
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

    with transaction.atomic():
        # Insert the file
        file = File.objects.create(
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

        # 2) Compute & store the tsvector (use Coalesce to avoid NULLs)
        File.objects.filter(pk=file.pk).update(
            ts=(
                SearchVector(Coalesce("name", Value("")), weight="A", config=ts_config)
                + SearchVector(
                    Coalesce("content", Value("")), weight="B", config=ts_config
                )
            )
        )

        # 3) Load the computed ts on the instance
        file.refresh_from_db(fields=["ts"])

    return file

def query_files_by_name(name_query, user_id):
    """Query for files by name containing any of the given tokens and user id.

    params:
        name_query: List or tuple of substrings to search for in file names.
        user_id: User id to restrict results to. (applies as an AND).
    returns:
        QuerySet of File objects matching the search criteria.
    """
    user = User.objects.get(pk=user_id)  # Ensure user exists

    assert isinstance(name_query, (list, tuple)), "name_query must be a list or tuple of tokens"
    assert user is not None, "User with given user_id does not exist"

    # Q() object to combine queries
    q = Q()
    for token in name_query:
        q |= Q(name__icontains=token)
    if not q.children:
        return File.objects.none()
    q &= Q(serviceId__userId=user_id)

    query_text = " ".join(name_query)
    results = File.objects.ranking_based_on_file_name(query_text, base_filter=q)

    return results
