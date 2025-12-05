"""Repository functions for handling File model operations."""

from datetime import datetime, timezone
from collections import defaultdict
from typing import Iterable
from django.db import transaction
from django.db.models import (
    Value,
    Q,
    F,
)  # , F # enable F when re-enabling modifiedAt__gt=F("indexedAt")
from django.contrib.postgres.search import SearchVector
from django.http import JsonResponse
from repository.models import File, Service, User
from p7.helpers import downloadable_file_extensions, smart_extension

NAME_RANK_WEIGHT = 0.7
CONTENT_RANK_WEIGHT = 0.3


def fetch_downloadable_files(service):
    """Fetches all downloadable files for a given service.

    params:
        service: The service object for which to fetch downloadable files.
    returns:
        A list of downloadable File objects associated with the service.
    """
    if isinstance(service, Service):
        return list(
            File.objects.filter(
                Q(indexedAt__isnull=True) | Q(modifiedAt__gt=F('indexedAt')), # re-enable when debugging/coding is done
                serviceId=service,
                extension__in=downloadable_file_extensions(),
                downloadable=True,
            )
        )

    return JsonResponse({"error": "Invalid service parameter"}, status=400)


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
    indexed_at,
    snippet,
):
    """Saves or updates file metadata and content to the database.

    params:
        service_id: ID of the service the file belongs to.
        serviceFileId: ID of the file in the external service.
        name: Name of the file.
        extension: File extension.
        downloadable: Boolean indicating if the file is downloadable.
        path: Path of the file in the service.
        link: URL link to the file.
        size: Size of the file in bytes.
        createdAt: Timestamp when the file was created.
        modifiedAt: Timestamp when the file was last modified.
        indexedAt: Timestamp when the file was last indexed.
        snippet: Text snippet or preview of the file content.
    """

    with transaction.atomic():
        # Insert the file
        defaults = {
            "name": name,
            "extension": extension,
            "downloadable": downloadable,
            "path": path,
            "link": link,
            "size": size,
            "createdAt": created_at,
            "modifiedAt": modified_at,
            "indexedAt": indexed_at,
            "snippet": snippet,
        }
        file, _ = File.objects.update_or_create(
            serviceId=service_id,
            serviceFileId=service_file_id,
            defaults=defaults,
        )

        update_tsvector(file, None, indexed_at)

    return file


def remove_extension_from_ts_vector_smart(file: File) -> str:
    """Removes the file extension from the file name for tsvector indexing.

    params:
        file: File instance whose name is to be processed.
    returns:
        The file name without its extension.
    """
    extension = smart_extension(file.serviceId.name, file.name)
    if extension and file.name.lower().endswith(extension.lower()):
        return file.name[: -len(extension)]
    return file.name


def update_tsvector(file, content: str | None, indexed_at: datetime | None) -> None:
    """Update the tsvector field for full-text search on the given file instance."""

    File.objects.filter(pk=file.pk).update(
        indexedAt=indexed_at,
        tsFilename=(
            SearchVector(
                Value(remove_extension_from_ts_vector_smart(file)),
                weight="A",
                config="simple",
            )
        ),
        tsContent=(SearchVector(Value(content or ""), weight="B", config="english")),
    )

    file.refresh_from_db(fields=["tsFilename", "tsContent"])


def query_files(
    name_query,
    user_id,
    provider=None,
    modified_after_date=None,
    modified_before_date=None,
    extension=None,
):
    """Query for files by name containing any of the given tokens and user id.

    params:
        name_query: List or tuple of substrings to search for in file names.
        user_id: User id to restrict results to. (applies as an AND).
    returns:
        QuerySet of Top 200 File objects matching the search criteria.
    """
    try:
        User.objects.get(pk=user_id)  # Ensure user exists
    except User.DoesNotExist:
        return JsonResponse(
            {"error": f"Service ({user_id}) not found for user"}, status=404
        )

    assert isinstance(
        name_query, (list, tuple)
    ), "name_query must be a list or tuple of tokens"

    # Q() object to combine queries
    q = Q()
    if provider:
        for p in provider:
            q &= Q(serviceId__name__iexact=p)
    if modified_after_date:
        q &= Q(modifiedAt__gte=modified_after_date)
    if modified_before_date:
        q &= Q(modifiedAt__lte=modified_before_date)
    if extension:
        for ext in extension:
            q &= Q(extension__iexact=ext)
    # Always filter by user_id
    q &= Q(serviceId__userId=user_id)

    query_text = " ".join(name_query)

    # Rank files based on file name
    name_ranked_files = File.objects.ranking_based_on_file_name(
        query_text, base_filter=q
    )

    # Rank files based on file content
    content_ranked_files = File.objects.ranking_based_on_content(
        query_text, base_filter=q
    )

    return combine_rankings(name_ranked_files, content_ranked_files)[:200]


def combine_rankings(
    name_ranked_files: Iterable[File],
    content_ranked_files: Iterable[File],
) -> list[File]:
    """
    Merge name and content ranking results into a single ordered list.

    Params:
        name_ranked_files: 
             Iterable of File objects (with appended rank) ranked by name.
        content_ranked_files: 
             Iterable of File objects (with appended rank) ranked by content (tf-idf).

    Returns:
        List of File objects sorted by their combined weighted rank.
    """
    scores = defaultdict(float)
    files_by_id = {}

    accumulate_file_scores(name_ranked_files, NAME_RANK_WEIGHT, scores, files_by_id)
    accumulate_file_scores(
        content_ranked_files, CONTENT_RANK_WEIGHT, scores, files_by_id
    )

    # Sort ids by score descending
    ordered_ids = sorted(scores, key=scores.get, reverse=True)

    result = []
    for file_id in ordered_ids:
        file = files_by_id[file_id]
        file.combined_rank = scores[
            file_id
        ]  # Score is attached, if we want to log it in front end
        result.append(file)

    return result


def accumulate_file_scores(
    files: Iterable[File], weight: float, scores: defaultdict, files_by_id: dict
) -> None:
    """
    Accumulate weighted rank scores for a set of files

    Params:
        files: Iterable of File objects that expose id and optional rank.
        weight: Weight multiplier to apply to each files rank
        scores: Dict tracking cumulative scores keyed by file id.
        files_by_id: Dict caching file objects keyed by id for later retrieval.
    """
    for f in files:
        rank = getattr(f, "rank", 0.0) or 0.0
        if not rank:
            continue  # skip if rank is 0
        scores[f.id] += rank * weight
        # only store file once
        if f.id not in files_by_id:
            files_by_id[f.id] = f


def get_files_by_service(service):
    """
    Retrieves all files associated with a given service.

    params:
        service: The service object for which to retrieve files.

    returns:
        A list of File objects associated with the service.
    """
    if isinstance(service, Service):
        return list(File.objects.filter(serviceId=service.id))
    return JsonResponse({"error": "Invalid service parameter"}, status=400)
