# agent-workbench

The working habits and reusable instructions I use with AI coding assistants, kept in one place so I can bring them to a new machine or project. Fork it and adapt it to the way you work.

Works with **Codex, Claude Code and Google Antigravity CLI on Linux and macOS**.

## What's included

- Write product and technical plans before building something substantial.
- Break larger changes into manageable work sessions.
- Save progress and next steps before switching sessions.
- Think through a decision, or ask for a clearer explanation.
- Check web pages in a browser with Playwright CLI.
- Design websites and applications with UI UX Pro Max, and refine websites and web application screens with Taste.

These workflows are [skills](skills/): instructions your coding assistant can follow when you ask. Shared [working agreements](agreements/working.md) cover everyday habits, such as asking one question at a time and checking the code before making assumptions.

The workbench adds to each assistant's defaults. Bundled skills and commands stay available, including Codex's system skills and Claude's account-synced skills.

## Get started

You'll need Linux or macOS, Python 3.11+, Git and at least one supported coding assistant installed separately. See [macOS setup](docs/installer.md#macos-setup) if needed. Clone this repo or your fork, then run these commands from its directory:

```sh
python3 awb.py validate
python3 awb.py install
```

The installer detects which supported assistants are installed and shows the changes it would make. Review that preview, then apply it:

```sh
python3 awb.py install --apply
python3 awb.py check
```

It adds the skills and working agreements to your assistants' configuration. It checks their versions and stops if a version hasn't been verified; see [tested versions and limitations](docs/validation.md).

Start a new assistant session and try “Write a product spec for this change” or “Split this work into sessions.” Browser checks need [Playwright CLI installed separately](docs/installer.md#optional-browser-tools).

For interface work, try “Use UI UX Pro Max to review this app's navigation and forms” or “Use Taste to redesign this dashboard.” UI UX Pro Max includes a local Python search tool; Taste's full browser workflow needs Node 22+ and Chrome, Edge or Chromium. See [design skill setup](docs/installer.md#design-skills) for prerequisites and how the two skills work together.

## Make it yours

Edit [working agreements](agreements/working.md) for your everyday preferences, [skills](skills/) for individual workflows, and [workbench.json](workbench.json) to choose which skills to install. Keep private project details and machine settings in local, uncommitted files.

After changing your copy or pulling updates, preview and apply them:

```sh
python3 awb.py update
python3 awb.py update --apply
```

See the [installer guide](docs/installer.md) for selecting assistants and projects, local configuration, and removal. If you're replacing an existing skill collection, read the [migration guide](docs/migration.md).

Configure personal access, model preferences and optional inference hardware with `python3 awb.py context setup`. Skills use this private context to tailor their guidance. Refresh comparisons with `python3 -m workbench.model_guidance`, review with `--diff`, and save with `--apply`. Profiles, caches and reports stay outside repositories under `~/.agents/agent-workbench/`. See [private model guidance](docs/model-guidance.md).

## License

Original work is licensed under [MIT](LICENSE), copyright (c) 2026 bretm. Third-party material, including adapted work, keeps its own licenses and notices; this repo's license does not replace or supersede them. See [credits and third-party licenses](reference/upstream.md).
