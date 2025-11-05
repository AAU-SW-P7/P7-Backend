"""Repository functions for handling File model operations."""

from django.db import transaction, connection
from django.db.models import Value, Q, F
from django.db.models.functions import Coalesce
from django.contrib.postgres.search import SearchVector
from django.http import JsonResponse
from repository.models import File, Service, User
import hashlib
import re

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
        
        # Remove extensions tag from name field
        extension_list = ["pdf", "docx","gdocx", "doc", "txt", "md", "xlsx", "xls", "pptx", "ppt", "csv", "rtf", "odt"]
        for ext in extension_list:
            if file.name.lower().endswith('.' + ext):
                name = file.name[:-(len(ext) + 1)]
                file.extension = '.' + ext
                file.save(update_fields=["extension"])
                break
                
        update_tsvector(file, name, None)

    return file

def get_raw_tsvector(text: str, config: str = "simple", weight: str | None = None):
    """
    Return PostgreSQL's weighted tsvector (with A/B weights).
    If no weight is provided, returns a normal tsvector.
    """
    if not text:
        return ""
    with connection.cursor() as cursor:
        if weight:
            cursor.execute(
                "SELECT setweight(to_tsvector(%s, %s), %s)", [config, text, weight]
            )
        else:
            cursor.execute("SELECT to_tsvector(%s, %s)", [config, text])
        result = cursor.fetchone()
    return result[0] if result else ""

def update_tsvector(file, name: str, content: str | None):
    """Generate a tsvector from name + content and store salted-hashed tokens."""
    user = file.serviceId.userId
    salt = user.salt

    # 1️⃣ Generate both vectors normally via PostgreSQL
    raw_name_vec = get_raw_tsvector(name, "simple", "A")
    raw_content_vec = get_raw_tsvector(content or "", "english", "B")

    # 2️⃣ Hash tokens in both, preserving weights/positions
    hashed_name_vec = hash_tsvector(raw_name_vec, salt)
    hashed_content_vec = hash_tsvector(raw_content_vec, salt)

    # 3️⃣ Combine vectors — both remain valid TSVECTOR syntax
    combined_tsvector = f"{hashed_name_vec} {hashed_content_vec}".strip()

    # 4️⃣ Update DB directly using tsvector literal
    with connection.cursor() as cursor:
        cursor.execute(
            'UPDATE "file" SET ts = %s::tsvector WHERE id = %s',
            [combined_tsvector, file.id],
        )

    file.refresh_from_db(fields=["ts"])


def tokenize_and_hash_with_salt(name: str, salt: str):
    """Tokenize, alphabetize, and hash each token with the given user salt."""
    tokens = re.findall(r'\w+', name.lower())
    tokens.sort()

    hashed_tokens = [
        hashlib.sha256((salt + token).encode('utf-8')).hexdigest()
        for token in tokens
    ]
    return hashed_tokens

def hash_tsvector(tsvector_str: str, salt: str):
    """
    Replace lexemes in a tsvector string with salted hashes,
    preserving position and weight data (like :3A,21A).
    """
    if not tsvector_str:
        return ""

    pattern = r"'([^']+)'(:[0-9A,]+)"
    hashed_entries = []

    for match in re.finditer(pattern, tsvector_str):
        token = match.group(1)
        positions = match.group(2)
        hashed_token = hashlib.sha256((salt + token).encode("utf-8")).hexdigest()
        hashed_entries.append(f"'{hashed_token}'{positions}")

    return " ".join(hashed_entries)

def query_files_by_name(name_query, user_id):
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

    assert isinstance(name_query, (list, tuple)), "name_query must be a list or tuple of tokens"

    # Q() object to combine queries
    q = Q()
    for token in name_query:
        q |= Q(name__icontains=token)
    if not q.children:
        return File.objects.none()
    q &= Q(serviceId__userId=user_id)

    query_text = " ".join(name_query)
    results = File.objects.ranking_based_on_file_name(query_text, base_filter=q)
    for f in results:
        print(f.rank, f.name)
    return results

def get_files_by_service(service):
    """Retrieves all files associated with a given service.
    
    params:
        service: The service object for which to retrieve files.
    
    returns:
        A list of File objects associated with the service.
    """
    if isinstance(service, Service):
        return list(File.objects.filter(serviceId=service.id))
    return JsonResponse({"error": "Invalid service parameter"}, status=400)