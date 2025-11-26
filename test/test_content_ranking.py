"""Testing of the core ranking function responsible for calculating tf-idf"""

import os
import sys
import math
from pathlib import Path

# Make the local backend package importable so `from p7...` works under pytest
repo_backend = Path(__file__).resolve().parents[1]  # backend/
sys.path.insert(0, str(repo_backend))
# Make the backend/test dir importable so you can use test_settings.py directly
sys.path.insert(0, str(repo_backend / "test"))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "test_settings")

import django

django.setup()

import pytest
import pytest_check as check

from p7.search.content_ranking import (
    compute_score_for_files,
    get_document_lnc,
    get_query_ltc,
)

# --- TESTING of get_query_ltc ---


def test_get_query_ltc_computes_expected_stats():
    """Ensure get_query_ltc returns correct TF, IDF, TF-IDF, and norms for a standard query."""
    user_documents = 10
    query_tokens = ["cloud", "storage", "cloud", "files"]
    document_frequencies = {"cloud": 4, "storage": 2, "files": 5}

    stats = get_query_ltc(user_documents, query_tokens, document_frequencies)

    tf_cloud = 2
    tf_storage = 1
    tf_files = 1
    tf_wt_cloud = 1 + math.log10(tf_cloud)
    tf_wt_storage = 1 + math.log10(tf_storage)
    tf_wt_files = 1 + math.log10(tf_files)
    idf_cloud = math.log10(user_documents / document_frequencies["cloud"])
    idf_storage = math.log10(user_documents / document_frequencies["storage"])
    idf_files = math.log10(user_documents / document_frequencies["files"])
    tf_idf_cloud = tf_wt_cloud * idf_cloud
    tf_idf_storage = tf_wt_storage * idf_storage
    tf_idf_files = tf_wt_files * idf_files

    length = math.sqrt(tf_idf_cloud**2 + tf_idf_storage**2 + tf_idf_files**2)

    # Check each term only appears once in the stats
    check.equal(stats.keys(), {"cloud", "storage", "files"})

    # Check term freqency for each term in the query
    check.equal(stats["cloud"]["tf-raw"], tf_cloud)
    check.equal(stats["storage"]["tf-raw"], tf_storage)
    check.equal(stats["files"]["tf-raw"], tf_files)

    # Check weighted term frequency
    check.equal(stats["cloud"]["tf-wt"], pytest.approx(tf_wt_cloud))
    check.equal(stats["storage"]["tf-wt"], pytest.approx(tf_wt_storage))
    check.equal(stats["files"]["tf-wt"], pytest.approx(tf_wt_files))

    # Check inverted document frequency
    check.equal(stats["cloud"]["idf"], pytest.approx(idf_cloud))
    check.equal(stats["storage"]["idf"], pytest.approx(idf_storage))
    check.equal(stats["files"]["idf"], pytest.approx(idf_files))

    # Check tf-idf score (wt)
    check.equal(stats["cloud"]["tf-idf"], pytest.approx(tf_idf_cloud))
    check.equal(stats["storage"]["tf-idf"], pytest.approx(tf_idf_storage))
    check.equal(stats["files"]["tf-idf"], pytest.approx(tf_idf_files))

    # Check normalized scores
    check.equal(stats["cloud"]["norm"], pytest.approx(tf_idf_cloud / length))
    check.equal(stats["storage"]["norm"], pytest.approx(tf_idf_storage / length))
    check.equal(stats["files"]["norm"], pytest.approx(tf_idf_files / length))


def test_get_query_ltc_handles_missing_document_frequencies():
    """Verify missing document frequency entries default to zero IDF"""
    user_documents = 20
    query_tokens = ["sync", "backup", "sync", "offline"]
    document_frequencies = {"sync": 4, "backup": 4}  # "offline" missing

    stats = get_query_ltc(user_documents, query_tokens, document_frequencies)

    tf_sync = 2
    tf_backup = 1
    tf_offline = 1
    tf_wt_sync = 1 + math.log10(tf_sync)
    tf_wt_backup = 1 + math.log10(tf_backup)
    tf_wt_offline = 1 + math.log10(tf_offline)
    idf_sync = math.log10(user_documents / document_frequencies["sync"])
    idf_backup = math.log10(user_documents / document_frequencies["backup"])
    idf_offline = 0.0
    tf_idf_sync = tf_wt_sync * idf_sync
    tf_idf_backup = tf_wt_backup * idf_backup
    length = math.sqrt(tf_idf_sync**2 + tf_idf_backup**2)

    check.equal(stats["sync"]["tf-raw"], tf_sync)
    check.equal(stats["backup"]["tf-raw"], tf_backup)
    check.equal(stats["offline"]["tf-raw"], tf_offline)
    check.equal(stats["sync"]["tf-wt"], pytest.approx(tf_wt_sync))
    check.equal(stats["backup"]["tf-wt"], pytest.approx(tf_wt_backup))
    check.equal(stats["offline"]["tf-wt"], pytest.approx(tf_wt_offline))
    check.equal(stats["sync"]["idf"], pytest.approx(idf_sync))
    check.equal(stats["backup"]["idf"], pytest.approx(idf_backup))
    check.equal(stats["offline"]["idf"], pytest.approx(idf_offline))
    check.equal(stats["sync"]["norm"], pytest.approx(tf_idf_sync / length))
    check.equal(stats["backup"]["norm"], pytest.approx(tf_idf_backup / length))
    check.equal(stats["offline"]["norm"], pytest.approx(0.0))


