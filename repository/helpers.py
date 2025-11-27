"""Helper for working with ts_lexize() and ts_stat() from PostgreSQL"""

from django.db import connection, models


def ts_tokenize(text, config):
    """
    Tokenizes a string using PostgreSQL's tsvector parser
    """
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT unnest(tsvector_to_array(to_tsvector(%s, %s)))", [config, text]
        )
        return [row[0] for row in cursor.fetchall()]


def ts_lexize(token):
    """
    Lexizes (stems) a token
    """
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
        A list of (term, document_frequency): list[tuple[str, int]]
    """
    # Convert the Django QuerySet into the raw SQL query
    # Only return tsContent (tsVector for the content) for each file
    sql, params = query_set.values("tsContent").query.sql_with_params()

    # Wrap the above SQL in the ts_stat() function
    ts_sql = f"""
            SELECT word, ndoc
            FROM ts_stat($${sql}$$)
        """

    # Execute the SQL
    with connection.cursor() as cursor:
        cursor.execute(ts_sql, params)
        ts_stats = cursor.fetchall()

        # Filter out rows not matching query terms
        filtered_stats = [row for row in ts_stats if row[0] in terms]
    return filtered_stats

def get_term_frequencies_for_file(file):
    """
    Retrieve term frequencies using ts_stat() for a single file instance.
    Args:
        file: A model instance with a tsContent field.
    """
    ts_sql = """
        SELECT word, nentry
        FROM ts_stat($$SELECT %s::tsvector$$)
    """

    with connection.cursor() as cursor:
        cursor.execute(ts_sql, [file.tsContent])
        return cursor.fetchall()