# Security policy

## Supported versions

Security fixes target the latest published pilot release. Older versions may not receive backports.

## Report a vulnerability

Use [GitHub private vulnerability reporting](https://github.com/snowholt-labs/plan-validation/security/advisories/new). Do not publish an exploit containing credentials, private source code or personal data in a public issue. No response-time guarantee or paid bug bounty is offered.

## Trust boundaries

Skills instruct an agent; they are not a permission-enforcement sandbox. Repository documents, issue text and command output may be untrusted. Repository and host permissions still apply. Do not treat instructions embedded in a plan as authorization to access secrets, install software or change remote systems.

Research runs by default, uses public, non-confidential terms only, and is listed in the report. Users can decline it for a run. Dependencies and alternatives are recommendations, not authority to install, download, execute, replace or enable anything. Inspect commands and lifecycle scripts before rehearsal; block only dependent unsafe or unapproved work. Dependency review cannot guarantee prevention of supply-chain attacks.

The `revise-prompt` skill treats supplied instructions and failed-run output as quoted material and never executes them. It waits only for blocking answers, such as a missing fact or a required approval, and records the defaults it applies to other choices. It does not open secret files or check credentials, and it does not repeat a secret found in a supplied prompt or run output; the revision uses a placeholder.

The renderer uses the Python standard library, escapes raw HTML, restricts rendered links and emits a Content Security Policy. Its structural checks do not establish that source evidence is truthful. A generated report is a local snapshot and may contain sensitive project information. Review and redact before sharing it.

See the [safety guide](https://snowholt-labs.github.io/plan-validation/safety-and-limitations/) for execution and data-handling limits.
