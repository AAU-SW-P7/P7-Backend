"""" Manager for ranking files based on query matches. """

from django.db import models
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import F, Value, FloatField


class FileQuerySet(models.QuerySet):
    """Custom QuerySet for File model with ranking capabilities."""
    def ranking_based_on_file_name(self, query_text: str, base_filter: models.Q | None = None):
        """
        Apply ranking favoring phrase matches, and token coverage.
        - query_text: the original user query ("file name with spaces")
        - base_filter: optional Q object with prefilter logic
        """
        tokens = query_text.split()
        token_count = len(tokens)
        
        # Search vector on the ts vector
        query_text_search_vector = F("ts")

        # Search type plain favors individual token matches
        plain_q = SearchQuery(query_text, search_type="plain", config="simple")

        # Apply base filter if provided
        query_set = self
        if base_filter is not None:
            query_set = query_set.filter(base_filter)

        # Annotate how many tokens appear in the name
        token_match_expr = sum(
            models.Case(
                models.When(ts__icontains=t, then=Value(1)),
                default=Value(0),
                output_field=models.IntegerField(),
            )
            for t in tokens
        )

        # Final ranking combines:
        #    1) Phrase rank (heavier weight)
        #    2) Plain rank
        #    3) Token coverage ratio
        #    4) Exact phrase match bonus (inversely proportional to name length)
        #    5) Normalized by name length to favor shorter names
        return (
            query_set
            .annotate(
                plain_rank=SearchRank(query_text_search_vector, plain_q, normalization=2),
                matched_tokens=token_match_expr,
            )
            .annotate(
                token_ratio=(F("matched_tokens") / Value(token_count, output_field=FloatField())),
                token_penalty= 1.0 - F("token_ratio"),
            )
            .annotate(
                ordered_bonus=models.Case(
                    models.When(name__icontains=query_text, then=Value(1.0)),
                    default=Value(0.0),
                    output_field=FloatField(),
                ),
            )
            .annotate(
                rank=(
                    # heavier weight for phrase matches
                    F("plain_rank") * F("token_penalty")
                    + F("token_ratio")   # moderate boost for token coverage
                    + F('ordered_bonus') # large boost for exact ordered phrase
                )
            )
            .filter(rank__gt=0.0)
            .order_by("-rank")
        )

class FileManager(models.Manager.from_queryset(FileQuerySet)):
    """ Custom manager for File model using FileQuerySet. """
