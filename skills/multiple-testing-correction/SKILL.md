---
name: multiple-testing-correction
description: >-
  Correct for multiple hypothesis testing before calling any factor,
  sub-period, or parameter-sweep result significant — and check whether a
  claimed set of independent signals or bets is actually a smaller number of
  correlated ones wearing a disguise. Trigger for "测了8个因子哪个显著",
  "筛选因子", "factor screen", "parameter sweep", "which of these signals is
  real", "p-hacking", "data snooping", "统计显著性", "breadth illusion",
  "effective breadth", "多重检验", "这些信号真的独立吗", "multiple testing
  correction", or whenever the user has run more than one significance test in
  a batch and is about to act on the ones that passed. Also trigger when a
  Sharpe/IR target is being justified by citing a number of supposedly
  independent bets, signals, or symbols — that count needs a correlation check
  before it goes into any Information Ratio math. Pair with
  backtest-validation: that skill’s Deflated Sharpe Ratio is this same
  correction applied to the single case of picking the best strategy variant
  out of N backtested; this skill is the general case for any batch of
  hypothesis tests, plus the separate breadth-illusion check neither skill
  otherwise covers. Do NOT trigger for a single, pre-specified test with no
  batch and no breadth claim — correcting one test against itself is a no-op.
---

# Multiple Testing Correction

Every hypothesis test carries a false-positive rate at its stated confidence
level — run enough of them and false positives arrive on schedule, not by bad
luck. Screen 30 factors at the conventional `|t| >= 2` (~95% single-test
confidence) and roughly 1-2 will look "significant" even if every one of them
is pure noise, purely from running 30 tests. Nobody needs to be dishonest for
this to happen; the batch size does it on its own. The same arithmetic error
shows up one level up: claim N "independent" signals or symbols and the
Fundamental Law of Active Management (Grinold, 1989) says skill scales with
`sqrt(N)` — but if those N things actually share high pairwise correlation
(same model family, same data source, same market regime), the *effective*
N is far smaller, and the implied Information Ratio was never really there.

## The two failure modes this skill catches

1. **Uncorrected batch significance.** A naive per-test threshold (`|t| >= 2`,
   `p < 0.05`) does not control the batch's error rate. Bonferroni controls
   the probability of *any* false positive in the batch (conservative);
   Benjamini-Hochberg (BH/FDR) controls the *expected proportion* of false
   positives among what gets called significant (the more common choice in
   modern quant research — the same logic behind the Deflated Sharpe Ratio).
2. **Breadth illusion.** A count of "independent" bets that are actually
   correlated inflates the Fundamental Law's IR estimate. `N` nominal bets at
   average pairwise correlation `rho` behave like
   `N / (1 + (N-1)*rho)` effective bets — at `rho=0.7` and `N=20`, that's
   ~1.4 effective bets, not 20.

## Workflow

1. Collect every test actually run in the batch — not just the ones that
   looked interesting. The batch size (`n`) *is* the correction; leaving out
   the tests that failed and only reporting the survivors defeats the whole
   point, the same way undisclosed trials defeat the Deflated Sharpe Ratio in
   `backtest-validation`.
2. For each test, get the t-statistic and the sample size (or degrees of
   freedom) that produced it.
3. Run the gate:
   `python scripts/multiplicity_gate.py --tests tests.json --alpha 0.05`
   where `tests.json` is `{"name": {"t_stat": float, "n_periods": int}, ...}`
   — one entry per hypothesis actually tested. With no data at hand, show the
   mechanics with `--demo`.
4. If a breadth/IR claim is also being made, add
   `--ic <avg information coefficient> --n-bets <N> --avg-corr <rho>` to the
   same call (or call it standalone with just those three flags) to check the
   Fundamental-Law breadth illusion independently of the correction above.
5. Report the **BH-FDR survivor set**, not the naive-significant set, as "what
   passed." Bonferroni's stricter survivor set is worth stating alongside it
   when the user needs the conservative answer (e.g. before capital
   deployment). Never report a factor as significant because it cleared the
   naive threshold alone.
6. Completion gate: a factor/variant is only "significant" in the final
   writeup if it is in the BH-FDR (or stricter) survivor set. On a
   `significance_evaporates` FAIL — naive flagged some, corrected keeps
   none — the correct deliverable is "this batch shows no evidence of a real
   effect at this batch size," which is a valid, useful research result, not
   a failure to find something.
7. If breadth was checked and flagged `breadth_illusion`, report the
   *effective*-breadth Information Ratio, not the nominal one, in any
   forward-looking claim.

## Guardrails

- No "N of M factors were significant" claim using the naive per-test
  threshold when M > 1. Correct first.
- No citing a Fundamental-Law IR without disclosing the correlation
  assumption behind the breadth number that produced it.
- Both checks require honest inputs the skill cannot verify on its own: the
  full test batch (not a cherry-picked subset) and a real, not assumed-away,
  correlation estimate for the breadth check. Say so when either is
  unavailable rather than defaulting silently to "independent."
- Missing scipy degrades to a normal approximation for the p-value (accurate
  once `n_periods` is reasonably large) rather than failing — but the CLI
  says so; don't silently treat it as exact for small samples.

## Bundled resources

- `scripts/multiplicity_gate.py` — Bonferroni + BH-FDR correction and the
  breadth-illusion check, in one gate with a PASS/WARN/FAIL verdict.
  `--demo` runs both scenarios with synthetic data and no dependencies beyond
  numpy/scipy (skips cleanly if absent).
- `references/methodology.md` — the exact formulas, when to prefer Bonferroni
  over BH-FDR, and how this relates to `backtest-validation`'s Deflated
  Sharpe Ratio and `risk-assessment`'s effective-N diversification check.
