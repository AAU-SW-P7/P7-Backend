from django.db import connection, models


def ts_tokenize(text, config):
    "Tokenizes a string using PostgreSQL's tsvector parser"
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT unnest(tsvector_to_array(to_tsvector(%s, %s)))", [config, text]
        )
        return [row[0] for row in cursor.fetchall()]


def ts_lexize(token):
    "Lexizes (stems) a token"
    with connection.cursor() as cursor:
        cursor.execute("SELECT ts_lexize('english_stem', %s);", [token])
        results = cursor.fetchone()
        return results[0] if results and results[0] is not None else []


def get_document_frequencies_matching_tokens(
    query_set: models.QuerySet, terms: list[str]
):
    """
    Gets all files for a user (included in query_set)
    Calls ts_stat() on the retrieved user files filtering out ndoc (document frequency)
    Only returns the document frequencies for terms matching our tokens
    params:
        query_set: The query containing the user we need to search files for
        terms: List of terms included in the user query
    returns:
        A list of (term, document_frequency)
    """
    # Convert the Django QuerySet into the raw SQL query
    # Only return tsContent (tsVector for the content) for each file
    sql, params = query_set.values("tsContent").query.sql_with_params()

    # Wrap the above SQL in the ts_stat() function
    ts_sql = (
        """
            SELECT word, ndoc
            FROM ts_stat($$%s$$)
        """
        % sql
    )

    # Execute the SQL
    with connection.cursor() as cursor:
        cursor.execute(ts_sql, params)
        ts_stats = cursor.fetchall()
        
        # Filter out rows not matching query terms
        filtered_stats = [row for row in ts_stats if row[0] in terms]
    return filtered_stats


def get_term_frequencies_for_file(query_set, file_id):
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
