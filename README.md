# Arthera Skills

[![test](https://github.com/artherahq/skills/actions/workflows/test.yml/badge.svg)](https://github.com/artherahq/skills/actions/workflows/test.yml)

The skill catalog for **Aria Code** — Arthera's AI quant terminal. Each skill
packages one piece of research discipline (point-in-time data hygiene, backtest
trust gates, risk decomposition, strategy spec gates…) as instructions plus
runnable verification scripts that Aria loads dynamically when a task matches.
Maintained by [`artherahq`](https://github.com/artherahq).

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
| [`supply-chain-knowledge-graph`](skills/supply-chain-knowledge-graph) | Maps a company's dependency graph — upstream suppliers, downstream customers, competitors — instead of reading its financials in isolation, so that a shock reaching the target through a supplier is visible before it shows up in the target's own numbers. Expands two hops, then tests the graph for the two failure modes that make a dependency actually dangerous rather than merely present: a single supplier above 15% of COGS (concentration), and downstream customers facing demand destruction. Ships a stdlib-only harness (`scripts/supply_chain_mapper.py --demo`). |
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
| [`web-motion-design`](skills/web-motion-design) | The layer applied last, after the static UI already works: transitions, hover/press feedback, loading states, scroll reveals, page transitions. Opens from the asymmetry that makes motion different from every other design layer — a color is free to look at, a 600ms transition is 600ms the user cannot act — so every animation must buy back the time it spends by answering one of exactly four questions (where did this come from / where did it go / did my input register / is the system working). Anything answering none of them is decoration, which is the generic-AI-motion signature: `transition: all 0.3s ease` on everything, heroes fading up, cards staggering in for no reason. Carries the duration scale (100/150/200/300/400ms, chosen by distance and size rather than importance), the three direction-chosen easing curves (entrances decelerate, exits accelerate and run ~30% shorter, on-screen moves ease both ends), the compositor constraint (`transform`/`opacity` only — everything else forces layout, and `transition: all` silently animates properties you never intended), and `prefers-reduced-motion` as a medical accommodation where the right treatment is reduce-not-remove. Cutting animation is an explicit valid outcome — over-animation is the more common failure. Stores its scale in `ui-design-system`'s `design-tokens.json` under `motion` rather than a parallel config, so animation is validated alongside color and spacing. |
| [`minimal-editorial-exports`](skills/minimal-editorial-exports) | A second, deliberately restrained style for the one surface per document that's allowed to be quiet — a report cover page, a PPTX title slide, a standalone chart export, a Canva one-pager — never the dense report body itself. Heavy negative space around one focal point, one accent color tied to real signal meaning, restrained serif/monospace type, texture only where the export format can render it (HTML/PDF, not PPTX/DOCX). Names exactly where this plugs into Aria Code's own export pipeline (`report_generator.py`'s chart palette, `pdf_report.py`'s theme cover page, `report_exporters.py`'s PPTX/DOCX title slide, `canva_client.py`'s Autofill data). Ships a runnable gate (`scripts/exports_gate.py --demo`) that fails a dense cover carrying borrowed dashboard chrome and format-mismatched texture next to a corrected minimal-editorial compile of the same cover. |
| [`minimal-editorial-poster`](skills/minimal-editorial-poster) | Domain-agnostic sibling of `minimal-editorial-exports` — compiles a minimal zine/editorial poster prompt for a theme, sentence, or brief from any domain Aria Code touches (finance, real estate, or none at all), not just for styling Aria Code's own exports. Nine first-principles fields answered in order (canvas, attention geometry, anchor, anchor treatment, typography, color logic, texture, emotional temperature, hard avoids), a variation engine so a batch of posters doesn't compile to the same recipe, and an explicit negative-constraints list. Actually executes the compiled prompt when a backend is configured — local self-hosted SDXL-Turbo (`aria.report.generate_image_local`/`edit_image_local`, no API key) or OpenAI's `gpt-image-1` — choosing generate vs. edit from the Anchor field and an `img2img` `strength` value from ranges tuned against a real run (0.55 confirmed on an actual portrait: duotone + simplified background + texture all came through while the subject stayed recognizable). Falls back to prompt-only + a non-image brief when no backend is configured. Ships a runnable gate (`scripts/poster_gate.py --demo`) that reproduces a real commercial-travel-poster prompt failing next to the corrected minimal-editorial compile for the same photo, catching leaked hard-avoid terms, doubled saturated colors, and negative-space that isn't really 70%+. |

| [`short-form-video-editing`](skills/short-form-video-editing) | Converts approved footage, posters, charts, and image assets into a platform-ready short-form video delivery package: edit plan, captions, publish copy, verification metadata, music declaration, and a deterministic gate. Keeps the financial-publishing boundary explicit: no invented performance, named data sources, audit-ready review ownership, and a signed-off delivery manifest before release. |
| [`aria-music-direction`](skills/aria-music-direction) | Creates rights-aware music direction for ARIA media: no-music rationale or an original/licensed/commissioned/user-supplied cue declaration, concise cue brief, mix targets, territory and term, proof location, clearance status, and named release approval. Ships an offline gate that blocks incomplete or uncleared cue manifests while intentionally bundling no third-party audio. |

A third plugin, `realty-operations-skills`, covers operating-rights and
revenue-share property arrangements — a separate vertical, because verifying a
private operator's self-reported revenue is a different discipline from
analysing a listed company:

| Skill | What it does |
|---|---|
| [`operator-revenue-integrity`](skills/operator-revenue-integrity) | Verifies an operator's or tenant's self-reported revenue before it settles a revenue-share or guarantee. Rejects the check most people actually run — reconciling declared revenue against the operator's own POS — because POS, payment codes, and bookkeeping are all inside the counterparty's control, and an operator routing customers to a personal payment code produces records that are internally consistent and understated at once. Only signals the operator does not control count as evidence: utility meters, door-access and foot-traffic logs, delivery-platform settlements, inventory deliveries. Documents what each signal can and cannot establish plus its specific false-alarm modes (seasonal HVAC swings dominate the energy ratio; a wrong margin assumption moves inventory-implied revenue more than most real underreporting would). Orchestrates the `cashflow_verify`, `energy_anomaly`, `fulfillment_risk`, and `revenue_share` agents. |

A fourth plugin, `enterprise-operations-skills`, covers operating a company's
*own* internal systems through an agent rather than analysing an external
market. These read and act on internal systems of record — an incident tracker,
a contract repository, an ERP — so each one ends at a human approval gate
rather than at a conclusion:

| Skill | What it does |
|---|---|
| [`devops-incident-responder`](skills/devops-incident-responder) | Triages an IT incident from its own logs before touching anything: pulls the error record, names a root cause, then applies the narrowest remediation that clears it and writes the resolution back to the ticket. The only skill in this catalog whose declared workflow has non-reversible side effects on live infrastructure (service restart, ticket write-back), which is why its `skill-policy.json` declares `workspace_write` and approval-gated execution instead of the read-only default the other operations skills use. |
| [`enterprise-legal-audit`](skills/enterprise-legal-audit) | Scans a vendor contract or SLA for the clause classes a human reviewer is specifically looking for — unlimited liability, auto-renewal traps, termination asymmetry — rather than summarizing the document. Runs the algorithmic flags, then routes anything carrying a high-risk flag to human General Counsel sign-off instead of clearing it. Verdict gates (PASS/WARN/FAIL). No bundled scripts: depends entirely on the Enterprise Lakehouse & RAG MCP server being connected. |
| [`logistics-warehouse-audit`](skills/logistics-warehouse-audit) | Checks warehouse inventory health, inbound exceptions, and freight-forwarder sync latency against the ERP, in that order — sync health first, because an inbound-status answer read from a lagging feed is wrong in a way that looks fine. Surfaces SKUs below minimum stock and damaged/quantity-mismatch shipments. Replenishment is **draft-only**: the skill is required to state explicitly that human approval in the ERP frontend is what actually commits an order. |

A fifth plugin, `commerce-operations-skills`, covers running a cross-border
e-commerce operation through an agent — a seller's own marketplace listings,
stock, P&L, ad spend, and competitive landscape, rather than internal
IT/legal/warehouse systems. Every skill here drafts or recommends; exactly
one (`commerce-operations-agent`) is authorised to act, and only behind a
seller-controlled policy the Agent cannot enable itself:

| Skill | What it does |
|---|---|
| [`cross-listing`](skills/cross-listing) | Migrates a product listing from one marketplace to another (OZON ↔ Wildberries) as a validated draft. Normalizes into a canonical schema before touching either marketplace's own field names, maps categories with no best-guess fallback, carries dimensions/weight/certifications verbatim (an unknown value is reported unknown, never backfilled with a plausible number), and gates any price move beyond ±15% on explicit confirmation. Publish is structurally out of reach: `skill-policy.json` never lists a publish-capable tool, so the refusal isn't just prose — the skill has no way to call one. |
| [`inventory-planner`](skills/inventory-planner) | Turns current stock, sales velocity, and supplier lead time into a draft restock recommendation per SKU — days-of-cover against a reorder point, classified `ok`/`reorder_now`/`urgent`/`stockout`. The forecasting sibling of `logistics-warehouse-audit`: refuses to size a SKU with no sales-velocity estimate or no declared lead time rather than guess one, the same discipline `execution-position` applies to position sizing. Flags stock already in transit before suggesting more, and rounds a suggested order up to a declared MOQ with the rounding disclosed. Never sends or commits a purchase order — draft only. |
| [`profit-engine`](skills/profit-engine) | Rolls up revenue minus ten real cost buckets (COGS, platform commission, advertising, logistics, warehousing, returns, refunds, payment fees, penalties, FX impact, tax) into net profit per store, then decomposes a period-over-period profit change into a ranked bridge — answering "GMV grew 18% but profit fell 7%" with the actual driver (advertising spend, in the shipped demo) instead of a bare total. A store with any missing cost bucket never gets zero-filled: it's reported `profit_incomplete` with an upper bound, since a missing cost can only overstate profit, never understate it, and portfolio rollups exclude incomplete stores from the total rather than blending in an understated number. |
| [`ads-optimizer`](skills/ads-optimizer) | Turns campaign spend/revenue/orders and a seller-declared ACOS target into a bid recommendation — `recommend_pause`/`recommend_decrease_bid`/`recommend_increase_bid`/`no_action` — never an executed bid change. Checks zero-conversion campaigns before ACOS-based rules so "not converting" is never scored as merely inefficient, refuses to score a campaign below a minimum-spend threshold rather than judge it on noise, and caps every step size at a non-negotiable `max_step_pct`. No mutating ads tool is reachable from the skill at all — the refusal to execute is declared in `skill-policy.json`, not just written guidance. |
| [`competitor-monitor`](skills/competitor-monitor) | Reads a competitor's price, inventory-proxy, search rank, and review-velocity deltas against six named patterns (clearance push, aggressive ad push, stockout risk, price war, fading listing, restock recovery) — requiring at least two corroborating signals per match, and phrasing every result as "consistent with," never "is." A single moving number, or fewer than two available signals, is `no_clear_pattern` rather than a forced narrative. Ranks competitors by how much evidence corroborates a read, not by how dramatic a lone signal looks, and never calls a tool that changes the seller's own price, bid, or listing — the response is the next skill's or the seller's decision. |
| [`commerce-operations-agent`](skills/commerce-operations-agent) | The one skill in this catalog authorised to take a live marketplace action — publishing a validated Wildberries `cross-listing` draft, or cancelling eligible Wildberries FBS orders — and only because both are deny-by-default behind a seller-maintained automation policy the Agent cannot itself create, edit, or enable. Checks `commerce.automation.status` before either operation, generates a fresh idempotency key per new request (never per retry), and for cancellation requires explicit order IDs plus a fresh eligibility preflight — never a product title, fuzzy search, or inferred order. OZON stays draft-only here too, for the same reason `cross-listing` never fabricates a category mapping: no verified product-import adapter exists for it yet. |

## Install

Aria Code discovers the catalog through `ARIA_SKILLS_PATH` or a sibling
checkout and registers each skill as `plugin:skill`:

```bash
git clone https://github.com/artherahq/skills aria-skills
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
$quant-research-skills:supply-chain-knowledge-graph
$app-engineering-skills:industry-design-direction
$app-engineering-skills:ui-design-system
$app-engineering-skills:trading-ui-patterns
$app-engineering-skills:terminal-software-design
$app-engineering-skills:conversational-ui-restraint
$app-engineering-skills:ai-generated-ui-craft
$app-engineering-skills:ui-asset-sourcing
$app-engineering-skills:web-motion-design
$app-engineering-skills:minimal-editorial-exports
$app-engineering-skills:minimal-editorial-poster
$app-engineering-skills:short-form-video-editing
$app-engineering-skills:aria-music-direction
$realty-operations-skills:operator-revenue-integrity
$enterprise-operations-skills:devops-incident-responder
$enterprise-operations-skills:enterprise-legal-audit
$enterprise-operations-skills:logistics-warehouse-audit
$commerce-operations-skills:cross-listing
$commerce-operations-skills:inventory-planner
$commerce-operations-skills:profit-engine
$commerce-operations-skills:ads-optimizer
$commerce-operations-skills:competitor-monitor
$commerce-operations-skills:commerce-operations-agent
```

Inside Aria Code:

- `/skills doctor` verifies catalog integrity and declared permissions.
- `/skills trace` shows why a skill was selected or blocked.

The repo doubles as a standard plugin marketplace (`artherahq/skills`), so any
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
