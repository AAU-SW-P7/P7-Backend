from math import log10, sqrt


def get_query_ltc(user_documents, tokens, document_frequencies):
    query_term_stats = {}
    df_dict = dict(document_frequencies)

    # Compute tf-idf and accumulate squared sum
    squared_sum = 0.0
    for token in set(tokens):
        tf_raw = tokens.count(token)
        tf_wt = 1 + log10(tf_raw)
        df = df_dict.get(
            token, 0
        )  # Get the document frequency if it exists, otherwise set it to 0
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
        stats["norm"] = stats["tf-idf"] / length if length != 0 else 0 

    return query_term_stats


def get_document_lnc(term_frequencies):
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
        stats["norm"] = stats["tf-idf"] / length if length != 0 else 0 

    return document_term_stats


def compute_score_for_files(query_term_stats, file_stats_list):
    file_scores = {}
    for file_stat in file_stats_list:
        (file_id, doc_stats), prod = next(iter(file_stat.items())), 0.0
        for term, stats in query_term_stats.items():
            doc_term = doc_stats.get(term)
            if doc_term:
                prod += stats["norm"] * doc_term["norm"]
        file_scores[file_id] = prod
    return file_scores
