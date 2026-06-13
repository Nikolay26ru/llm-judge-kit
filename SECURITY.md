# Security Policy

## Supported versions

The latest released `0.1.x` line receives security fixes. Earlier versions are
not maintained — please upgrade to the newest release.

## Reporting a vulnerability

Please report security issues **privately** — do not open a public issue.

- Preferred: [open a private advisory](https://github.com/Nikolay26ru/llm-judge-kit/security/advisories/new)
  (repository → **Security** → **Report a vulnerability**).
- Alternatively, contact the maintainer via their
  [GitHub profile](https://github.com/Nikolay26ru).

Include reproduction steps and the affected version(s). You can expect an initial
response within a few days. Once a fix is ready it is released to PyPI, and you
will be credited unless you prefer to remain anonymous.

## Scope notes

`llm-judge-kit` sends prompts to whatever LLM provider you configure. Treat model
inputs and outputs as untrusted:

- The library parses model JSON defensively and validates/clamps judge scores to
  `[0, 1]` (rejecting non-finite values), so a malformed or adversarial model
  response cannot smuggle in an out-of-range score or crash a later render.
- You remain responsible for the data you send to third-party providers and for
  securing your API keys. Keys are read from the environment by the provider
  SDKs; the library never logs them.
