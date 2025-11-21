""" " Manager for ranking files based on query matches."""

from django.db import models
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import F, Value, FloatField, Q
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
                plain_rank=SearchRank(query_text_search_vector, plain_q, normalization = 16),
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

    def ranking_based_on_content(
        self, query_text: str, base_filter: models.Q | None = None
    ):
        """
        Apply ranking to file content using Term Frequency-Inverse Document Frequency (tf-idf)
        The following notation is used:(Term frequency)-(Document frequency)-(Normalization)
        For the query we use logarithm-idf-cosine (ltc)
        For the files we use logarithm-none-cosine (lnc)
        - query_text: the original user query ("file name with spaces")
        - base_filter: always contains user filter (id) and possibly others
        """

        # Retrieve tokens from query string (stemmed)
        tokens = ts_tokenize(query_text, "english")
        query_set = self

        # No tokens, we cannot query anything
        if not tokens:
            return query_set.none()
        
        # Apply base filter (always includes user)
        all_user_files = query_set.filter(base_filter)

        # Get totalt number of documents for user
        # Important to do here before query_set is reduced
        user_documents_count = len(list(all_user_files))
        
        # Compute document frequencies for all terms included in the query over all user files
        document_frequencies = get_document_frequencies_matching_tokens(
            query_set, tokens
        )

        # Build SearchQuery by combining tokens with | operator
        search_query = SearchQuery(
            " | ".join(tokens), search_type="raw", config="english"
        )

        # Use the GIN index to find files matching query
        user_files_matching_query = list(query_set.filter(tsContent=search_query))
        
        # Compute ltc stats for the query
        query_ltc = get_query_ltc(user_documents_count, tokens, document_frequencies)

        # Calculate document lnc for each file
        file_stats_list = [
            {
                file.id: get_document_lnc(
                    get_term_frequencies_for_file(query_set, file.id)
                )
            }
            for file in user_files_matching_query
        ]

        # Compute a score for each file
        scored_files = compute_score_for_files(query_ltc, file_stats_list)

        # Add rank attribute to the files
        for file in user_files_matching_query:
            file.rank = scored_files.get(file.id, 0.0)
        
        return user_files_matching_query
    
class FileManager(models.Manager.from_queryset(FileQuerySet)):
    """Custom manager for File model using FileQuerySet."""
