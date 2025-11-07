"""" Manager for ranking files based on query matches. """

import json
from pathlib import Path
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

        # Evaluate the expression per row and capture it as text
        debug_rows = list(
            self.annotate(tsv=query_text_search_vector)
                .values("id", "name", "tsv")[:50]   # limit to keep it small
        )

        Path("query_text_search_vector.json").write_text(
            json.dumps(debug_rows, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        # Search type phrase favors exact phrase matches
        # Search type plain favors individual token matches
        phrase_q = SearchQuery(query_text, search_type="phrase", config="simple")
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
                phrase_rank=SearchRank(query_text_search_vector, phrase_q, normalization=2),
                plain_rank=SearchRank(query_text_search_vector, plain_q, normalization=2),
                matched_tokens=token_match_expr,
            )
            .annotate(
                token_ratio=(F("matched_tokens") / Value(token_count, output_field=FloatField())),
                token_penalty=1.0 - F("token_ratio"),
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
                    (F("phrase_rank") + F("plain_rank"))
                    + F("token_ratio") * 1.5
                    - (F("token_penalty") *
                    (token_count + 3 - F("matched_tokens")))  # small penalty for missing tokens
                    + F('ordered_bonus') * 2
                )
            )
            .filter(rank__gte=-10)
            .order_by("-rank")
        )

class FileManager(models.Manager.from_queryset(FileQuerySet)):
    """ Custom manager for File model using FileQuerySet. """
