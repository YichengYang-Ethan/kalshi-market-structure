#!/usr/bin/env python3
"""Assemble the relation-family audit pack from the inventory + rules text."""
import csv, json, os, re, sys
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from kalshi_structure.audit import RelationFamily, RelationSample, render_pack, pack_size_report
from kalshi_structure.universe import DEFAULT_DATA

DATA = os.path.join(DEFAULT_DATA, "elections_politics")
mk = {r['ticker']: r for r in csv.DictReader(open(f"{DATA}/markets.csv"))}
rules = {}
for line in open(f"{DATA}/rules.jsonl"):
    r = json.loads(line)
    rules[r['ticker']] = (r.get('rules_primary') or '', r.get('rules_secondary') or '')

def q(t):
    m = mk.get(t)
    if not m: return "n/a"
    return f"{m['yes_bid'] or '-'}/{m['yes_ask'] or '-'} (bid {m['bid_size']}, ask {m['ask_size']}, vol {m['volume']})"

def traded(t):
    return mk.get(t, {}).get('ever_traded') == 'True'

def early(t):
    return (mk.get(t, {}).get('early_close_condition') or '')[:150]

def sample(a, b, note=""):
    ra, rb = rules.get(a, ('', '')), rules.get(b, ('', ''))
    return RelationSample(
        a_ticker=a, b_ticker=b,
        a_subtitle=mk.get(a, {}).get('yes_sub_title', '?'),
        b_subtitle=mk.get(b, {}).get('yes_sub_title', '?'),
        a_rules=(ra[0] + ("\n" + ra[1] if ra[1] else "")).strip(),
        b_rules=(rb[0] + ("\n" + rb[1] if rb[1] else "")).strip(),
        a_quote=q(a), b_quote=q(b), a_traded=traded(a), b_traded=traded(b),
        a_early_close=early(a), b_early_close=early(b), note=note)

fams = [
 RelationFamily(
   name="margin ladder implies party winner",
   pattern="KXMIDTERMMOV-<race><party>-P<n>  =>  KXHOUSERACE-<race>-<party> / SENATE<ST>-26-<party> / GOVPARTY<ST>-26-<party>",
   claim="P(party wins by >= n points) <= P(party holds the seat)",
   n_pairs=3900,
   machine_findings=("Scanned 3,900 pairs on the 2026-08-02 snapshot: 14 gross violations, 9 surviving "
     "per-series taker fees, ~$16 total at the touch. Largest is KXMIDTERMMOV-TX34R-P2 at +4.29c/contract, "
     "whose derivative leg has ZERO lifetime volume. Other violated pairs sit on legs that have traded "
     "(OH-07: 7,193 contracts, active within 24h), so the violations are not a single population. "
     "Two ladders resolve on 'the first round' of a runoff state and were excluded from the scan."),
   suspected_failure_modes=(
     "The margin contract resolves on the certified election result; the winner contract resolves on the "
     "party of the member sworn in. Death, resignation, disqualification or refusal to serve between "
     "those two moments, followed by a special election won by the other party, separates them.",
     "Fusion voting: a candidate may appear on several party lines, so the party credited with the win "
     "and the formal party membership of the person sworn in need not be the same.",
     "House winner markets carry accelerated determination on media consensus while Senate markets state "
     "early close follows the swearing in, so the two legs of one package can settle weeks apart."),
   samples=[sample("KXMIDTERMMOV-TX34R-P2", "HOUSETX34-26-R",
                   "largest violation on the exchange; the margin leg has never traded"),
            sample("KXMIDTERMMOV-OH07R-P1", "KXHOUSERACE-OH07-26-R",
                   "violated on a leg that HAS traded and was active within 24h")]),
 RelationFamily(
   name="specific territory acquisition implies any territory acquisition",
   pattern="KXGREENTERRITORY-29  =>  KXUSAEXPANDTERRITORY-29JAN21 (deadlines matched exactly)",
   claim="P(US acquires any part of Greenland by T) <= P(US gains control of any new territory by T)",
   n_pairs=1,
   machine_findings=("Live-verified 2026-08-01 and again 2026-08-02: specific leg bid 0.25 against general "
     "leg ask 0.22, gross +3c, +0.49c after fees. Both legs trade actively (2.8M and 86k contracts). "
     "Deadlines are identical to the second."),
   suspected_failure_modes=(
     "The two contracts use different verbs: one says 'acquires any part of', the other 'gains control of "
     "any territory outside its sovereignty'. A lease, basing agreement or compact might satisfy one and "
     "not the other, in either direction.",),
   samples=[sample("KXGREENTERRITORY-29", "KXUSAEXPANDTERRITORY-29JAN21")]),
 RelationFamily(
   name="presidential departure routes are subsets of leaving office",
   pattern="KXTRUMPRESIGN / KXTRUMPREMOVE  =>  KXTRUMPOUT27-27-JAN2029",
   claim="P(resigns) + P(removed by conviction) <= P(leaves office before 2029-01-20), if the routes are exclusive",
   n_pairs=3,
   machine_findings=("Selling both route legs and buying the OUT leg showed roughly +2.7c net on ~950 "
     "contracts at the touch. All three legs trade actively."),
   suspected_failure_modes=(
     "Whether resignation and Senate conviction are mutually exclusive turns on whether the Senate may "
     "convict a former officeholder; the secondary rules appear to require the subject to be sitting on "
     "the day of the vote, which would make them exclusive.",
     "Death is excluded from the OUT contract and handled by a last-price mechanism with committee "
     "discretion, leaving the long-OUT leg's payoff undefined in that state."),
   samples=[sample("KXTRUMPRESIGN", "KXTRUMPOUT27-27-JAN2029"),
            sample("KXTRUMPREMOVE", "KXTRUMPOUT27-27-JAN2029")]),
]
# drop samples whose rules text is missing so the pack never ships an empty contract
for f in fams:
    f.samples = [s for s in f.samples if s.a_rules and s.b_rules]
fams = [f for f in fams if f.samples]

pack = render_pack(fams,
    title="Kalshi Elections + Politics — settlement-logic relation audit",
    snapshot="2026-08-02 census; prices re-verified live 2026-08-02",
    fee_note="taker = fee_multiplier x 0.07 x P x (1-P) per contract per leg; maker = 0 on every "
             "series in this pack; no settlement fee. Multipliers resolved per series from /series.")
out = f"{DATA}/audit_pack_relations.txt"
open(out, "w").write(pack)
print(f"wrote {out}")
print(json.dumps(pack_size_report(pack), indent=1))
print(f"families: {len(fams)}, samples: {sum(len(f.samples) for f in fams)}")
