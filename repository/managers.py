"""" Manager for ranking files based on query matches. """

import hashlib
import json
from pathlib import Path
import re
from django.db import models
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.db.models import F, Value, FloatField


        
def hash_query_tokens(query: str, salt: str):
    """Tokenize query and hash tokens with the given salt."""
    tokens = re.findall(r'\w+', query.lower())
    hashed = [hashlib.sha256((salt + t).encode('utf-8')).hexdigest() for t in tokens]
    return hashed

class FileQuerySet(models.QuerySet):
    """Custom QuerySet for File model with ranking capabilities."""
    def ranking_based_on_file_name(self, query_text: str, base_filter: models.Q | None = None, user_salt: str = None):
        """
        Apply ranking favoring phrase matches, and token coverage.
        - query_text: the original user query ("file name with spaces")
        - base_filter: optional Q object with prefilter logic
        """


        hashed_tokens = hash_query_tokens(query_text, user_salt)
        token_count = len(hashed_tokens)
        print(f"Ranking query tokens (count={token_count}): {hashed_tokens}")
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
            for t in hashed_tokens
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
                phrase_rank=SearchRank(F("ts"), phrase_q),
                plain_rank=SearchRank(F("ts"), plain_q),
                matched_tokens=token_match_expr,
            )
            .annotate(
                token_ratio=(F("matched_tokens") / Value(token_count, output_field=FloatField())),
                token_penalty= 1.0 - (F("matched_tokens") / Value(token_count, output_field=FloatField())),
                exact_phrase_match=models.Case(
                        models.When(ts__icontains=query_text,
                                    then=Value(1.0)/models.functions.Length("ts")),
                    default=Value(0.0),
                    output_field=FloatField(),
                ),
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
                    + (F("token_ratio") * 1.5)
                    - (F("token_penalty") * (token_count + 3 - F("matched_tokens"))) * 2.5  # small penalty for missing tokens
                    + F('ordered_bonus') * 2  # large boost for exact ordered phrase
                )
                / models.functions.Greatest(models.functions.Length("ts"), Value(1))
            )
            .filter(rank__gt=0.0)
            .order_by("-rank")
        )

class FileManager(models.Manager.from_queryset(FileQuerySet)):
    """ Custom manager for File model using FileQuerySet. """
