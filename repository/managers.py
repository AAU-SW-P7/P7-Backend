from django.db import models
from django.contrib.postgres.search import SearchQuery, SearchRank, TrigramSimilarity
from django.db.models import Func, F, Value, FloatField

class FileQuerySet(models.QuerySet):
    def smart_search(self, query_text: str, base_filter: models.Q | None = None):
        """
        Apply ranking favoring phrase matches, trigram similarity, and token coverage.
        - query_text: the original user query ("file name with spaces")
        - base_filter: optional Q object with prefilter logic
        """
        tokens = query_text.split()
        token_count = len(tokens)

        # Search type phrase favors exact phrase matches
        # Search type plain favors individual token matches
        phrase_q = SearchQuery(query_text, search_type="phrase", config="simple")
        plain_q = SearchQuery(query_text, search_type="plain", config="simple")

        query_set = self
        if base_filter is not None:
            query_set = query_set.filter(base_filter)

        # Annotate how many tokens appear in the name
        token_match_expr = sum(
            models.Case(
                models.When(name__icontains=t, then=Value(1)),
                default=Value(0),
                output_field=models.IntegerField(),
            )
            for t in tokens
        )
        
        # Final ranking combines:
        # - Phrase rank (weighted x2)
        # - Plain rank (weighted x1)
        # - Trigram similarity (weighted x0.5)
        # - Token coverage ratio (matched tokens / total tokens)
        return (
            query_set.annotate(
                phrase_rank=SearchRank(models.F("ts"), phrase_q) * 1.5,
                plain_rank=SearchRank(models.F("ts"), plain_q),
                trigram_sim=TrigramSimilarity("name", query_text),
                matched_tokens=token_match_expr,
            )
            .annotate(
                token_ratio=(F("matched_tokens") / Value(token_count, output_field=FloatField())),
            )
            .annotate(
                rank=(
                    models.functions.Greatest(
                        models.F("phrase_rank"), models.F("plain_rank")
                    )
                    * 0.7
                    + models.F("trigram_sim") * 0.3
                )
                / models.functions.Length("name")
            )
            .filter(rank__gt=0.0)
            .order_by("-rank")
        )


class FileManager(models.Manager.from_queryset(FileQuerySet)):
    pass
