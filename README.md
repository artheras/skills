# Arthera Skills

[![test](https://github.com/artheras/skills/actions/workflows/test.yml/badge.svg)](https://github.com/artheras/skills/actions/workflows/test.yml)

The skill catalog for **Aria Code** — Arthera's AI quant terminal. Each skill
packages one piece of research discipline (point-in-time data hygiene, backtest
trust gates, risk decomposition, strategy spec gates…) as instructions plus
runnable verification scripts that Aria loads dynamically when a task matches.
Maintained by [`artheras`](https://github.com/artheras).

The catalog uses the open Agent Skills layout — a flat `skills/` directory, a
`spec/` describing the format, a `template/` for new skills, and a plugin
`marketplace.json` — so the same skills also run in any Agent-Skills-compatible
runtime. Aria Code is the first-class consumer: its portable skill loader
verifies the catalog against `skills.lock.json` before anything executes.

> [!IMPORTANT]
> **Nothing in this repository constitutes investment, legal, tax, or
> accounting advice.** These skills produce analyst work product — factor
> studies, backtest validations, risk decompositions, strategy specs, research
> notes — for review by a qualified professional. They do not make investment
> recommendations and they do not execute trades: `execution-position` emits
> paper-only order intents and fails mechanically on any live-execution path.
> Every output is staged for human sign-off.
>
> A PASS verdict from any gate in this catalog means the declared checks ran
> and passed on the inputs you supplied — it is not a claim that a strategy is
> profitable, that a backtest will generalize, or that a risk model captures
> your actual exposure. Validation gates catch known failure modes; they cannot
> certify an unknown one.
>
> You are responsible for verifying outputs and for compliance with the laws
> and regulations that apply to you or your firm. Provided as-is, without
> warranty of any kind — see [LICENSE](LICENSE).

## Skills

| Skill | What it does |
|---|---|
| [`point-in-time-research`](skills/point-in-time-research) | Enforces point-in-time data discipline when backtesting factors or strategies. Catches the three silent leaks (period-end dating, latest-value overwrite, same-session execution), quantifies the distortion with a four-variant A–D information-set comparison, and runs the validation gauntlet. Ships a runnable harness (`scripts/information_set_compare.py --demo`). |
| [`backtest-validation`](skills/backtest-validation) | Validates whether a backtest is trustworthy before any conclusion: honest metric set, turnover cost ladder, chronological IS/OOS split, stationary-bootstrap Sharpe CI, and the Deflated Sharpe Ratio against disclosed trials. Verdict gates (PASS/WARN/FAIL) with a runnable harness (`scripts/validation_gauntlet.py --demo`). |
| [`compliance-audit-trail`](skills/compliance-audit-trail) | Validates a model/strategy governance manifest before it reaches a counterparty doing real due diligence: every capability claim needs an evidence pointer, every "production" asset must have actually cleared its declared gates, every risk control must be verified to trigger (not just present in the code), a persisted audit trail is required, and an empty limitations list is itself a flag. Verdict gates (PASS/WARN/FAIL) with a runnable harness (`scripts/governance_manifest_gate.py --demo`). |
| [`multiple-testing-correction`](skills/multiple-testing-correction) | Corrects for multiple hypothesis testing before calling any factor, sub-period, or parameter-sweep result significant — Bonferroni and Benjamini-Hochberg FDR, plus a Fundamental Law of Active Management (Grinold 1989) breadth-illusion check for when claimed "independent" bets are actually correlated ones. Verdict gates (PASS/WARN/FAIL) with a runnable harness (`scripts/multiplicity_gate.py --demo`). |
| [`gamma-exposure`](skills/gamma-exposure) | Computes Gamma Exposure (GEX) — options-dealer hedging pressure inferred from open interest and implied volatility — with the standard Black-Scholes/sign-convention methodology, then audits the report before it's shared: dealer-assumption and coverage disclosures required, summary numbers must match the per-strike detail, regime label must match the total's sign. Verdict gates (PASS/WARN/FAIL) with a runnable harness (`scripts/gex_gate.py --demo`) that reproduces a one-character sign bug silently flipping a regime call. |
| [`risk-assessment`](skills/risk-assessment) | Decomposes portfolio/strategy risk from its actual history: VaR/CVaR with Cornish–Fisher tail adjustment, drawdown, concentration (effective N), diversification illusion via pairwise correlation, historical worst windows, and labeled linear beta shocks. Flags → risk level with mandatory disclosures; runnable harness (`scripts/risk_profile.py --demo`). |
| [`factor-research`](skills/factor-research) | Judges whether a cross-sectional factor genuinely predicts returns: per-period rank IC/IR/t-stat, decay across horizons, quantile monotonicity, sub-period sign-flip detection, and turnover via rank autocorrelation. Verdict routes survivors to backtest-validation; runnable harness (`scripts/factor_evaluate.py --demo`). |
| [`strategy-generation`](skills/strategy-generation) | Turns trading ideas into disciplined specs and implementations through a six-stage pipeline with three executable gates: a spec validator (hard risk controls, cost assumption, overfit preflight, forbidden-claim scan, honesty ledger for tried variants), then backtest-validation, then risk-assessment. Deploy advice caps at paper trading (`scripts/validate_strategy_spec.py --demo`). |
| [`portfolio-optimization`](skills/portfolio-optimization) | Estimation-robust weights with no expected-return inputs: inverse vol, long-only min variance, ERC risk parity, and inline HRP — plus a walk-forward `compare` mode that reports honestly when the optimizer fails to beat equal weight out-of-sample. Disclosed covariance shrinkage; weights ship with risk contributions (`scripts/optimize_portfolio.py --demo`). |
| [`execution-position`](skills/execution-position) | The pre-trade gate: sizes a signal (vol-target, or fractional Kelly only from a declared edge, hard-capped at 0.25), checks position/gross/cash/liquidity limits and stop-distance sanity, estimates costs, and emits paper-only order intents — live execution fails mechanically (`scripts/position_gate.py --demo`). |
| [`equity-research-report`](skills/equity-research-report) | Produces comprehensive equity reports through an auditable plan, normalized evidence bundle, specialist agents, deterministic fallbacks, critic pass, and executable completion gates. |

The `quant-research-skills` plugin above is the research pipeline. A second
plugin, `app-engineering-skills`, helps the user build apps to their own
standards:

| Skill | What it does |
|---|---|
| [`industry-design-direction`](skills/industry-design-direction) | The step *before* `ui-design-system`: choosing a direction rather than enforcing one. Answers "what should a dental clinic / restaurant / fintech app actually look like" from 95 industry profiles, 57 defined styles, 96 six-role palettes, 57 Google-Fonts pairings, and 30 landing-page structures — each industry carrying the constraint it most often gets wrong (accessibility mandatory for healthcare, trust signals for finance, visuals-first for portfolio). Exists because the failure mode it targets is not bad taste but *absent* taste: the same purple-gradient/Inter/hero-features-CTA default applied identically to a metal fabricator and an NFT marketplace. Every palette's body-text-on-background ratio was computed with the WCAG relative-luminance formula and clears AA — and the skill says plainly that this is the only pair verified, so CTA-label contrast stays the reader's job. Naming a style is not enough — the style library defines each one including its **"do not use for"** line (glassmorphism over low-contrast backgrounds, neumorphism where accessibility is required), because a style that is only named collapses back into whatever the model already assumed it meant. Ships a data-integrity gate (`scripts/verify_contrast.py`) that re-derives all 96 printed contrast ratios from their hex values and catches drift if the reference file is ever hand-edited after the fact. |
| [`ui-design-system`](skills/ui-design-system) | Helps the user establish and enforce **their own** design system: freezes their palette/type/radius/spacing choices into a portable `design-tokens.json`, validates it objectively (WCAG contrast, monotonic scales), then lints generated UI (SwiftUI/CSS/RN/Flutter) for color and radius literals that drift off *their* tokens. Taste stays the user's; consistency and accessibility are enforced by script. No house style of its own — runnable harnesses (`scripts/design_tokens.py --demo`, `scripts/design_lint.py --demo`). |
| [`trading-ui-patterns`](skills/trading-ui-patterns) | The opposite of `ui-design-system`: this one *does* have a house style — three of them. Encodes X (timeline post, action bar), TradingView (watchlist row, technical rating gauge), and Trading212 (order ticket, holdings row) component conventions, then audits a component manifest against the claimed pattern's checklist. Catches the market-convention bug that looks completely fine at a glance: red/green direction color hardcoded from one market (US) silently rendering backwards on another (CN/TW), the same failure shape as a sign-convention flip in a quant computation — runnable harness (`scripts/pattern_audit.py --demo`). |
| [`terminal-software-design`](skills/terminal-software-design) | Neither of the above two — this is the density/composition/native-chrome discipline that applies to terminals, IDEs, and dashboards regardless of whether you're also freezing tokens or matching a reference product. Covers why density is correct (not a compromise) in a working tool, semantic-vs-brand color, tabular numeric alignment, keyboard-first interaction, sidebar/popover/segmented-toggle failure modes, and Electron-specific pitfalls (native window background bleeding at theme boundaries, traffic-light centering). Four real before/after bugs from a production trading terminal, cross-referenced from each section. Pure reference, no scripts — every file is self-contained prose that works pasted into any assistant, not only inside this harness. |
| [`conversational-ui-restraint`](skills/conversational-ui-restraint) | The opposite instinct from `terminal-software-design`: for chat/copilot interfaces, restraint is correct, not density — the UI should disappear and the content (prose) should be what's remembered. Distills the actual discipline behind ChatGPT/Claude/Codex-style interfaces (not their internal tooling, which isn't knowable from outside — this is reverse-engineered from observable shipped design): near-monochrome color reserved for signal, content-over-chrome visual weight, one icon language, motion that communicates real state rather than decorates, progressive disclosure into a side canvas instead of bloating the message stream, and coding-agent-specific diff/collapse conventions. Pure reference, no scripts. |
| [`ai-generated-ui-craft`](skills/ai-generated-ui-craft) | Orthogonal to both of the above — not a UI category, but the generation-time self-critique process that separates a considered AI-built design from a templated one. Names the actual cliché cluster AI-generated UI falls into by default (warm-cream-serif-terracotta, purple-gradient hero, Inter-as-safe-font, emoji section markers, rounded-lg everywhere) and gives the process that avoids it: ground every choice in the specific subject, honor an existing design system before inventing a new one, choose neutrals/type deliberately rather than defaulting to them, design both themes with equal care, spend boldness in exactly one place, and run an explicit self-critique pass ("would this same plan show up on an unrelated project?") before shipping. Pure reference, no scripts. |
| [`ui-asset-sourcing`](skills/ui-asset-sourcing) | The step after a direction exists and before the boxes are filled: icons, imagery, logos, placeholder content. Targets two failure modes that are visible instantly and both come from *recalling* instead of *fetching* — invented SVG path data (a "Stripe logo" emitted from memory renders as a blob) and emoji standing in for interface icons. Names which icon set suits which aesthetic (Lucide/Heroicons/Phosphor/Tabler/Material, Simple Icons for real brand marks) and insists on import-by-name over hand-written paths. For imagery it maps style direction to imagery *kind* — the wrong kind being a bigger error than a mediocre execution of the right one — and gives prompt patterns that carry the chosen palette's hex values into Aria Code's own generators (`aria.report.generate_image_local` free/local, `aria.report.generate_image` paid), including where each backend actually fails (SDXL-Turbo cannot render legible text). Draws a hard line at generated people, places, and brand marks presented as real. Ships a lint (`scripts/asset_lint.py`) for the three mechanically-checkable gate items — emoji-as-icon, uncited long SVG path data, mixed icon sets — separate from `ui-design-system`'s token-conformance linter, plus a real fetcher (`scripts/fetch_icon.py`) that pulls actual SVG source from Lucide/Heroicons/Tabler/Phosphor/Simple Icons' published registries instead of an icon being hand-recalled, validating the response actually parses as SVG rather than trusting a 200 status alone. |
| [`minimal-editorial-exports`](skills/minimal-editorial-exports) | A second, deliberately restrained style for the one surface per document that's allowed to be quiet — a report cover page, a PPTX title slide, a standalone chart export, a Canva one-pager — never the dense report body itself. Heavy negative space around one focal point, one accent color tied to real signal meaning, restrained serif/monospace type, texture only where the export format can render it (HTML/PDF, not PPTX/DOCX). Names exactly where this plugs into Aria Code's own export pipeline (`report_generator.py`'s chart palette, `pdf_report.py`'s theme cover page, `report_exporters.py`'s PPTX/DOCX title slide, `canva_client.py`'s Autofill data). Ships a runnable gate (`scripts/exports_gate.py --demo`) that fails a dense cover carrying borrowed dashboard chrome and format-mismatched texture next to a corrected minimal-editorial compile of the same cover. |
| [`minimal-editorial-poster`](skills/minimal-editorial-poster) | Domain-agnostic sibling of `minimal-editorial-exports` — compiles a minimal zine/editorial poster prompt for a theme, sentence, or brief from any domain Aria Code touches (finance, real estate, or none at all), not just for styling Aria Code's own exports. Nine first-principles fields answered in order (canvas, attention geometry, anchor, anchor treatment, typography, color logic, texture, emotional temperature, hard avoids), a variation engine so a batch of posters doesn't compile to the same recipe, and an explicit negative-constraints list. Actually executes the compiled prompt when a backend is configured — local self-hosted SDXL-Turbo (`aria.report.generate_image_local`/`edit_image_local`, no API key) or OpenAI's `gpt-image-1` — choosing generate vs. edit from the Anchor field and an `img2img` `strength` value from ranges tuned against a real run (0.55 confirmed on an actual portrait: duotone + simplified background + texture all came through while the subject stayed recognizable). Falls back to prompt-only + a non-image brief when no backend is configured. Ships a runnable gate (`scripts/poster_gate.py --demo`) that reproduces a real commercial-travel-poster prompt failing next to the corrected minimal-editorial compile for the same photo, catching leaked hard-avoid terms, doubled saturated colors, and negative-space that isn't really 70%+. |
| [`short-form-video-editing`](skills/short-form-video-editing) | Turns approved footage, posters, charts and image assets into a platform-ready short-form video package — edit plan, captions, publish copy and a delivery manifest — with platform specs, asset provenance and finance-content rules in its references. Prepares the package; it does not publish, handle account credentials, or invent rights for a source asset. Ships a delivery gate (`scripts/video_delivery_gate.py --manifest delivery.json`) that validates the manifest against `assets/delivery-manifest.schema.json` before release. |

A third plugin, `realty-operations-skills`, covers operating-rights and
revenue-share property arrangements — a separate vertical, because verifying a
private operator's self-reported revenue is a different discipline from
analysing a listed company:

| Skill | What it does |
|---|---|
| [`operator-revenue-integrity`](skills/operator-revenue-integrity) | Verifies an operator's or tenant's self-reported revenue before it settles a revenue-share or guarantee. Rejects the check most people actually run — reconciling declared revenue against the operator's own POS — because POS, payment codes, and bookkeeping are all inside the counterparty's control, and an operator routing customers to a personal payment code produces records that are internally consistent and understated at once. Only signals the operator does not control count as evidence: utility meters, door-access and foot-traffic logs, delivery-platform settlements, inventory deliveries. Documents what each signal can and cannot establish plus its specific false-alarm modes (seasonal HVAC swings dominate the energy ratio; a wrong margin assumption moves inventory-implied revenue more than most real underreporting would). Orchestrates the `cashflow_verify`, `energy_anomaly`, `fulfillment_risk`, and `revenue_share` agents. |

## Install

Aria Code discovers the catalog through `ARIA_SKILLS_PATH` or a sibling
checkout and registers each skill as `plugin:skill`:

```bash
git clone https://github.com/artheras/skills aria-skills
export ARIA_SKILLS_PATH=/path/to/aria-skills/skills
```

`ARIA_SKILLS_PATH` points at a directory that *contains* skill folders — the
`skills/` subdirectory, not the repository root. Pointing it at the root also
picks up `template/SKILL.md` as a skill named `your-skill-name`. Nothing
dangerous happens (it has no lock entry, and an unlocked skill can never
activate automatically) but it is noise you do not want in the catalog.

Cloning the repo as `aria-skills` next to `aria-code` needs no environment
variable at all — that sibling path is one of the defaults.

```text
$quant-research-skills:point-in-time-research
$quant-research-skills:equity-research-report
$quant-research-skills:backtest-validation
$quant-research-skills:compliance-audit-trail
$quant-research-skills:multiple-testing-correction
$quant-research-skills:gamma-exposure
$quant-research-skills:risk-assessment
$quant-research-skills:factor-research
$quant-research-skills:strategy-generation
$quant-research-skills:portfolio-optimization
$quant-research-skills:execution-position
$app-engineering-skills:industry-design-direction
$app-engineering-skills:ui-design-system
$app-engineering-skills:trading-ui-patterns
$app-engineering-skills:terminal-software-design
$app-engineering-skills:conversational-ui-restraint
$app-engineering-skills:ai-generated-ui-craft
$app-engineering-skills:ui-asset-sourcing
$app-engineering-skills:minimal-editorial-exports
$app-engineering-skills:minimal-editorial-poster
$app-engineering-skills:short-form-video-editing
$realty-operations-skills:operator-revenue-integrity
```

Inside Aria Code:

- `/skills doctor` verifies catalog integrity and declared permissions.
- `/skills trace` shows why a skill was selected or blocked.

The repo doubles as a standard plugin marketplace (`artheras/skills`), so any
Agent-Skills-compatible runtime can install the same catalog.

## Integrity And Permissions

- `.claude-plugin/skills.lock.json` pins each Skill tree to a SHA-256 digest.
- `skill-policy.json` declares tools, runtime permissions, and script policy.
- Bundled scripts are never pre-authorized; Aria's normal command approval still applies.
- Regenerate and verify the lock after changing a Skill:

```bash
python scripts/build_skill_lock.py
python scripts/build_skill_lock.py --check
```

## Layout

```
aria-skills/
├── .claude-plugin/
│   ├── marketplace.json     # installable marketplace metadata
│   └── skills.lock.json     # versioned content-integrity lock
├── skills/                  # every skill follows the same shape:
│   └── <skill-name>/
│       ├── SKILL.md         # triggering + workflow + guardrails
│       ├── skill-policy.json# declared tools / permissions / script policy
│       ├── references/      # methodology, thresholds, schemas
│       └── scripts/         # runnable harness or gate + its pytest suite
├── spec/                    # the SKILL.md format, briefly
├── scripts/                 # catalog integrity tooling (skills.lock builder)
└── template/                # scaffold for a new skill
```

Every skill ships an executable verifier with a `--demo` mode — the discipline
is enforced by scripts and exit codes, not by prose.

## Run the bundled harness

The point-in-time skill ships a self-contained comparison harness. Verify it
with no data:

```bash
cd skills/point-in-time-research/scripts
python information_set_compare.py --demo
```

It embeds a deliberate look-ahead edge and shows the earnings factor's alpha
collapse from ~72% (naive, period-end-dated, revised values) to ~0% under strict
point-in-time alignment.

Tests (pandas/numpy required; they skip cleanly where absent):

```bash
pytest skills/point-in-time-research/scripts/test_information_set_compare.py
```

## License

Apache-2.0. See [LICENSE](LICENSE).
