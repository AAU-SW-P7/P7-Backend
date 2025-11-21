from math import log10, sqrt
from collections import Counter
from typing import Callable, Dict, Iterable, Mapping, Sequence, Union, List

TermStats = Dict[str, Union[float, int]]
DocumentStats = Dict[str, TermStats]


def build_weighted_vector(
    freq_map: Dict[str, int], idf_lookup: Callable[[str], float]
) -> DocumentStats:
    """
    Build a normalized tf-idf vector from term frequencies.

    Args:
        freq_map: Mapping of term to its raw frequency within a document or query.
        idf_lookup: Function returning the inverse document frequency for a term.

    Returns:
        DocumentStats: Per-term statistics including tf, idf, tf-idf, and normalized weights.
    """
    term_stats, squared_sum = {}, 0.0

    for term, tf_raw in freq_map.items():
        tf_wt = 1 + log10(tf_raw)
        idf = idf_lookup(term)
        tf_idf = tf_wt * idf
        term_stats[term] = {
            "tf-raw": tf_raw,
            "tf-wt": tf_wt,
            "idf": idf,
            "tf-idf": tf_idf,
        }
        squared_sum += tf_idf**2

    length = sqrt(squared_sum)

    for term in term_stats:
        term_stats[term]["norm"] = term_stats[term]["tf-idf"] / length if length else 0
    return term_stats


def get_query_ltc(
    user_documents: int,
    query_tokens: Sequence[str],
    document_frequencies: Mapping[str, int],
):
    """
    Compute the ltc-weighted vector for a query.

    Args:
        user_documents: Total number of user documents.
        query_tokens: Tokenized query terms.
        document_frequencies: Frequency of term accross all user files

    Returns:
        DocumentStats: LTC-normalized statistics for the query terms.
    """
    # Dictionary holding term: document_frequency mapping
    df_lookup = dict(document_frequencies)
    # Term frequency of each token in the query
    freq_map = Counter(query_tokens)
    return build_weighted_vector(
        # The lambda function calculates the inverted document frequency for a term
        freq_map,
        lambda term: (
            log10(user_documents / df_lookup[term]) if df_lookup.get(term) else 0
        ),
    )


def get_document_lnc(term_frequencies:  Mapping[str, int]):
    """
    Compute the lnc-weighted vector for a document.

    Args:
        term_frequencies: Term frequency data for the document

    Returns:
        DocumentStats: LNC-normalized statistics for the document terms
    """
    # Dictionary holding term: term_frequency mapping
    freq_map = dict(term_frequencies)
    
    # When computing lnc the df is 1
    return build_weighted_vector(
        freq_map, lambda _term: 1.0
    )


def compute_score_for_files(query_term_stats: DocumentStats, file_stats_list: List[Dict[int, DocumentStats]]):
    """
    Calculate cosine similarity scores between a query vector and document vectors.

    Args:
        query_term_stats: Normalized statistics for query terms.
        file_stats_list: List of document stats keyed by file identifier.

    Returns:
        Dict[str, float]: Mapping from file identifier to similarity score.
    """
    file_scores = {}
    for file_stat in file_stats_list:
        (file_id, doc_stats), prod = next(iter(file_stat.items())), 0.0
        for term, stats in query_term_stats.items():
            doc_term = doc_stats.get(term)
            if doc_term:
                prod += stats["norm"] * doc_term["norm"]
        file_scores[file_id] = prod
    return file_scores