def test_get_query_ltc_handles_no_documents():
    """Return an empty stats dict when no documents exist"""
    stats = get_query_ltc(
        user_documents=0,
        query_tokens=["cloud", "storage", "cloud", "files"],
        document_frequencies={"cloud": 4, "storage": 2, "files": 5},
    )
    check.equal(stats, {})


def test_get_query_ltc_handles_empty_query():
    """Return an empty stats dict when the provided query has no tokens."""
    stats = get_query_ltc(
        user_documents=25,
        query_tokens=[],
        document_frequencies={"cloud": 4, "storage": 2, "files": 5},
    )
    check.equal(stats, {})


def test_get_query_ltc_handles_no_document_frequencies():
    """Set IDF-derived values to zero when document frequencies are unavailable."""
    stats = get_query_ltc(
        user_documents=25,
        query_tokens=["cloud", "storage", "cloud", "files"],
        document_frequencies={},
    )

    # Check inverted document frequency
    check.equal(stats["cloud"]["idf"], 0)
    check.equal(stats["storage"]["idf"], 0)
    check.equal(stats["files"]["idf"], 0)

    # Check tf-idf score (wt)
    check.equal(stats["cloud"]["tf-idf"], 0)
    check.equal(stats["storage"]["tf-idf"], 0)
    check.equal(stats["files"]["tf-idf"], 0)

    # Check normalized scores
    check.equal(stats["cloud"]["norm"], 0)
    check.equal(stats["storage"]["norm"], 0)
    check.equal(stats["files"]["norm"], 0)


def test_get_query_ltc_handles_no_valid_input():
    """Return an empty dict when both the query tokens and document frequencies are missing"""
    stats = get_query_ltc(user_documents=25, query_tokens=[], document_frequencies={})
    check.equal(stats, {})


# --- TESTING of get_document_lnc ---


def test_get_document_lnc_returns_expected_document_stats():
    """Validate TF, IDF, TF-IDF, and normalization for a multi-term document."""
    term_frequencies = {"report": 4, "summary": 2, "data": 1}

    stats = get_document_lnc(term_frequencies)

    tf_wt_report = 1 + math.log10(4)
    tf_wt_summary = 1 + math.log10(2)
    tf_wt_data = 1 + math.log10(1)
    tf_idf_report = tf_wt_report * 1.0
    tf_idf_summary = tf_wt_summary * 1.0
    tf_idf_data = tf_wt_data * 1.0
    length = math.sqrt(tf_idf_report**2 + tf_idf_summary**2 + tf_idf_data**2)

    check.equal(stats["report"]["tf-raw"], 4)
    check.equal(stats["summary"]["tf-raw"], 2)
    check.equal(stats["data"]["tf-raw"], 1)
    check.equal(stats["report"]["idf"], pytest.approx(1.0))
    check.equal(stats["summary"]["idf"], pytest.approx(1.0))
    check.equal(stats["data"]["idf"], pytest.approx(1.0))
    check.equal(stats["report"]["tf-idf"], pytest.approx(tf_idf_report))
    check.equal(stats["summary"]["tf-idf"], pytest.approx(tf_idf_summary))
    check.equal(stats["data"]["tf-idf"], pytest.approx(tf_idf_data))
    check.equal(stats["report"]["norm"], pytest.approx(tf_idf_report / length))
    check.equal(stats["summary"]["norm"], pytest.approx(tf_idf_summary / length))
    check.equal(stats["data"]["norm"], pytest.approx(tf_idf_data / length))


def test_get_document_lnc_handles_empty_term_frequencies():
    """Return an empty result when a document has no recorded term frequencies."""
    stats = get_document_lnc(term_frequencies={})
    check.equal(stats, {})


