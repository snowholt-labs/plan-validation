# Focused dependency and alternatives review

Read this when the scoped plan proposes or changes a dependency, relies on an existing security-critical dependency, or has a consequential build-versus-adopt choice. Follow the [public research](research-permissions.md) rules for any external lookup. Research supports a recommendation; it does not authorize implementation.

## Select a bounded review

- Inventory exact proposed/changed packages, plugins, services and versions from the plan and permitted manifests/lockfiles. Add existing security-critical dependencies only where their role is relevant to this plan, such as its authentication, signature verification, payment or untrusted-file boundary. State why each item is in scope.
- Inspect relevant transitive paths from a local lockfile, SBOM or existing audit. Expand only for a concrete advisory, reachable sensitive path, install hook or compatibility concern; do not audit every transitive package.
- Separate requested version, resolved version and current upstream version. An unpinned or unresolved version is Unknown; do not silently pick a new one. A package name alone does not establish identity.
- If no material dependency concern or alternatives decision applies, record the evidence and `No dependency change or unresolved choice in the reviewed scope.` Complete the normal report without unnecessary research, comparisons or a menu.

## Verify evidence, not reputation

Use dated primary sources: official registry records, publisher-controlled repositories and documentation, release/tag history, security policies/advisories, vendor notices, licenses and official service pricing/terms. Record the exact source URL, version or commit, source date when available, access date and the claim it supports. Local evidence needs a path/revision, not an invented public citation. Separate **Verified**, **Assumption** and **Unknown** for each material claim. A reported issue is not a confirmed advisory; a fix is not deployed merely because a release exists.

Cover these dimensions proportionately; mark genuinely irrelevant dimensions N/A with a reason, and missing evidence Unknown:

| Dimension | Required assessment |
| --- | --- |
| Identity and provenance | Exact ecosystem/package or marketplace/plugin ID, version, publisher, official registry/repository ownership links, source/release correspondence and available signatures/attestations; flag typosquatting or legacy lookalikes without assuming misconduct. |
| Maintenance and releases | Release history, support policy, maintainer continuity, relevant issue/PR response and deprecation/archive notices. Distinguish mature stable software with infrequent releases from abandonment; release age alone is insufficient. |
| Security and fixes | Confirmed advisory identifiers, affected/fixed ranges, relevance to the proposed/resolved version and reachable code path, mitigations and unresolved reports. No reported vulnerabilities is not proof of safety. |
| License and provenance limits | License for the exact component/version and material transitive constraints; compatibility with intended distribution and any unclear ownership or artifact origin. Do not give unsupported legal assurances. |
| Compatibility and transitive risk | Runtime/framework/platform support, peer requirements, lockfile resolution, relevant transitive conflicts, critical-path components and likely migration breakage. |
| Scripts and permissions | Available install/build/lifecycle hooks, planned commands, shell/network activity, requested host/plugin permissions and credential access. If scripts are not locally or publicly inspectable through public research, record Unknown; do not download or execute the package to find out. |
| Privacy and operations | Data sent/stored, recipients, retention, telemetry, credentials, network dependence and operational burden. Public documentation does not verify deployed behavior. |
| Cost and lock-in | Current documented price/limits with date, estimated usage assumptions, recurring costs, portability/export, switching and rollback costs. Unknown usage is not zero cost. |

Stars, downloads, company backing and a lack of advisories are contextual signals, never proof of safety. Do not invent trust scores, convert a reputation signal into a security verdict, or promise prevention of supply-chain attacks.

## Compare at most two strong alternatives

Start with the plan's original approach. Where a meaningful choice exists, investigate at most two strong alternatives among maintained libraries, open-source projects, established standards, services and agent plugins. Consider keeping the existing implementation or adding no dependency as an alternative when viable; it counts toward the two-alternative limit. Do not fill the table with weak options just to reach a quota.

Compare requirements fit, concrete benefit, security/audit evidence, maintenance and license, privacy/data handling, integration/operational effort, customization, relevant performance/accessibility, total time/cost, lock-in and migration/rollback. Prefer established standards and vetted components for security-sensitive protocols, while grounding suitability in this plan's requirements.

Before recommending an agent plugin, verify official ownership, exact publisher/ID/version, current availability for the intended host, documented capability, permissions and fit. A similarly named search result, company endorsement or repository alone does not verify an installable official plugin. If these facts cannot be verified, record the candidate as unverified and do not offer adoption as an actionable recommendation. **Auth0 is only an example to investigate when relevant, never a default recommendation or an assumed official plugin.**

Use a compact table inside report section 5; one row per actual approach, original plus at most two alternatives. Include a separate compact dependency table when needed for the evidence dimensions above. Group columns for readability, without omitting material risks:

| Approach and exact identity/version | Fit and benefit | Security, maintenance, license and evidence | Privacy, cost and lock-in | Integration and migration/rollback effort | Decision confidence and unknowns |
| --- | --- | --- | --- | --- | --- |

Use **Decision confidence: High / Medium / Low**, with reasons:

- **High:** current primary and local evidence resolves the material suitability questions; name remaining limits.
- **Medium:** evidence supports the choice, but relevant compatibility, operations or integration remains unexercised or rests on stated assumptions.
- **Low:** material identity, safety, availability or fit evidence is missing, contradictory or stale. Do not recommend an unverified plugin.

These are evidence judgments, not probabilities or safety ratings. Keep the report's existing PLAN/SPEC quality scores and readiness-confidence contract separate. If custom code wins, state why the alternatives fail the requirements and name the ongoing security/maintenance burden.

## Preserve decisions and authority

Finish all independent checks and prepare the complete report without stopping to ask. Write a menu in report section 6 only for unresolved actionable choices, not informational findings or already accepted decisions. The user answers it later:

- **Keep original approach:** name it and explain the benefit, risk and any unsatisfied safety/approval conditions.
- **Adopt [verified named alternative]:** state the concrete benefit, integration effort, costs, tradeoffs and migration/rollback impact. Include at most the two researched alternatives.
- **Defer:** name the dependent tasks that will wait and the independent work that can continue.

Mark one recommendation and give its reasons and High/Medium/Low confidence. If no alternative is verified, omit adoption and explain that limit. Record a decision ID, user answer or pending/deferred status, exact approval scope, affected tasks and separately required installation/service permission in sections 5–6. The short handoff references that complete record. Routine presentation or execution-order clarifications may use recorded defaults within the approved scope; dependency/service adoption and other required approvals cannot. A recommendation, silence, elapsed time or completed research is not an adoption decision. Adopting an approach does not authorize executing its install/enable commands during validation.

Retain selected PLAN/SPEC content while approval is pending. Recheck affected documents after an approved revision. Declined or failed research alone does not make every task unsafe; block only dependent work and state what remains independently verified.
