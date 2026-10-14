# Installation

## Requirements

- Claude Code or Codex with filesystem access and command execution.
- Git and Python 3.10 or later available on PATH.
- A repository containing an implementation plan and its approved specification.
- Project dependencies already available for any rehearsal commands.
- A fresh independent reviewer for a Ready verdict. Without one, the report records the missing review and remains Not ready.

The initial release is verified on Linux. The manual shell commands below target Linux/macOS shells; native Windows installation has not been verified. The renderer has no third-party Python dependencies, API keys or account of its own. Your agent host may incur normal model charges.

## Claude Code plugin

In your terminal:

```bash
claude plugin marketplace add snowholt/plan-validation
claude plugin install plan-validation@snowholt-plugins
claude plugin list
claude plugin details plan-validation
```

Look for both skills in the component inventory. Start a fresh session in your project. The plugin commands are:

```text
/plan-validation:validation-args
/plan-validation:validate-plan
```

This is the project's own marketplace, not Anthropic's official directory. Installation follows the [Claude marketplace mechanism](https://code.claude.com/docs/en/plugin-marketplaces).

To inspect locally before installing, clone the repository and run `claude plugin validate .` from its root. A temporary local session can load it with `claude --plugin-dir /absolute/path/to/plan-validation`.

### Update or remove

```bash
claude plugin marketplace update snowholt-plugins
claude plugin update plan-validation@snowholt-plugins
```

Restart Claude Code after updating. To remove the plugin:

```bash
claude plugin uninstall plan-validation@snowholt-plugins
```

Your project's plan/spec edits and saved reports remain your files. Review them separately; uninstalling a skill does not undo a validation.

## Codex skills

Inside Codex, request both skills from the built-in installer:

```text
$skill-installer install validate-plan and validation-args from https://github.com/snowholt/plan-validation, using skills/validate-plan and skills/validation-args.
```

Resolve an existing installation instead of overwriting it. If skills do not appear, restart Codex. Invoke with `$validation-args` and `$validate-plan`. A packaged plugin may expose a namespace; use the exact name shown by its skill picker.

### Manual clone and symlinks

Use this alternative when you want an inspectable checkout and straightforward updates. The script stops before creating anything if its destination paths are already in use. It does not replace existing skills.

```bash
bash <<'SH'
set -eu
pv_checkout="$HOME/.local/share/plan-validation-skills"
pv_skills="$HOME/.agents/skills"
for pv_path in "$pv_checkout" "$pv_skills/validate-plan" "$pv_skills/validation-args"; do
  if [ -e "$pv_path" ] || [ -L "$pv_path" ]; then
    printf 'Already exists; inspect before installing: %s\n' "$pv_path" >&2
    exit 1
  fi
done
mkdir -p "$HOME/.local/share" "$pv_skills"
git clone https://github.com/snowholt/plan-validation.git "$pv_checkout"
ln -s "$pv_checkout/skills/validate-plan" "$pv_skills/validate-plan"
ln -s "$pv_checkout/skills/validation-args" "$pv_skills/validation-args"
SH
```

Codex supports user skills at `~/.agents/skills` and follows symlinked skill folders. See the [official skills documentation](https://learn.chatgpt.com/docs/build-skills). The clone tracks `main`; inspect changes before updating. For a fixed pilot revision, check out `v0.1.0` in the clone instead.

### Update or disable

For the manual clone on `main`:

```bash
git -C "$HOME/.local/share/plan-validation-skills" pull --ff-only
```

An installer-created copy does not follow that clone. Use the installer to prepare a replacement version after preserving any local changes; do not overwrite a customized skill without reviewing the diff.

To disable a skill without deleting it, add a `[[skills.config]]` entry to your existing `~/.codex/config.toml`, using the exact absolute `SKILL.md` path shown by Codex, with `enabled = false`. Preserve the rest of your configuration and restart Codex. [Official enable/disable guidance](https://learn.chatgpt.com/docs/build-skills#enable-or-disable-local-codex-skills).

To remove the manual symlink installation, first verify that each path is a symlink to this clone. Remove those two symlinks only; keep the clone if it contains changes. Do not delete a skill folder from another installation. The built-in installer route may use a different user skill location; inspect its actual installed path.

## Plugin package for Codex

The repository includes `.codex-plugin/plugin.json`, referencing the same `skills/` directory. It is a compatibility package for hosts that support that layout. The first-release quick start uses standalone skills; live Codex plugin installation and public directory acceptance are not claimed. See [OpenAI plugin packaging](https://developers.openai.com/plugins/build/plugins) for current host-specific authoring and submission routes.
