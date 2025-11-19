"""" Manager for ranking files based on query matches. """

from django.db import models
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import F, Value, FloatField, Q


class FileQuerySet(models.QuerySet):
    """Custom QuerySet for File model with ranking capabilities."""
    def ranking_based_on_file_name(self, query_text: str, base_filter: models.Q | None = None):
        """
        Apply ranking favoring phrase matches, and token coverage.
        - query_text: the original user query ("file name with spaces")
        - base_filter: optional Q object with prefilter logic
        """
        # Search vector on the ts vector
        query_text_search_vector = F("tsFilename")

        # Search type plain favors individual token matches
        plain_q = SearchQuery(query_text, search_type="plain", config="simple")

        # Apply base filter if provided
        query_set = self
        if base_filter is not None:
            query_set = query_set.filter(base_filter)

        tokens = query_text.split()
        token_count = len(tokens)
        
        # Filter to only files that match at least one token
        q = Q()
        for t in tokens:
            q |= Q(name__icontains=t)
        query_set = query_set.filter(q)

        # Annotate how many tokens appear in the name
        token_match_expr = sum(
            models.Case(
                models.When(tsFilename__icontains=t, then=Value(1)),
                default=Value(0),
                output_field=models.IntegerField(),
            )
            for t in tokens
        )

        # Adds Final ranking composed of below and orders by it:
        #    1) Plain rank with normalization 16 
        #       https://www.postgresql.org/docs/current/textsearch-controls.html#TEXTSEARCH-RANKING
        #    2) Query Token coverage ratio (0.0 to 1.0)
        #    3) ordered bonus for phrase matches (0.5 bonus)
        return (
            query_set
            .annotate(
                plain_rank=SearchRank(query_text_search_vector, plain_q, normalization=16),
                matched_tokens=token_match_expr,
                token_ratio=(F("matched_tokens") / Value(token_count, output_field=FloatField())),
                ordered_bonus=models.Case(
                    models.When(name__icontains=query_text, then=Value(0.5)),
                    default=Value(0.0),
                    output_field=FloatField(),
                ),
                rank=(
                    (F("plain_rank") * (F("token_ratio")))
                    + F("ordered_bonus")
                ),
            )
            .order_by("-rank")
        )

class FileManager(models.Manager.from_queryset(FileQuerySet)):
    """ Custom manager for File model using FileQuerySet. """
