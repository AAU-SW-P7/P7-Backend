from django.db import models
from django.contrib.postgres.search import SearchQuery, SearchRank, TrigramSimilarity, SearchVector
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

        query_text_search_vector = SearchVector("name", config="simple")
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
            query_set
            .annotate(
                search=query_text_search_vector,
                search_rank=SearchRank(query_text_search_vector, phrase_q),
                phrase_rank=SearchRank(query_text_search_vector, phrase_q),
                plain_rank=SearchRank(query_text_search_vector, plain_q),
                trigram_sim=TrigramSimilarity("name", query_text),
                matched_tokens=token_match_expr,
            )
            .annotate(
                token_ratio=(F("matched_tokens") / Value(token_count, output_field=FloatField())),
                exact_phrase_match=models.Case(
                    models.When(name__icontains=query_text, then=Value(1.0)),
                    default=Value(0.0),
                    output_field=FloatField(),
                ),
            )
            .annotate(
                rank=(
                    # heavier weight for phrase matches
                    (F("phrase_rank") * 3.0 + F("plain_rank") * 1.0)
                    + (F("trigram_sim") * 2.0)
                    + (F("search_rank") * 0.2)
                    + (F("token_ratio") * 1.0)
                    + (F("exact_phrase_match") * 4.0)  # large boost for exact ordered phrase
                )
                / models.functions.Greatest(models.functions.Length("name"), Value(1))
            )
            .filter(rank__gt=0.0)
            .order_by("-rank")
        )


class SmartSearchQuery(SearchQuery):
    def as_sql(self, compiler, connection, function=None, template=None):
        if self.search_type == "phrase":
            config_sql = "%s, " % connection.ops.quote_name(self.config) if self.config else ""
            template = f"phraseto_tsquery({config_sql}%s)"
        elif self.search_type == "raw":
            template = "to_tsquery(%s, %s)"  # or other fallback
        else:
            template = f"{self.search_type}to_tsquery(%s, %s)"
        params = [self.config, self.value] if self.config else [self.value]
        return template, params

class FileManager(models.Manager.from_queryset(FileQuerySet)):
    pass