def test_get_document_lnc_single_term_normalizes_to_one():
    """Confirm a single-term document normalizes to a cosine length of one."""
    term_frequencies = {"agenda": 7}

    stats = get_document_lnc(term_frequencies)

    tf_wt = 1 + math.log10(7)
    tf_idf = tf_wt * 1.0
    length = math.sqrt(tf_idf**2)

    check.equal(stats["agenda"]["tf-raw"], 7)
    check.equal(stats["agenda"]["tf-wt"], pytest.approx(tf_wt))
    check.equal(stats["agenda"]["tf-idf"], pytest.approx(tf_idf))
    check.equal(stats["agenda"]["norm"], pytest.approx(tf_idf / length))
    check.equal(stats["agenda"]["norm"], pytest.approx(1.0))


# --- TESTING of compute_score_for_files ---


def test_compute_score_for_files_returns_cosine_scores():
    """Check cosine similarity scoring between query terms and multiple documents."""
    query_term_stats = {
        "alpha": {"norm": 0.8},
        "beta": {"norm": 0.6},
    }
    file_stats_list = [
        {1: {"alpha": {"norm": 0.5}, "beta": {"norm": 0.5}}},
        {2: {"alpha": {"norm": 0.8}}},
        {3: {"gamma": {"norm": 1.0}}},
    ]

    scores = compute_score_for_files(query_term_stats, file_stats_list)

    check.equal(scores[1], pytest.approx(0.8 * 0.5 + 0.6 * 0.5))
    check.equal(scores[2], pytest.approx(0.8 * 0.8))
    check.equal(scores[3], pytest.approx(0.0))


def test_compute_score_for_files_reflects_query_weight_changes():
    """Ensure document ranking shifts appropriately when query term weights change."""
    file_stats_list = [
        {101: {"cloud": {"norm": 0.6}, "backup": {"norm": 0.4}}},
        {102: {"cloud": {"norm": 0.2}, "backup": {"norm": 0.8}}},
    ]

    balanced_query = {"cloud": {"norm": 0.5}, "backup": {"norm": 0.5}}
    backup_heavy_query = {"cloud": {"norm": 0.2}, "backup": {"norm": 0.8}}
    cloud_heavy_query = {"cloud": {"norm": 0.85}, "backup": {"norm": 0.15}}

    balanced_scores = compute_score_for_files(balanced_query, file_stats_list)
    heavy_scores = compute_score_for_files(backup_heavy_query, file_stats_list)
    cloud_scores = compute_score_for_files(cloud_heavy_query, file_stats_list)

    check.equal(
        balanced_scores[101],
        pytest.approx(
            balanced_query["cloud"]["norm"] * file_stats_list[0][101]["cloud"]["norm"]
            + balanced_query["backup"]["norm"] * file_stats_list[0][101]["backup"]["norm"]
        ),
    )

    check.equal(
        balanced_scores[102],
        pytest.approx(
            balanced_query["cloud"]["norm"] * file_stats_list[1][102]["cloud"]["norm"]
            + balanced_query["backup"]["norm"] * file_stats_list[1][102]["backup"]["norm"]
        ),
    )

    check.equal(
        heavy_scores[101],
        pytest.approx(
            backup_heavy_query["cloud"]["norm"] * file_stats_list[0][101]["cloud"]["norm"]
            + backup_heavy_query["backup"]["norm"] * file_stats_list[0][101]["backup"]["norm"]
        ),
    )

    check.equal(
        heavy_scores[102],
        pytest.approx(
            backup_heavy_query["cloud"]["norm"] * file_stats_list[1][102]["cloud"]["norm"]
            + backup_heavy_query["backup"]["norm"] * file_stats_list[1][102]["backup"]["norm"]
        ),
    )

    check.equal(
        cloud_scores[101],
        pytest.approx(
            cloud_heavy_query["cloud"]["norm"] * file_stats_list[0][101]["cloud"]["norm"]
            + cloud_heavy_query["backup"]["norm"] * file_stats_list[0][101]["backup"]["norm"]
        ),
    )

    check.equal(
        cloud_scores[102],
        pytest.approx(
            cloud_heavy_query["cloud"]["norm"] * file_stats_list[1][102]["cloud"]["norm"]
            + cloud_heavy_query["backup"]["norm"] * file_stats_list[1][102]["backup"]["norm"]
        ),
    )

    check.equal(cloud_scores[101] > cloud_scores[102], True)
    check.equal(heavy_scores[102] > heavy_scores[101], True)
