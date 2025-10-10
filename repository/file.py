from repository.models import File

def save_file(
    sericeId,
    serviceFileId,
    name,
    extension,
    downloadable,
    path,
    link,
    size,
    createdAt,
    modifiedAt,
    lastIndexed,
    snippet,
    content,
):
    File.objects.create(
        serviceId=sericeId,
        serviceFileId=serviceFileId,
        name=name,
        extension=extension,
        downloadable=downloadable,
        path=path,
        link=link,
        size=size,
        createdAt=createdAt,
        modifiedAt=modifiedAt,
        lastIndexed=lastIndexed,
        snippet=snippet,
        content=content,
    )
