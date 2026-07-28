# Support

## Documentation first

- Installation and remote hosts: [Deployment](docs/deployment.md)
- Provider and runtime settings: [Configuration](docs/configuration.md)
- Dashboard workflow: [Operator guide](docs/user-guide.md)
- Common failures: [Troubleshooting](docs/troubleshooting.md)
- Evaluation semantics: [Evaluation](docs/evaluation.md)

## Ask a question or report a bug

Use this repository's GitHub issue templates. Before posting:

1. search existing issues;
2. reproduce on the tip of `main`;
3. reduce the case to one benchmark task where possible;
4. redact credentials, private source, prompts, provider headers, and private
   artifact content.

A useful bug report includes the commit, operating system, Docker and Compose
versions, benchmark, setup, model identifier, expected behavior, actual
behavior, reproduction steps, and a short redacted log excerpt.

Model quality variance and a benchmark task failing its checks are not
necessarily platform bugs. Report a platform bug when execution, capture,
evaluation, persistence, export, or UI behavior differs from the documented
contract.

## Security and private data

Do not report vulnerabilities or leaked credentials in an issue. Follow
[SECURITY.md](SECURITY.md) for private reporting.

## Scope

Maintainers can help with the platform and shipped plugin integration. Support
for provider accounts, third-party benchmark content, target repository build
systems, or custom plugins may require the corresponding upstream project.