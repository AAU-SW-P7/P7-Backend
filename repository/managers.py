""" " Manager for ranking files based on query matches."""

from math import log10, sqrt
from django.db import models
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import F, Value, FloatField
from repository.helpers import ts_tokenize
from django.db import connection


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
        document_frequencies = self.get_document_frequencies_matching_tokens(
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
        query_ltc = self.get_query_ltc(user_documents, tokens, document_frequencies)
        # print(f"QUERY STATALATS: {query_ltc}" )

        # Calculate document lnc
        files = list(query_set)
        file_stats = []
        for file in files:
            term_frequencies = self.get_term_frequencies_for_file(
                query_set, tokens, file.id
            )
            # print(f"THESE ARE THE TERM FREQUENCIES {term_frequencies}")
            stats = self.get_document_lnc(term_frequencies)
            # print(f"RESULT FOR FILE {file.name}: {result}")
            file_stats.append({file.id: stats})

        scored_files = self.compute_score_for_files(query_ltc, file_stats)

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

    def get_document_frequencies_matching_tokens(self, query_set, tokens):
        # Get the total number of documents for a user
        sql, params = query_set.values("tsContent").query.sql_with_params()
        ts_sql = (
            """
            SELECT word, ndoc
            FROM ts_stat($$%s$$)
        """
            % sql
        )
        with connection.cursor() as cursor:
            cursor.execute(ts_sql, params)
            ts_stats = cursor.fetchall()
            filtered_stats = [row for row in ts_stats if row[0] in tokens]
        return filtered_stats

    def get_term_frequencies_for_file(self, query_set, tokens, file_id):
        file_ts_query = query_set.filter(pk=file_id).values("tsContent")

        if not file_ts_query.exists():
            return []

        sql, params = file_ts_query.query.sql_with_params()
        ts_sql = (
            """
            SELECT word, nentry
            FROM ts_stat($$%s$$)
        """
            % sql
        )
        with connection.cursor() as cursor:
            cursor.execute(ts_sql, params)
            ts_stats = cursor.fetchall()
        return ts_stats

    def get_query_ltc(self, user_documents, tokens, document_frequencies):
        query_term_stats = {}
        df_dict = dict(document_frequencies)

        # Compute tf-idf and accumulate squared sum
        squared_sum = 0.0
        for token in set(tokens):
            tf_raw = tokens.count(token)
            tf_wt = 1 + log10(tf_raw)
            df = df_dict.get(token,0) # Get the document frequency if it exists, otherwise set it to 0
            idf = log10(user_documents / df) if df != 0 else 0
            tf_idf = tf_wt * idf

            query_term_stats[token] = {
                "tf-raw": tf_raw,
                "tf-wt": tf_wt,
                "df": df,
                "idf": idf,
                "tf-idf": tf_idf,
            }
            squared_sum += tf_idf**2

        # Compute vector length
        length = sqrt(squared_sum)

        # Add normalized weight
        for token, stats in query_term_stats.items():
            stats["norm"] = stats["tf-idf"] / length

        return query_term_stats

    def get_document_lnc(self, term_frequencies):
        document_term_stats = {}
        tf_dict = dict(term_frequencies)

        # Compute tf-idf and accumulate squared sum
        squared_sum = 0.0

        for term in tf_dict:
            tf_raw = tf_dict[term]
            tf_wt = 1 + log10(tf_raw)
            tf_idf = tf_wt  # Since we use lnc the df is 1

            document_term_stats[term] = {
                "tf-raw": tf_raw,
                "tf-wt": tf_wt,
                "tf-idf": tf_idf,
            }
            squared_sum += tf_idf**2

        # Compute vector length
        length = sqrt(squared_sum)

        # Add normalized weight
        for term, stats in document_term_stats.items():
            stats["norm"] = stats["tf-idf"] / length

        return document_term_stats

    def compute_score_for_files(self, query_term_stats, file_stats_list):
        file_scores = {}
        # print(f"THESE ARE THE QUERY STATALLALLALAA: {query_term_stats}")
        for file_stat in file_stats_list:
            (file_id, doc_stats), prod = next(iter(file_stat.items())), 0.0
            for term, stats in query_term_stats.items():
                doc_term = doc_stats.get(term)
                if doc_term:
                    prod += stats["norm"] * doc_term["norm"]
            file_scores[file_id] = prod
        return file_scores


class FileManager(models.Manager.from_queryset(FileQuerySet)):
    """Custom manager for File model using FileQuerySet."""
