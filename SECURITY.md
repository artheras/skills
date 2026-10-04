# Security

These skills are instructions and scripts that AI agents follow on a user's
machine, so a flaw in one can become an action taken on someone's behalf. We
treat reports about them as security issues.

## Reporting a vulnerability

Please report privately through GitHub:
**https://github.com/artheras/skills/security/advisories/new**

Do not open a public issue for a vulnerability. Include the skill, the file and
line or commit, and what an agent or attacker could make it do.

We will acknowledge the report, agree on a fix and a disclosure date with you,
and credit you in the advisory unless you prefer otherwise.

## What counts

Especially:

- a skill that asks for, reads, stores or transmits a private key, seed phrase,
  wallet export, or credentials beyond what its policy declares;
- a script that executes code fetched from a source that can change after
  review (a pipe into a shell, an unpinned package, an install from a branch);
- a skill whose `skill-policy.json` understates what its scripts do — network
  access, writes, or command execution;
- a skill that can leak one client's data into another client's output
  (the logistics skills promise per-shipper isolation);
- a calculation that can be steered to a wrong amount without an error.

## Guarantees the repository enforces

`scripts/validate_catalog.py` runs in CI and fails if any skill pipes a
download into a shell, runs an unpinned `npx …@latest`, installs from a git
branch, or carries a package.json lifecycle script.

Skills that touch money or wallets — for example `stablecoin-settlement-audit`
— are read-only: they never need or accept a private key or seed phrase, and
they never sign or send a transaction.

## Releases

Directories that list these skills, such as solana.com/skills, link to a tagged
release rather than `main`. A listed skill changes only through a new tag,
which each directory reviews again.
