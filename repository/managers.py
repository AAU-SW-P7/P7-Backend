""" " Manager for ranking files based on query matches."""

from django.db import models
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import F, Value, FloatField
from repository.helpers import ts_tokenize, get_document_frequencies_matching_tokens, get_term_frequencies_for_file
from p7.search_files_by_filename.content_ranking import get_document_lnc, get_query_ltc, compute_score_for_files


class FileQuerySet(models.QuerySet):
    """Custom QuerySet for File model with ranking capabilities."""

    def ranking_based_on_file_name(
        self, query_text: str, base_filter: models.Q | None = None
    ):
        """
        Apply ranking favoring phrase matches, and token coverage.
        - query_text: the original user query ("file name with spaces")
        - base_filter: optional Q object with prefilter logic
        """

        tokens = query_text.split()
        token_count = len(tokens)

        # Search vector on the ts vector
        query_text_search_vector = F("tsFilename")

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
                models.When(tsFilename__icontains=t, then=Value(1)),
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
            query_set.annotate(
                phrase_rank=SearchRank(
                    query_text_search_vector, phrase_q, normalization=2
                ),
                plain_rank=SearchRank(
                    query_text_search_vector, plain_q, normalization=2
                ),
                matched_tokens=token_match_expr,
            )
            .annotate(
                token_ratio=(
                    F("matched_tokens") / Value(token_count, output_field=FloatField())
                ),
                token_penalty=1.0 - F("token_ratio"),
            )
            .annotate(
                ordered_bonus=models.Case(
                    models.When(name__icontains=query_text, then=Value(1.0)),
                    default=Value(0.0),
                    output_field=FloatField(),
                ),
            )
            # STEP 1: compute raw rank first
            .annotate(
                raw_rank=(
                    (F("phrase_rank") + F("plain_rank"))
                    + F("token_ratio") * 1.5
                    - (F("token_penalty") * (token_count + 3 - F("matched_tokens")))
                    + F("ordered_bonus") * 2
                )
            )
            # STEP 2: clamp negatives to 0
            .annotate(
                rank=models.Case(
                    models.When(raw_rank__lt=0, then=Value(0.0)),
                    default=F("raw_rank"),
                    output_field=FloatField(),
                )
            )
            .filter(rank__gte=0)
            .order_by("-rank")
        )

    def ranking_based_on_content(
        self, query_text: str, base_filter: models.Q | None = None
    ):
        """
        Apply ranking to file content accodring to tf-idf
        - query_text: the original user query ("file name with spaces")
        - base_filter: optional Q object with prefilter logic
        """

        # Retrieve tokens from query string
        # The function also stems them
        tokens = ts_tokenize(query_text, "english")

        # Apply base filter if provided
        query_set = self
        if base_filter is not None:
            query_set = query_set.filter(base_filter)

        # Get totalt number of documents for user
        # Important to do here before query_set is reduced
        user_documents = len(list(query_set))
        document_frequencies = get_document_frequencies_matching_tokens(
            query_set, tokens
        )

        # Create a SearchQuery from tokens to use GIN index
        # Combine tokens with AND logic for binary search
        if not tokens:
            return query_set.none()

        # Build SearchQuery by combining tokens with & operator
        search_query = SearchQuery(tokens[0], config="english")
        for token in tokens[1:]:
            search_query = search_query | SearchQuery(token, config="english")

        # Use the GIN index with binary search (@@)
        query_set = query_set.filter(tsContent=search_query)
        query_ltc = get_query_ltc(user_documents, tokens, document_frequencies)

        # Calculate document lnc
        files = list(query_set)
        file_stats = []
        for file in files:
            term_frequencies = get_term_frequencies_for_file(
                query_set, file.id
            )
            stats = get_document_lnc(term_frequencies)
            file_stats.append({file.id: stats})

        scored_files = compute_score_for_files(query_ltc, file_stats)

        rank_case = models.Case(
            *[
                models.When(pk=file_id, then=Value(score))
                for file_id, score in scored_files.items()
            ],
            default=Value(0.0),
            output_field=FloatField(),
        )

        return (
            query_set.filter(pk__in=scored_files.keys())
            .annotate(content_rank=rank_case)
            .order_by("-content_rank")
        )

class FileManager(models.Manager.from_queryset(FileQuerySet)):
    """Custom manager for File model using FileQuerySet."""
