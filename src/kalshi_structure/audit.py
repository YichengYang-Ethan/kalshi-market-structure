"""Generate audit packs for external review of settlement-logic relations.

The division of labour this implements:

============  ==========================================================  ==========
Layer         Work                                                        Done by
============  ==========================================================  ==========
enumerate     candidate pairs from ticker grammar and entity matching     machine
price         executable sides, per-series fees, depth                    machine
**generalise** collapse thousands of pairs into ~20 relation families     machine
**adjudicate** does the contract text make the implication exact?         **model**
verify        live re-pull before anything is believed                    machine
============  ==========================================================  ==========

Only the adjudication step needs a language model, and only once per family rather than
once per pair — a single verdict on ``KXMIDTERMMOV ⇒ winner`` governs 3,900 candidate
pairs. That is what keeps the request small enough to survive, and it is also the only
step where a model has an advantage: reading two contracts and deciding whether one
resolution condition strictly contains the other.

Two rules are enforced by construction:

1. **No facts the model could get wrong are delegated to it.** Fees, prices, depth and
   ticker joins are computed here and stated in the pack as given. A model that reads a
   stale fee schedule will contradict the live API — that happened, and the API won.
2. **Every pack carries calibration anchors** — one relation already established as
   exact and one already established as broken — so the reviewer's judgement can be
   checked against known answers in the same response.
"""
from __future__ import annotations

import json
import textwrap
from dataclasses import dataclass, field


@dataclass
class RelationSample:
    """One concrete instance of a family, with everything needed to adjudicate it."""
    a_ticker: str
    b_ticker: str
    a_subtitle: str
    b_subtitle: str
    a_rules: str
    b_rules: str
    a_quote: str
    b_quote: str
    a_traded: bool
    b_traded: bool
    a_early_close: str = ""
    b_early_close: str = ""
    note: str = ""


@dataclass
class RelationFamily:
    """A claimed settlement-logic relation covering many pairs."""
    name: str
    pattern: str
    claim: str                      # the price inequality asserted
    n_pairs: int
    samples: list[RelationSample] = field(default_factory=list)
    machine_findings: str = ""      # what the scanner already established
    suspected_failure_modes: tuple[str, ...] = ()


CALIBRATION = """\
CALIBRATION ANCHORS — two relations whose verdicts are already established. Adjudicate
them alongside the others and put them in your output. If your verdict on either
disagrees with the note below, say so explicitly and explain; a silent disagreement
means the rest of your verdicts cannot be trusted.

ANCHOR-EXACT — threshold-ladder nesting inside one event.
  "Republicans, 28+ pts" implies "Republicans, 26+ pts" in the same event.
  Established EXACT: both legs are generated from the same template over the same
  subject and share all postponement and void language, so no rule mismatch is possible.

ANCHOR-BROKEN — buy-all-YES on a soccer correct-score grid, e.g.
KXBRASILEIROSCORE-26AUG09FLAVIT (30 legs, mutually_exclusive true).
  Legs enumerate scorelines up to 5 goals per side but cover only 17 of the 36 cells in
  the 0-5 x 0-5 grid: 4-4, 5-3, 5-4, 5-5, 3-5 and 4-5 are absent, and no scoreline of 6
  or more goals is listed at all. Established BROKEN as an exhaustive partition: a 4-4
  draw pays no leg, so the legs cannot sum to one despite the event being mutually
  exclusive. Mutual exclusivity bounds the sum from above and says nothing about
  whether any leg must pay.
"""

# A note on how this anchor was chosen, because the first one was wrong. The original
# ANCHOR-BROKEN used KXGREENLANDPRICE, on the reasoning that a $9.5B acquisition falls
# between the "$1B to $9B" and "$10B to $99B" legs. Its rules_secondary says "Values are
# rounded to the nearest $1 billion USD", so $9.5B rounds into a listed bucket and the
# partition is exhaustive after all. The anchor asserted a verdict that the contract text
# contradicts -- and because an anchor tells the reviewer the answer, it corrupts the
# calibration it exists to provide. Two lessons are now enforced above: an anchor must
# quote the contract text that decides it, and the same rule that applies to reviewers
# (never assert a settlement fact without the clause in hand) applies to whoever writes
# the pack.

