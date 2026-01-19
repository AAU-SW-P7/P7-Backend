"""Manager for ranking files based on query matches."""

import time
from django.db import models
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import F, Value, FloatField
from repository.helpers import (
    ts_tokenize,
    get_document_frequencies_matching_tokens,
    get_term_frequencies_for_file,
    parse_tsvector,
)
from p7.search.content_ranking import (
    get_document_lnc,
    get_query_ltc,
    compute_score_for_files,
)


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
        start_text_search_vector = time.perf_counter()
        # Search vector on the ts vector
        query_text_search_vector = F("tsFilename")
        end_text_search_vector = time.perf_counter()
        print(f"Time to get ts vector field: {end_text_search_vector - start_text_search_vector:.6f} seconds")

        start_plain_query = time.perf_counter()
        # Search type plain favors individual token matches
        plain_q = SearchQuery(query_text, search_type="plain", config="simple")
        end_plain_query = time.perf_counter()
        print(f"Time to create plain SearchQuery: {end_plain_query - start_plain_query:.6f} seconds")

        start_query_set = time.perf_counter()
        # Apply base filter if provided
        query_set = self
        if base_filter is not None:
            query_set = query_set.filter(base_filter)
        end_query_set = time.perf_counter()
        print(f"Time to apply base filter: {end_query_set - start_query_set:.6f} seconds")

        start_tokens = time.perf_counter()
        tokens = [t for t in (query_text or "").split() if t]
        if not tokens:
            # No tokens -> nothing to search
            return self.none()
        end_tokens = time.perf_counter()
        print(f"Time to tokenize query: {end_tokens - start_tokens:.6f} seconds")

        start_search_query = time.perf_counter()
        search_query = SearchQuery(
            " | ".join(tokens), search_type="raw", config="simple"
        )
        end_search_query = time.perf_counter()
        print(f"Time to create raw SearchQuery: {end_search_query - start_search_query:.6f} seconds")
        
        start_query_set_filter = time.perf_counter()
        query_set = query_set.filter(tsFilename=search_query)
        end_query_set_filter = time.perf_counter()
        print(f"Time to filter query set with search query: {end_query_set_filter - start_query_set_filter:.6f} seconds")

        start_token_match_expr = time.perf_counter()
        token_match_expr = sum(
            models.Case(
                models.When(tsFilename=SearchQuery(t, search_type="plain", config="simple"),
                     then=models.Value(1)),
                default=models.Value(0),
                output_field=models.IntegerField(),
            )
            for t in tokens
        )
        end_token_match_expr = time.perf_counter()
        print(f"Time to create token match expression: {end_token_match_expr - start_token_match_expr:.6f} seconds")

        # Adds Final ranking composed of below and orders by it:
        #    1) Plain rank with normalization 16
        #       https://www.postgresql.org/docs/current/textsearch-controls.html#TEXTSEARCH-RANKING
        #    2) Query Token coverage ratio (0.0 to 1.0)
        #    3) ordered bonus for phrase matches (0.5 bonus)
        
        start_query_set_annotate = time.perf_counter()
        res = query_set.annotate(
            plain_rank=SearchRank(query_text_search_vector, plain_q, normalization=16),
            matched_tokens=token_match_expr,
            token_ratio=(
                F("matched_tokens") / Value(len(tokens), output_field=FloatField())
            ),
            ordered_bonus=models.Case(
                models.When(name__icontains=query_text, then=Value(0.1)),
                default=Value(0.0),
                output_field=FloatField(),
            ),
            rank=(F("plain_rank")* F("token_ratio") + F("ordered_bonus")),
        )
        end_query_set_annotate = time.perf_counter()
        print(f"Time to annotate query set with ranking: {end_query_set_annotate - start_query_set_annotate:.6f} seconds")
        
        return res

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
        
        start_tokenize_query = time.perf_counter()
        # Retrieve tokens from query string (stemmed)
        tokens = ts_tokenize(query_text, "english")
        query_set = self
        end_tokenize_query = time.perf_counter()
        print(f"Time to tokenize query {end_tokenize_query - start_tokenize_query:.6f} seconds")


        # No tokens, we cannot query anything
        if not tokens:
            return query_set.none()

        # Apply base filter (always includes user)
        start_get_user_files = time.perf_counter()
        all_user_files = query_set.filter(base_filter)
        end_get_user_files = time.perf_counter()
        print(f"Time to get all user files {end_get_user_files - start_get_user_files:.6f} seconds")


        # Get totalt number of documents for user
        # Important to do here before query_set is reduced
        start_user_documents_count = time.perf_counter()
        user_documents_count = all_user_files.count()
        end_user_documents_count = time.perf_counter()
        print(f"Time to count user documents {end_user_documents_count - start_user_documents_count:.6f} seconds")

        # Compute document frequencies for all terms included in the query over all user files
        start_document_frequencies = time.perf_counter()
        document_frequencies = get_document_frequencies_matching_tokens(
            all_user_files, tokens
        )
        end_document_frequencies = time.perf_counter()
        print(f"Time to compute document frequencies {end_document_frequencies - start_document_frequencies:.6f} seconds")

        # Build SearchQuery by combining tokens with | operator
        start_search_query = time.perf_counter()
        search_query = SearchQuery(
            " | ".join(tokens), search_type="raw", config="english"
        )
        end_search_query = time.perf_counter()
        print(f"Time to create raw SearchQuery: {end_search_query - start_search_query:.6f} seconds")

        # Use the GIN index to find files matching query
        start_user_files_matching_query = time.perf_counter()
        user_files_matching_query = all_user_files.filter(tsContent=search_query)
        end_user_files_matching_query = time.perf_counter()
        print(f"Time to filter user files matching query: {end_user_files_matching_query - start_user_files_matching_query:.6f} seconds")

        # Compute ltc stats for the query
        start_query_ltc = time.perf_counter()
        query_ltc = get_query_ltc(user_documents_count, tokens, document_frequencies)
        end_query_ltc = time.perf_counter()
        print(f"Time to compute query ltc: {end_query_ltc - start_query_ltc:.6f} seconds")

        # Calculate document lnc for each file
        start_file_stats_list = time.perf_counter()
        file_stats_list = [
            {
                file.id: get_document_lnc(
                    get_term_frequencies_for_file(file)
                )
            }
            for file in user_files_matching_query
        ]
        # files_data = user_files_matching_query.values_list('id', 'tsContent')

        # file_stats_list = []

        # # 2. Iterate through the tuples in Python (very fast)
        # for file_id, ts_content_raw in files_data:
        #     # Use our new Python helper instead of a SQL query
        #     term_frequencies = parse_tsvector(ts_content_raw)
            
        #     # Calculate lnc using existing logic
        #     lnc_vector = get_document_lnc(term_frequencies)
            
        #     file_stats_list.append({file_id: lnc_vector})
        end_file_stats_list = time.perf_counter()
        print(f"Time to compute file stats list: {end_file_stats_list - start_file_stats_list:.6f} seconds")

        # Compute a score for each file
        start_scored_files = time.perf_counter()
        scored_files = compute_score_for_files(query_ltc, file_stats_list)
        end_scored_files = time.perf_counter()
        print(f"Time to compute scored files: {end_scored_files - start_scored_files:.6f} seconds")

        # Add rank attribute to the files
        start_scored_files_assignment = time.perf_counter()
        for file in user_files_matching_query:
            file.rank = scored_files.get(file.id, 0.0)
        end_scored_files_assignment = time.perf_counter()
        print(f"Time to assign ranks to files: {end_scored_files_assignment - start_scored_files_assignment:.6f} seconds")

        return user_files_matching_query


class FileManager(models.Manager.from_queryset(FileQuerySet)):
    """Custom manager for File model using FileQuerySet."""
