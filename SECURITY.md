# Security and public data handling

This repository is an experimental local Python library/CLI, not a hardened public
inference service. Do not infer authentication, tenant isolation, sandboxing, or
production readiness from the existence of controller budgets.

## Credentials and external data

Jev credentials are read from `TYPESAFE_API_KEY`, `~/.typesafe.ai/jev`, or an explicit
key-file path. Never commit or echo keys, put them in command arguments, attach
authorization headers to errors, or embed credentials in configuration/examples.
The Jev endpoint is fixed; do not forward credentials across redirects.

Jev mode sends the question, evidence, accepted text, and candidate text to TypeSafe.
Send only content permitted for that external evaluation. Generated text and model
scores are data, not permission to execute commands, bypass budgets, or publish.

Result traces contain prompts and output text. Publish only synthetic, appropriately
licensed public, or authorized sanitized data after reviewing the whole artifact.
Do not assume ignored local files, GitHub drafts, PRs, or CI logs are private.

## Failure and resource boundaries

Validate configuration and provider responses; preserve explicit rejection/error
states. A timed-out call can have reached the provider, so do not silently replay it
or report zero cost when usage is unknown. Bound generation, retries, context, and
API work at their owning layer; do not claim one limit covers every resource.
Keep remote model code disabled by default and review changes to model loading,
serialization, dependency pins, file output, and network destinations.

## Reporting a sensitive issue

Do not post credentials, private data, or exploitable details in a public issue.
Use GitHub's private vulnerability reporting for this repository **if enabled**,
or an established private maintainer channel. This document does not claim a
private reporting channel is configured. If no private path is available, ask for
one without disclosing sensitive details. Maintainers should arrange credential
rotation with the owner when exposure is confirmed; never copy the secret into
the incident record or publish a replacement key.
