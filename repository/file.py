"""Repository functions for handling File model operations."""

import time
from datetime import datetime
from collections import defaultdict
from typing import Iterable
from django.db import transaction
from django.db.models import (
    Value,
    Q,
    F,
)
from django.contrib.postgres.search import SearchVector
from django.http import JsonResponse
from repository.helpers import sanitize_for_postgres
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
                Q(modifiedAt__gt=F("indexedAt")) | Q(indexedAt__isnull=True),
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

        update_tsvector_filename(file, indexed_at)

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


def update_tsvector_content(file, content: str | None, indexed_at: datetime | None) -> None:
    """Update the tsContent field for full-text search on the given file instance."""
    if not content:
        cleaned_content = ""
    else:
        # hard cap at 20M chars
        content = content[:20_000_000]
        cleaned_content = sanitize_for_postgres(content)
        cleaned_content = cleaned_content.encode("utf-8", "ignore").decode("utf-8", "ignore")

    File.objects.filter(pk=file.pk).update(
        indexedAt=indexed_at,
        tsContent=(
            SearchVector(
                Value(cleaned_content),
                weight="B",
                config="english"
            )
        )
    )

    file.refresh_from_db(fields=["tsContent"])

def update_tsvector_filename(file, indexed_at: datetime | None) -> None:
    """Update the tsFilename field for full-text search on the given file instance."""
    File.objects.filter(pk=file.pk).update(
        indexedAt=indexed_at,
        tsFilename=(
            SearchVector(
                Value(remove_extension_from_ts_vector_smart(file)),
                weight="A",
                config="simple",
            )
        )
    )

    file.refresh_from_db(fields=["tsFilename"])


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
        QuerySet of File objects matching the search criteria.
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

    start_query_building = time.perf_counter()
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
    end_query_building = time.perf_counter()
    print(f"Query building took {end_query_building - start_query_building:.6f} seconds")

    query_text = " ".join(name_query)

    # Rank files based on file name
    start_name_ranking = time.perf_counter()
    name_ranked_files = File.objects.ranking_based_on_file_name(
        query_text, base_filter=q
    )
    end_name_ranking = time.perf_counter()
    print(f"Name ranking took {end_name_ranking - start_name_ranking:.6f} seconds")
    

    # Rank files based on file content
    start_content_ranking = time.perf_counter()
    content_ranked_files = File.objects.ranking_based_on_content(
        query_text, base_filter=q
    )
    end_content_ranking = time.perf_counter()
    print(f"Content ranking took {end_content_ranking - start_content_ranking:.6f} seconds")
    
    res = combine_rankings(name_ranked_files, content_ranked_files)[:200]
    
    print(f"Matching files - Filename: {name_ranked_files.count()}")
    print(f"Matching files - Filecontent: {content_ranked_files.count()}")

    return res


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

    start_combining = time.perf_counter()
    accumulate_file_scores(name_ranked_files, NAME_RANK_WEIGHT, scores, files_by_id)
    accumulate_file_scores(
        content_ranked_files, CONTENT_RANK_WEIGHT, scores, files_by_id
    )
    end_combining = time.perf_counter()
    print(f"Combining rankings took {end_combining - start_combining:.6f} seconds")

    # Sort ids by score descending
    start_ordering = time.perf_counter()
    ordered_ids = sorted(scores, key=scores.get, reverse=True)
    end_ordering = time.perf_counter()
    print(f"Ordering took {end_ordering - start_ordering:.6f} seconds")

    start_result_assembly = time.perf_counter()
    result = []
    for file_id in ordered_ids:
        file = files_by_id[file_id]
        file.combined_rank = scores[
            file_id
        ]  # Score is attached, if we want to log it in front end
        result.append(file)
    end_result_assembly = time.perf_counter()
    print(f"Result assembly took {end_result_assembly - start_result_assembly:.6f} seconds")
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
