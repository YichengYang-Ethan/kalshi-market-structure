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


def test_quote_strings_are_not_tested_for_truthiness():
    """Quote fields are decimal strings; bool("0.0000") is True.

    Using bool() as a proxy for 'this side is quoted' marked every market on the
    exchange as two-sided in a published index.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "bsi", os.path.join(os.path.dirname(__file__), "..", "scripts", "build_structure_index.py"))
    # Import the helper without running the module's collection pass.
    src = open(spec.origin).read()
    ns = {}
    start = src.index("def quoted(")
    end = src.index("series = load_series()")
    exec(compile(src[start:end], spec.origin, "exec"), ns)
    quoted = ns["quoted"]
    assert quoted("0.4500") is True
    assert quoted("0.0000") is False      # the bug
    assert quoted("1.0000") is False      # not a live quote
    assert quoted("") is False
    assert quoted(None) is False


def test_combination_wins_over_threshold():
    """Combination legs also satisfy the threshold grammar, so order decides."""
    combo = {"markets": [
        {"status": "active", "yes_sub_title": "Core above 0.3% and headline above 0.2%",
         "rules_primary": "If ALL of the following occur: core CPI above 0.3%, headline CPI above 0.2%, then the market resolves to Yes."},
        {"status": "active", "yes_sub_title": "Core above 0.4% and headline above 0.3%",
         "rules_primary": "If ALL of the following occur: core CPI above 0.4%, headline CPI above 0.3%, then the market resolves to Yes."}]}
    assert classify_event(combo) == "combination"


def test_generator_label_survives_its_legs_settling():
    """A ladder with one rung left is still a ladder; only its tradeable shape is binary."""
    ladder = {"markets": [
        {"status": "finalized", "yes_sub_title": "Before Jun 1, 2026"},
        {"status": "finalized", "yes_sub_title": "Before Jul 1, 2026"},
        {"status": "finalized", "yes_sub_title": "Before Aug 1, 2026"},
        {"status": "active", "yes_sub_title": "Before Jan 1, 2027"}]}
    assert classify_event(ladder) == "deadline"
    assert classify_event(ladder, active_only=True) == "binary"


def test_buy_all_requires_explicit_exhaustiveness():
    from kalshi_structure.relations import Partition, Quote
    q = [Quote("A", 0.30, 0.31, 100, 100), Quote("B", 0.60, 0.62, 100, 100)]
    for grade, expect_edge in (("explicit", True), ("implicit", False), ("none", False)):
        p = Partition(legs=("A", "B"), tiled=True, basis="test", exhaustiveness=grade)
        assert (p.evaluate_buy_all(q) is not None) is expect_edge


def test_published_index_formats_agree():
    """Every published format must come from the same run.

    The plain CSV was once produced by hand from the gzip file; when the classifier
    changed, the two diverged and the plain file kept serving the previous run's labels
    for as long as nobody compared them.
    """
    import csv, gzip
    from collections import Counter
    root = os.path.join(os.path.dirname(__file__), "..", "data")
    # Skipping silently when the index is absent means this test passes on a checkout
    # where the artifacts were never built, which is exactly when it is needed.
    for name in ("events_index.csv", "events_index.csv.gz",
                 "markets_index.csv.gz", "series_rollup.csv"):
        assert os.path.exists(os.path.join(root, name)), f"missing published artifact: {name}"
    with open(os.path.join(root, "events_index.csv")) as f:
        plain = [dict(r) for r in csv.DictReader(f)]
    with gzip.open(os.path.join(root, "events_index.csv.gz"), "rt") as f:
        packed = [dict(r) for r in csv.DictReader(f)]
    assert plain == packed

    with gzip.open(os.path.join(root, "markets_index.csv.gz"), "rt") as f:
        markets = [dict(r) for r in csv.DictReader(f)]
    with open(os.path.join(root, "series_rollup.csv")) as f:
        roll = [dict(r) for r in csv.DictReader(f)]
    # Reconcile the rollup against the market index field by field, not just in total.
    from collections import defaultdict
    recomputed = defaultdict(lambda: dict(n_markets=0, n_active=0, n_ever_traded=0,
                                          n_traded_24h=0, n_two_sided=0, templates=set()))
    for m in markets:
        a = recomputed[m["series_ticker"]]
        a["n_markets"] += 1
        a["n_active"] += int(m["status"] == "active")
        a["n_ever_traded"] += int(m["ever_traded"])
        a["n_traded_24h"] += int(m["traded_24h"])
        a["n_two_sided"] += int(m["two_sided"])
        a["templates"].add(m["template"])
    assert len(roll) == len(recomputed)
    for r in roll:
        a = recomputed[r["series_ticker"]]
        for field in ("n_markets", "n_active", "n_ever_traded", "n_traded_24h", "n_two_sided"):
            assert int(r[field]) == a[field], f"{r['series_ticker']}.{field}"
        assert r["templates"] == "|".join(sorted(a["templates"]))

    # Every market's event and template must agree with the event index.
    events = {r["event_ticker"]: r for r in plain}
    for m in markets:
        e = events.get(m["event_ticker"])
        assert e is not None, m["ticker"]
        assert m["template"] == e["template"], m["ticker"]
    per_event = Counter(m["event_ticker"] for m in markets)
    for e in plain:
        assert int(e["n_markets"]) == per_event[e["event_ticker"]], e["event_ticker"]

    # The truthiness bug made this exactly 100%; it must never be 100% again by accident.
    two_sided = sum(int(r["n_two_sided"]) for r in roll)
    assert 0 < two_sided < len(markets)


def test_partition_evaluators_require_exactly_their_legs():
    """A basket prices the whole outcome space or nothing.

    Both evaluators once ignored which markets they were handed: a three-leg partition
    priced from two quotes reported +$0.80, and a two-leg partition priced from the same
    leg twice reported +$0.60. Both packages pay zero in states the partition covers.
    """
    from kalshi_structure.relations import Partition, Quote
    p3 = Partition(legs=("A", "B", "C"), tiled=True, basis="t", exhaustiveness="explicit")
    two = [Quote("A", 0.09, 0.10, 100, 100), Quote("B", 0.09, 0.10, 100, 100)]
    assert p3.evaluate_buy_all(two) is None
    assert p3.evaluate_sell_all(two) is None

    p2 = Partition(legs=("A", "B"), tiled=True, basis="t", exhaustiveness="explicit")
    dupe = [Quote("A", 0.80, 0.81, 100, 100), Quote("A", 0.80, 0.81, 100, 100)]
    assert p2.evaluate_buy_all(dupe) is None
    assert p2.evaluate_sell_all(dupe) is None

    wrong = [Quote("A", 0.30, 0.31, 100, 100), Quote("Z", 0.60, 0.62, 100, 100)]
    assert p2.evaluate_buy_all(wrong) is None

    ok = [Quote("A", 0.30, 0.31, 100, 100), Quote("B", 0.60, 0.62, 100, 100)]
    assert p2.evaluate_buy_all(ok) is not None
    assert p2.evaluate_sell_all(ok) is not None


def test_deadline_grammar_covers_partial_dates():
    """Ladders mix full dates with month+year and bare months.

    A parser reading only full dates failed the majority vote on real ladders
    (FEDHIKE, KXALBUMRELEASEDATETRIPPIE) and classified them as entity menus.
    """
    assert parse_deadline("Before July 2026") == (2026, 7, 1)
    assert parse_deadline("Before June") == (0, 6, 1)     # year unstated
    assert parse_deadline("before September") == (0, 9, 1)


def test_threshold_grammar_tolerates_unit_glyphs():
    assert parse_threshold("79° or below") == ("", 79.0, "<=")
    assert parse_threshold("88° or above") == ("", 88.0, ">=")
    assert parse_threshold("$4/MTok or below") == ("", 4.0, "<=")


def test_tombstone_legs_do_not_sink_the_vote():
    """Placeholder legs carry no strike and must leave the denominator."""
    ladder = {"markets": [
        {"status": "finalized", "yes_sub_title": "Before June"},
        {"status": "finalized", "yes_sub_title": "Before August"},
        {"status": "inactive", "yes_sub_title": "DEACTIVATED"},
        {"status": "active", "yes_sub_title": "Before Sep 1, 2026"},
        {"status": "active", "yes_sub_title": "Before Oct 1, 2026"},
        {"status": "active", "yes_sub_title": "Before Nov 1, 2026"}]}
    assert classify_event(ladder) == "deadline"