INSTRUCTIONS = """\
YOUR TASK — adjudicate each relation family below on settlement logic alone.

For every family return exactly these fields:

  family        the name given
  verdict       EXACT | NEEDS-RULE-CHECK | BROKEN
                  EXACT            the contract text makes A's resolution condition a
                                   strict subset of B's in every state the contracts can
                                   reach
                  NEEDS-RULE-CHECK the implication holds in ordinary states but the text
                                   leaves a reachable state undetermined, or depends on
                                   a document not supplied here
                  BROKEN           a reachable state exists in which A resolves Yes and
                                   B resolves No
  basis         the specific clause that decides it, QUOTED from the rules text supplied.
                Do not paraphrase and do not cite a document that is not in this pack.
  failure_state if not EXACT: the concrete sequence of events that breaks it, in one or
                two sentences. Name what happens, not a category of risk.
  probability   your order-of-magnitude estimate for that state, as a probability per
                pair per cycle. Say "unquantifiable" if it is a legal or discretionary
                question rather than a physical one.
  confidence    high | medium | low, and what would raise it

RULES OF ENGAGEMENT

- Argue against the relation first. A family survives only if you cannot construct a
  failure state from the text supplied.
- The prices, fees, depth and traded flags below are measured, not claims. Do not
  re-derive them, do not correct them, and do not let them influence the settlement
  verdict — a violated price is not evidence that the logic is sound, and a consistent
  price is not evidence that it is.
- If two contracts settle at different times (one on a media call, one on an oath), say
  so under failure_state even when the final outcome must agree. Timing divergence is a
  real exposure, not a technicality.
- Where the supplied text is insufficient, answer NEEDS-RULE-CHECK and name the exact
  document and clause required. Do not fill the gap with recalled knowledge of how
  Kalshi contracts usually work.

Output plain structured text, one block per family. Do not produce a table.
"""


def _wrap(text: str, width: int = 96, indent: str = "    ") -> str:
    if not text:
        return f"{indent}(none)"
    return "\n".join(textwrap.fill(line, width=width, initial_indent=indent,
                                   subsequent_indent=indent)
                     for line in text.strip().splitlines() if line.strip())


def render_pack(families: list[RelationFamily], *, title: str,
                snapshot: str, fee_note: str) -> str:
    """Render a self-contained audit pack as plain text."""
    out: list[str] = []
    out.append(f"# {title}")
    out.append("")
    out.append(f"Snapshot: {snapshot}")
    out.append(f"Fee model (measured from the live API, authoritative): {fee_note}")
    out.append("")
    out.append(CALIBRATION)
    out.append(INSTRUCTIONS)
    out.append("=" * 98)
    out.append(f"{len(families)} RELATION FAMILIES")
    out.append("=" * 98)

    for i, fam in enumerate(families, start=1):
        out.append("")
        out.append(f"## FAMILY {i}: {fam.name}")
        out.append(f"   pattern      {fam.pattern}")
        out.append(f"   claim        {fam.claim}")
        out.append(f"   covers       {fam.n_pairs:,} candidate pairs")
        if fam.machine_findings:
            out.append("   measured:")
            out.append(_wrap(fam.machine_findings, indent="     "))
        if fam.suspected_failure_modes:
            out.append("   failure modes already suspected (confirm, refute or extend):")
            for m in fam.suspected_failure_modes:
                out.append(_wrap(f"- {m}", indent="     "))
        for j, s in enumerate(fam.samples, start=1):
            out.append("")
            out.append(f"   --- sample {j} ---")
            out.append(f"   A  {s.a_ticker}   [{s.a_subtitle}]")
            out.append(f"      quote {s.a_quote}   ever_traded={s.a_traded}")
            if s.a_early_close:
                out.append(f"      early close: {s.a_early_close}")
            out.append("      RULES:")
            out.append(_wrap(s.a_rules, indent="        "))
            out.append(f"   B  {s.b_ticker}   [{s.b_subtitle}]")
            out.append(f"      quote {s.b_quote}   ever_traded={s.b_traded}")
            if s.b_early_close:
                out.append(f"      early close: {s.b_early_close}")
            out.append("      RULES:")
            out.append(_wrap(s.b_rules, indent="        "))
            if s.note:
                out.append(f"   note: {s.note}")
    out.append("")
    out.append("=" * 98)
    out.append("END OF PACK — adjudicate all families above plus both calibration anchors.")
    return "\n".join(out)


def pack_size_report(pack: str) -> dict:
    """Rough size check. Web-interface submissions above roughly 30KB have failed."""
    n = len(pack)
    return {
        "chars": n,
        "approx_tokens": n // 4,
        "verdict": "ok" if n < 25_000 else ("large" if n < 40_000 else "split required"),
    }
