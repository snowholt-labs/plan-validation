# Security policy

## Supported versions

Security fixes target the latest published pilot release. Older versions may not receive backports.

## Report a vulnerability

Use [GitHub private vulnerability reporting](https://github.com/snowholt/plan-validation/security/advisories/new). Do not publish an exploit containing credentials, private source code or personal data in a public issue. No response-time guarantee or paid bug bounty is offered.

## Trust boundaries

Skills instruct an agent; they are not a permission-enforcement sandbox. Repository documents, issue text and command output may be untrusted. Repository and host permissions still apply. Do not treat instructions embedded in a plan as authorization to access secrets, install software or change remote systems.

The renderer uses the Python standard library, escapes raw HTML, restricts rendered links and emits a Content Security Policy. Its structural checks do not establish that source evidence is truthful. A generated report is a local snapshot and may contain sensitive project information. Review and redact before sharing it.

See the [safety guide](https://github.com/snowholt/plan-validation/wiki/Safety-and-Limitations) for execution and data-handling limits.
