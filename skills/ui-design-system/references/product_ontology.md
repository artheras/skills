# Product ontology and evidence before visual design

A coherent interface starts one level above tokens. Before choosing a color or
laying out a hero, establish what the product *is*, what it can do today, where
it is first being proven, and where it intends to go. When these layers are
collapsed, the most visible current use case accidentally becomes the brand.

## The four-layer brief

Write one plain sentence for each layer and keep the order stable:

1. **Enduring identity** — the idea that should still describe the product if
   its first market changes.
2. **Core capability** — the repeatable system or intelligence loop the
   product provides.
3. **Application domains** — where that capability is used. Mark the first
   mature domain separately from experiments and future domains.
4. **Surfaces** — the concrete apps, SDKs, consoles, or devices through which a
   person uses the capability.

Example structure (not a prescribed brand):

```text
Identity: A research and execution intelligence system.
Capability: Turns questions into evidence-linked, reproducible work.
Proven domain: Quantitative research.
Direction: The same loop across code, science, and other complex domains.
Surfaces: Assistant, code environment, terminal, mobile app, API.
```

The information architecture should normally follow identity and capability,
not list every application domain at the top level. Domains belong under a
research, solutions, or applications layer unless the user deliberately wants
a vertical product brand.

## Claim evidence states

Every product claim used in a public interface must have one of these states:

- **Shipped** — available to the intended user now. Link to the actual surface.
- **Demonstrated** — backed by a reproducible product demo or artifact. Show
  what was done, not a superlative.
- **Measured** — backed by a named metric, measurement method, and time window.
- **Directional** — an explicit product direction or roadmap theme. Phrase it
  as intent, not present capability.

Do not publish a number because it makes a proof strip look complete. Uptime,
latency, model accuracy, customers, assets covered, and research volume are
measured claims and require a source. If proof is unavailable, use a workflow,
artifact, architecture, or transparent product state instead.

## Page-job test

Before designing a page, state:

- primary audience;
- one job the page must complete;
- one action the visitor should take;
- proof inventory available for that action;
- non-goals and claims the page must not imply.

Reject sections that do not advance the page job or establish needed trust.
This usually produces fewer, stronger sections than a generic landing-page
template.

## Learning from open-source projects safely

Evaluate references at the component-system level, not by star count or visual
similarity alone. Record:

| Field | Required note |
| --- | --- |
| Source | Repository and exact path or package |
| License | License governing that path, not only the repository badge |
| Lesson | The interaction, architecture, token, or testing pattern learned |
| Adoption | Reimplement, depend on, or copy with attribution as permitted |
| Avoid | Brand expression, sample-app styling, or proprietary paths not used |

Prefer references that strengthen one of four layers: accessible primitives,
semantic tokens, component composition, or isolated documentation/testing.
Avoid installing a second component system when the project already has the
needed primitives; design-system quality comes from consistent semantics and
governance, not dependency count.

Never reproduce another company's logo, signature palette, typography,
illustrations, product copy, or distinctive page composition merely to reach
its perceived level of quality. Match rigor—hierarchy, restraint,
accessibility, proof, and consistency—while preserving the user's identity.
