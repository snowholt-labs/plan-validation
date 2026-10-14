# Launch strategy

Prepared 14 October 2026. This is a proposed pilot strategy, not an adoption forecast.

## Positioning

Lead with **“Rehearse the plan before you hand it to a coding agent.”** The useful distinction is execution evidence, visible scope changes and a durable handoff. Position the project as a companion to planning tools. Do not claim perfect plans, guaranteed safety, automatic savings or superiority based on scores.

## Distribution choice

| Route | Fit and burden | Decision |
| --- | --- | --- |
| Native Claude plugin plus Codex skills | Reuses established host discovery, versions and skill folders; no runtime service, telemetry or package dependency. Host behavior still needs testing. | Adopt for the pilot. |
| A single pasted prompt | Very easy to share but loses deterministic renderer/assets, versioned references and updateable packaging. | Use a short prompt only to explain the product. |
| A custom CLI, npm package or hosted service | Adds installation, maintenance, dependency or data-handling work without solving a first-release requirement. | Defer unless actual users demonstrate a need. |

**Decision confidence: High** for using native packaging and avoiding a new service; **Medium** for audience fit; **Unknown** for repeat use, net time savings and marketplace acceptance. These are judgments, not numerical trust scores.

Current primary guidance: [Claude plugin packaging](https://code.claude.com/docs/en/plugins), [marketplaces](https://code.claude.com/docs/en/plugin-marketplaces), [Codex skills](https://learn.chatgpt.com/docs/build-skills), [OpenAI plugin packaging](https://developers.openai.com/plugins/build/plugins), and the [Agent Skills format](https://agentskills.io/specification). Sources checked 14 October 2026. The first release uses native folders and standard-library Python; it adds no third-party runtime package or paid service.

## First month

| Stage | Action | Evidence to collect |
| --- | --- | --- |
| Release | Publish one versioned pilot, working install steps, a screenshot, wiki, clear limits and issue templates. | A fresh install loads both skills; deterministic checks pass. |
| First week | Share one concrete demonstration through your own developer profile and an appropriate community where project sharing is welcome. Use the [draft launch post](launch-post.md). | Where newcomers get stuck and whether they complete a first run. |
| Weeks 2–3 | Invite a small voluntary pilot and fix repeated friction. Ask for redacted examples instead of private repositories. | Confirmed useful findings, false alarms, missed defects, support effort and voluntary second use. |
| Week 4 | Publish a short case study with real evidence. Consider official directory submission once installation and repeated use are credible. | A reproducible result and explicit limits, not a star target presented as success. |

A practical learning target is about ten independent users across several repositories, with a few returning users and confirmed findings. These are proposed learning targets, not statistical proof of demand. Measure an observation period and denominator before reporting conversion or retention.

## Earning visibility

Keep the first screen of the README concrete: problem, report preview, installation and one useful example. Use accurate GitHub topics, a concise About description, release notes and a single gentle star request. Answer reproducible issues and give contributors credit. Replace the authored example with an authorized real case study when one exists, retaining honest labels.

Post from your own accounts and follow each community's current rules. Do not buy stars, use engagement exchanges or repeatedly advertise in unrelated issues. Official directory listings are applications with separate review; do not claim acceptance merely because the repository is public.

## What to do next

Use the release on one real, shareable plan. Publish a short account of the specific defect it found, the evidence, the extra time it took and what it missed. That is a stronger reason to try the project than more badges or an unsupported performance claim.

No social posts, outreach messages or third-party directory submissions are made by publishing this strategy document.
