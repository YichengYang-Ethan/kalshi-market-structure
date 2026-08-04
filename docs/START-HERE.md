# Start here

This repository maps every kind of relatedness between Kalshi markets and prices what
that map is worth. Pick your path:

## Path A — "I want to trade the arbitrage" → [layer1-arbitrage-guide.md](layer1-arbitrage-guide.md)

The verified settlement bindings: which relation families are real, under what
conditions, how to scan them, and the honest capacity answer (small — read it before
building anything).

## Path B — "I want to research the correlations" → [layer2-correlation-guide.md](layer2-correlation-guide.md)

The seven shared-driver classes where markets co-move without binding — lead-lag,
relative value, cross-hedging. Machine-readable pair universes ship in
[`data/layer2/`](../data/layer2/). This is the open research space.

## Path C — "I want to check whether any of this is true" → [audit-response.md](audit-response.md)

Four external adversarial audit rounds plus a 16-agent internal reality check, with
every finding verified or refuted and the corrections recorded in place. The credibility
record is the product; start with the round-four verdict.

## The three-sentence summary

1. **Binding (Layer 1):** ~28,000 independent rule-forced constraints exist; the market
   holds them tight — standing riskless capacity ≈ $0, transient exact arb ~$0.64 best
   observed, a millisecond-scale harvester already operates at the fast end.
2. **Shared drivers (Layer 2):** 1,555 same-game clusters, 505 same-race clusters,
   20 same-underlying window families, measured lead-lag of 3–8 days on the slow end —
   unpriced, and where the strategies are.
3. **Spurious (Layer 3):** 10+ documented look-alike relations with concrete refuting
   states — the do-not-trade list, and the QC gate every new relation must pass.
