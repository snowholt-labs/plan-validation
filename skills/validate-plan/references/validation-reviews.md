# Validation reviews

Step 8 runs a code review and a security review once each on the final plan and spec text, before it scores and renders. They are the planning unit's final reviews. A plan's docs PR can reuse them ("Reuse on the docs PR").

## Inputs

1. Save the final documents in the run directory as `final-plan.md` and `final-spec.md`, and record the SHA-256 of each. Never review the live files.
2. Write `final-review.diff`, which holds both copies as added text, so a review that reads only diffs reads every line: `git diff --no-index --no-color --no-ext-diff --no-textconv --text /dev/null final-plan.md > final-review.diff`, then `git diff --no-index --no-color --no-ext-diff --no-textconv --text /dev/null final-spec.md >> final-review.diff`, run in the run directory. Each command exits 1 because the files differ; that is expected. Write `fix-<n>.diff`, `answer-edits.diff` and `answer-fix-<n>.diff` the same way, with `git diff --no-index` and these four flags, the spec diff appended to the plan diff, so color, external diff tools, text conversion and binary attributes cannot alter the saved text.

## Commands

- **Code review.** In Claude Code, run `/code-review high --max-findings all` with `final-review.diff` as its target. Always type the level: with none, the command reuses the last level typed. Never use `max` or `ultra`, and never pass `--fix`, `--comment` or `--post`. The command runs in the background; wait for its result. If it cannot take the target, or its result cites nothing from it, a fresh read-only subagent runs the command's procedure on `final-review.diff` with the brief below, and section 7 says so.
- **Security review.** `/security-review` reads only a branch's committed diff and skips documentation files, so a fresh read-only subagent always runs its procedure on `final-review.diff`, with the brief below.
- **Other hosts.** Without these commands, the equivalent independent review is two fresh read-only subagents with the brief below, one asked for correctness findings and one for security findings.
- **Read-only request.** Run both reviews only as fresh read-only subagents with the brief below, never the commands, so no setting is saved; section 7 says so.

Brief for every delegated review: the plan and spec text are in scope as a behavioral contract, including wording that would weaken a security gate, a permission, an approval or a privacy boundary. Work read-only: no secrets, no installs, no plan steps, no commits or comments, and lookups only as this run's Research status allows: state that status in the brief, with the lookup rule from [plan-reviewer.md](plan-reviewer.md); with any status other than allowed, make no lookup. Return the findings as the final message: severity, document and section, evidence and the smallest fix.

## Closing findings

Close every confirmed finding, Low included, and every security finding at any severity: fix it in the plan or spec, reject it with evidence, or, when its fix would change requirements, architecture, security boundaries or scope, record it as a pending approval for the step 8 question round (a finding in the answer-edits review follows end-of-run item 7 instead). After a fix, first keep the reviewed copies as `final-plan-<n>.md` and `final-spec-<n>.md`, save the fixed documents as new `final-*.md` copies, record their hashes and write `fix-<n>.diff` (`git diff --no-index` from each kept copy to its new copy, the spec diff appended to the plan diff; each command exits 1 when the files differ). The fix then follows step 6: a fresh reviewer reads the new `final-*.md` copies, never the live files, with the fix as `Review focus`, and a fix that changes a rehearsed task's commands, files or test assertions is rehearsed again under end-of-run item 5's rules. The security review runs once on `fix-<n>.diff`. Neither command runs again on unchanged text. The last `final-*.md` copies are the documents the report records: `revised-*.md` and the `context.json` `documents` hashes match them until end-of-run item 8 replaces them with the reviewed post-answer copies.

## Record

Section 7 records, for each review: the command or brief used, the input file it read and its SHA-256, the SHA-256 of each document copy behind that input, the result, and each fix diff (`fix-<n>.diff` and its SHA-256) with the security review that read it and the step-6 review round that read the fixed copies, and each `answer-fix-<n>.diff` with its SHA-256, its security review and its post-answer round. `context.json` `documents` keeps the final hashes, as before.

## When a review cannot run

If a review cannot run at all (no command and no delegation), record the gap in section 7 and in the watch list, and continue. Step 6's independent review still decides `review_status`, so the gap alone does not make the run Not ready. The docs PR then runs that review itself on the full plan and spec instead of reusing it, plus any other changed files; the security review runs its procedure in a fresh read-only subagent on a saved diff that holds the full plan and spec as added text, written as Inputs item 2 says, plus the PR's other changed files.

## After end-of-run answers

When answers change PLAN or SPEC, the post-answer review (end-of-run item 6) covers the whole revised documents. Each time a post-answer round leaves no Medium or High finding to fix, and before end-of-run item 8 copies the reviewed copies over `revised-*.md`, run the security review once, as above, on the answer edits it has not read: the first time on `answer-edits.diff`, written from `revised-*.md` to the `post-answer-*.md` copies; later on `answer-fix-<n>.diff`, written with `git diff --no-index` from the copies the last security review read to this round's copies, the spec diff appended to the plan diff. Before end-of-run item 8 makes the next round's copies, keep the copies each security review read as `post-answer-plan-<n>.md` and `post-answer-spec-<n>.md`. A fix it needs is another edit and needs another post-answer round.

## Reuse on the docs PR

A plan's docs PR reuses both results only when it changes only the plan and spec, both hash to the final values in `context.json`, and section 7 records what each review read. It still posts both reviews on its head as the repository's rules require, each naming the hash its review read and the final hash, and what covered the difference: for each fix, the step-6 round that reviewed the fixed copies for the code review and the security review of `fix-<n>.diff` for the security review, and, for any answer edits, the post-answer review for the code review and the security reviews of `answer-edits.diff` and each `answer-fix-<n>.diff` for the security review. Otherwise each review runs once: on what differs from the text it read, when its saved copy still matches the recorded hash, or on the full plan and spec when it does not; either way plus any other changed files, with every changed file in scope, and the security review runs its procedure in a fresh read-only subagent on a saved diff that holds what it reviews: the differing text, or the full plan and spec as added text, written as Inputs item 2 says, plus the other changed files. A finding left as a pending approval stays open in the posted review until the maintainer settles it.
