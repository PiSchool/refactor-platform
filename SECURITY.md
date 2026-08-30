# Security Policy

## Supported versions

The project publishes a moving research branch rather than versioned security
releases. Security fixes are applied to the tip of `main`. Older commits and
forks are not supported.

## Reporting a vulnerability

Do **not** open a public issue for a suspected vulnerability or leaked secret.
Use GitHub's private **Report a vulnerability** flow on this repository. If
private vulnerability reporting is unavailable, contact a maintainer privately
and ask for a secure reporting channel, without including exploit details in a
public message.

Include, when safe:

- affected commit/version and deployment mode;
- impact and prerequisites;
- minimal reproduction steps;
- whether credentials or private repository data may be exposed;
- suggested mitigation, if known.

Maintainers should acknowledge a report, validate impact, coordinate a fix and
disclosure, and revoke exposed credentials before publishing details.

## Security model and deployment warning

Refactor Platform is designed for a trusted, single operator. It executes
autonomous coding agents, benchmark bootstrap code, project builds, and
test suites. These workloads can run arbitrary commands inside the backend
container and may access credentials passed to the agent.

The default operator application has **no built-in authentication or
authorization**. The demo lock screen is a visual introduction, not a security
boundary.

- do not expose the frontend or backend directly to the public internet;
- place remote deployments behind an authenticated reverse proxy, VPN, or
  equivalent access control with TLS;
- keep the backend bound to loopback unless a protected network requires
  otherwise;
- use dedicated, least-privilege provider and cloud credentials;
- never mount a Docker socket, host home directory, or broad cloud credentials
  into the backend;
- treat third-party plugins, benchmark data, target repositories, and imported
  run bundles as untrusted;
- protect and encrypt backups of the `retrieval-data` volume: S2 persists source
  chunks and embeddings from indexed repositories even after task workspaces are
  cleaned;
- review provider data-retention terms before sending proprietary code or
  prompts;
- avoid running this demo on a host that also stores unrelated sensitive data.

There is no supported internet-facing configuration. The dashboard and API bind
to loopback; reach them over an SSH tunnel, or put a reverse proxy providing TLS
and authentication in front of them. Authentication at the edge does not make
plugin loading or agent execution safe to expose: both run arbitrary code from
the benchmark's repositories and the model's replies. To publish results, export
the run and serve the archive.

Docker isolation is not a complete sandbox. The backend image
contains compilers, package managers, Git, Java runtimes, Node, and an agent CLI.

## Secret handling

- Secrets belong in protected environment configuration or a dedicated secret
  manager, never Git, the database, a tracker, screenshots, logs, or exports.
- `.env` is ignored; review commits to confirm they are clean.
- The backend's retrieval writer credential is never passed to the agent. MCP
  receives a distinct SELECT-only database role in private configuration that
  is excluded from exports. Do not expose the pgvector port or reuse either
  credential outside this deployment.
- Track credential ownership, purpose, storage reference, and rotation dates;
  do not track the secret value in a project-management tool.
- Redact tokens, private source, prompts, environment dumps, and provider headers
  before sharing diagnostics.
- If a secret is exposed, revoke/rotate it first, then remove it from current and
  historical artifacts as needed. Deleting only the latest file is insufficient.

## Dependency and data responsibility

Users are responsible for the licenses and security posture of model providers,
agent CLIs, downloaded benchmark datasets, target repositories, Maven/Gradle/npm
dependencies, and custom plugins. Bootstrap scripts download upstream material;
the MIT license for this repository does not relicense that material.