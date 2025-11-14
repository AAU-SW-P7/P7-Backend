from django.db import connection

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