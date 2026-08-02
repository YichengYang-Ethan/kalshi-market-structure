"""Regression tests for the structural parsers.

Every case here comes from a real leg subtitle that a previous version of the parser
got wrong; the comments name the category that surfaced it.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from kalshi_structure.taxonomy import (  # noqa: E402
    classify_event, parse_bucket, parse_deadline, parse_threshold, partition_is_tiled,
    quantisation_evidence,
)


def test_threshold_grammars():
    # Elections: subject-qualified margin ladder
    assert parse_threshold("Republicans, 26+ pts") == ("republicans", 26.0, ">=")
    # Sports: trailing unit noun after the level
    assert parse_threshold("6+ wins") == ("", 6.0, ">=")
    # Sports: subject prefix with an 'over' comparator and a trailing noun
    assert parse_threshold("Arizona over 1.5 runs scored") == ("arizona", 1.5, ">=")
    # Economics / Mentions: compact comparators on integer counts
    assert parse_threshold("<9") == ("", 9.0, "<=")
    assert parse_threshold(">20") == ("", 20.0, ">=")
    # Financials: magnitude suffixes and currency
    assert parse_threshold("Above 250K") == ("", 250000.0, ">=")
    assert parse_threshold("$150,000 or above") == ("", 150000.0, ">=")
    # Both tail directions
    assert parse_threshold("Below 60.5%") == ("", 60.5, "<=")
    assert parse_threshold("0.0% or Below") == ("", 0.0, "<=")


def test_bucket_and_deadline():
    assert parse_bucket("95,000 to 99,999.99") == (95000.0, 99999.99)
    assert parse_bucket("0.1% to 0.5%") == (0.1, 0.5)
    assert parse_deadline("Before Jan 1, 2027") == (2027, 1, 1)
    assert parse_deadline("Before 2027") == (2027, 1, 1)


def _ladder(subtitles):
    return {"markets": [{"status": "active", "yes_sub_title": s} for s in subtitles]}


def test_tiling_is_scale_invariant():
    """A quantised closed-range ladder tiles regardless of the index's magnitude.

    The earlier relative-tolerance test accepted the ~61-valued ladder and rejected the
    ~2-valued one despite identical structure, which produced a spurious finding that
    most Economics partitions had settlement gaps.
    """
    gdp = _ladder(["0.0% or Below", "0.1% to 0.5%", "0.6% to 1.0%", "1.1% or Above"])
    lfp = _ladder(["Below 60.5%", "60.5% to 60.9%", "61.0% to 61.4%", "61.5% or Above"])
    assert partition_is_tiled(gdp)
    assert partition_is_tiled(lfp)


def test_tiling_rejects_a_gap_the_size_of_a_bucket():
    """A gap comparable to a bucket is a hole, not a reporting quantum."""
    holed = _ladder(["Below 10", "10 to 19", "25 to 30", "31 or Above"])
    assert not partition_is_tiled(holed)


def test_tiling_accepts_segmented_tick_sizes():
    """Crypto ladders change tick size within one event; that is still a tiling."""
    xrp = _ladder([
        "$0.5199999 or below", "$0.52 to $0.5299999", "$0.53 to $0.5399999",
        "$0.54 to $0.549", "$0.55 or above",
    ])
    assert partition_is_tiled(xrp)


def test_consistent_gaps_are_not_sufficient_for_exhaustiveness():
    """Arithmetic cannot separate a quantum from a hole; rule text can.

    These two ladders have identical gap structure. GDP is published to one decimal
    place so nothing falls between its buckets; an acquisition price can settle at
    $9.5B, which no leg of the price ladder pays.
    """
    gdp = {"markets": [
        {"status": "active", "yes_sub_title": "0.0% or Below", "rules_secondary": "All stated bounds are inclusive. The value is rounded to one decimal place."},
        {"status": "active", "yes_sub_title": "0.1% to 0.5%", "rules_secondary": ""},
        {"status": "active", "yes_sub_title": "0.6% or Above", "rules_secondary": ""},
    ]}
    price = _ladder(["$0 or Below", "$1 to $9", "$10 or Above"])
    assert partition_is_tiled(gdp) and partition_is_tiled(price)
    assert quantisation_evidence(gdp) is not None
    assert quantisation_evidence(price) is None


def test_combination_detected_from_rule_text_not_conjunctions():
    """Entity names contain 'and'; only the contract template is evidence."""
    nations = {
        "mutually_exclusive": True,
        "markets": [
            {"status": "active", "yes_sub_title": "Bosnia and Herzegovina", "rules_primary": "If Bosnia and Herzegovina wins, then the market resolves to Yes."},
            {"status": "active", "yes_sub_title": "Antigua and Barbuda", "rules_primary": "If Antigua and Barbuda wins, then the market resolves to Yes."},
        ],
    }
    assert classify_event(nations) == "entity_menu"

    combo = {
        "mutually_exclusive": True,
        "markets": [
            {"status": "active", "yes_sub_title": "Democrats sweep", "rules_primary": "If ALL of the following occur: Governor: Democrat, Senate: Democrat, then the market resolves to Yes."},
            {"status": "active", "yes_sub_title": "Republicans sweep", "rules_primary": "If ALL of the following occur: Governor: Republican, Senate: Republican, then the market resolves to Yes."},
        ],
    }
    assert classify_event(combo) == "combination"
