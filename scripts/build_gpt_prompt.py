#!/usr/bin/env python3
"""Assemble the prompt to paste into a ChatGPT Pro session that has the GitHub
connector authorised for this repository.

The split is deliberate: methodology, known traps and the audit protocol live in the
repo and are read by the model directly, so they never consume prompt budget and never
drift from what is committed. Only what the repo cannot contain -- contract text and
prices, which Kalshi's terms bar from redistribution -- is inlined.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from kalshi_structure.audit import pack_size_report
from kalshi_structure.universe import DEFAULT_DATA
import json

DATA = os.path.join(DEFAULT_DATA, "elections_politics")
pack = open(f"{DATA}/audit_pack_relations.txt").read()

PREAMBLE = """\
You are a derivatives settlement-rules auditor. Your judgement is being used to decide
whether machine-detected price relations on the Kalshi prediction exchange are genuine
settlement logic or artefacts. Be adversarial: your job is to break these relations, not
to confirm them.

STEP 1 — read the repository before answering anything.

Use the GitHub connector on the private repo `YichengYang-Ethan/kalshi-market-structure`
and read, in this order:

  docs/settlement-patterns.md   the constraint grammar, and what ~120,000 executable
                                checks across the whole exchange actually found
  docs/universe-inventory.md    the traded surface; in particular the finding that
                                violations of one logical family fall into at least two
                                populations that quoted spread cannot distinguish
  docs/taxonomy.md              why the category field is unusable, and why partition
                                exhaustiveness cannot be decided arithmetically
  docs/fee-model.md             the fee surface and its per-series exceptions
  src/kalshi_structure/relations.py   how a constraint is turned into an executable
                                package, with the failure modes recorded per family
  src/kalshi_structure/audit.py       the protocol you are operating under

These documents record mistakes already made and corrected in this work — a tolerance
bug that manufactured a false finding about settlement gaps, a parser that inferred
conjunction contracts from the word "and" and misclassified national teams, an
explanation about undiscovered quotes that the data then refuted. Do not re-derive
these, and do not repeat them. If you believe any conclusion in those documents is
wrong, say so explicitly and give your reasoning — that is more valuable than agreement.

If the connector cannot reach that repository — it is private and was created recently,
so it may not be inside your authorised scope — say so in one line and proceed anyway.
Everything required to adjudicate is inlined below; the repository supplies context and
prior corrections, not evidence. Do not stall, and do not substitute recalled knowledge
of the repo's contents for having read it.

STEP 2 — note what is deliberately absent.

No market data is committed to that repository, because Kalshi's terms prohibit
redistribution. Every contract text, quote, depth figure and traded flag you need is
inlined below and is measured, not asserted. Treat the numbers as given: do not
recompute fees, do not correct prices, and do not let a violated price argue for the
logic being sound or a consistent price argue against it. The one prior audit error
worth avoiding specifically: a static fee-schedule PDF was used to contradict the live
API about which series are zero-fee, and the API was right.

STEP 3 — adjudicate the audit pack that follows.

Follow its instructions exactly, including the two calibration anchors. Answer for every
family plus both anchors. If your verdict on an anchor disagrees with the note attached
to it, say so — a silent disagreement makes the rest of your verdicts unusable.

"""

out = PREAMBLE + "\n" + "=" * 98 + "\n\n" + pack
p = f"{DATA}/gpt_pro_prompt.txt"
open(p, "w").write(out)
print(f"wrote {p}")
print(json.dumps(pack_size_report(out), indent=1))
