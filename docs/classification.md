# Classification of the Elections + Politics universe

Every one of the 1,092 series in the universe is assigned a research taxonomy by
`src/kalshi_structure/classify.py`, applied via `scripts/classify_universe.py`. Output:
`series_classification.csv` in the data directory.

## Why this is rule-based

The first attempt handed 1,092 series to language models in four batches for labelling.
All four stalled: each was being asked to emit 273 ten-field JSON objects, roughly 50k
tokens of structured output in one response. That was a design error, but the deeper
problem is that it was the wrong tool. Ticker grammar, `settlement_sources`, contract
template and close dates already determine most of the taxonomy deterministically. Rules
are reproducible, auditable, survive a re-fetch, and can be improved incrementally when
they miss — a one-off labelling pass is none of those things.

What rules genuinely cannot decide is left as `unknown` rather than filled with a
plausible guess, and coverage is reported per field so the residue is visible.

## Fields

| Field | Coverage | Derived from |
| --- | --- | --- |
| `cycle` | 100% | ticker year tokens, latest close date |
| `time_class` | 100% | series `frequency` + template |
| `subject_type` | 98.6% | derivative family, then template + title tokens |
| `resolution_authority` | 81.5% | `settlement_sources`, matched most-specific-first |
| `domain` | 72.2% | ordered ticker/title patterns |
| `geography` | 69.4% | ticker grammar, then title, then domain fallback |
| `derivative_family` / `is_derivative` | exact | ticker prefix |

`resolution_authority` is matched most-specific-first on purpose: a contract naming both
a state canvass and a wire service is *resolved* by the canvass and only *accelerated* by
media, so it classifies as `state_election_authority`. This field is what makes
correlated settlement risk visible — two contracts resolved by the same canvass share a
failure mode that two resolved by different authorities do not.

`geography` consults the ticker before the title, because titles are sometimes wrong:
`SENATELA-26` is titled "Kentucky Senate winner?" and settles on Kentucky, while
Louisiana's 2026 race is `KXSENATELA-26NOV`.

## What the universe is made of

304 series (28%) have no resolved domain, but they are **4.3% of volume** — the residue
is the long tail of one-off speculative contracts, not anything load-bearing. By volume:

| Domain | Series | Share of volume |
| --- | --- | --- |
| `us_primary` | 131 | 36.5% |
| `us_local_election` | 38 | 11.9% |
| `us_federal_legislative_election` | 172 | 9.5% |
| `geopolitics` | 51 | 8.4% |
| `us_state_election` | 89 | 8.3% |
| `us_federal_executive_election` | 11 | 7.7% |
| `personnel` | 73 | 5.2% |
| *unresolved* | 304 | 4.3% |
| `legislation` | 82 | 3.1% |
| everything else | 141 | 5.1% |

Primaries and nomination contests dominate — more than a third of all volume — while the
general-election machinery that generates most of the *listings* is a much smaller share
of the *trading*.

## The derivative surface

`is_derivative` marks series generated over a base contest rather than asking their own
question. This is where the exchange's listed volume and its traded volume diverge most:

| Family | Subject | Markets | Events traded | Lifetime volume |
| --- | --- | --- | --- | --- |
| `KXMIDTERMMOV` | vote margin | 3,939 | 448 / 522 | 1,691,746 |
| `KXMIDTERMVOTETURN` | turnout | 2,756 | **176 / 502** | **106,444** |
| `KXPRIMARYMOV` | vote margin | 105 | 10 / 10 | 642,776 |
| `KXVOTEPRIMARY` | vote share | 38 | 5 / 5 | 1,920,672 |
| `KXPRIMARYPLACE` | placement | 31 | 7 / 7 | 317,587 |
| `KXLAMOV` | vote margin | 10 | 2 / 2 | 4,976 |

The two midterm families are **6,695 markets — 49% of the entire universe by listing
count — and together traded 1.8 million contracts**, about 0.24% of the universe's
volume. `KXMIDTERMVOTETURN` in particular has 2,756 listed markets and roughly 106k
contracts of lifetime volume across them; two-thirds of its events have never traded at
all.

The primary-cycle derivatives are the opposite: small, fully traded, and reasonably
active. Whatever is true of one derivative family is not automatically true of another,
which is the practical reason `is_derivative` and the traded flags have to be carried
together.

## Known limitations

- The 304 unresolved domains are dominated by one-off thematic contracts
  (`KXCITRINI`, `KXNEWPOPE`, `KXFEDEND`). Each new pattern added to the rules is a
  judgement call about whether it generalises; the rules deliberately stop short of
  encoding one-offs.
- `resolution_authority` is `unknown` for 18.5% of series, mostly where
  `settlement_sources` names an organisation the patterns do not recognise. That list is
  the highest-value target for the next rule pass, since settlement authority is what
  groups correlated failure modes.
- Classification is at the **series** level. Events within a series occasionally differ
  (a series covering both a primary and a general), which this does not yet capture.
