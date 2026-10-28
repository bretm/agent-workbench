---
name: design-taste-frontend
description: Use Taste to design or refine websites and web application screens with researched visual directions, reference imagery, and browser critique. Applies to landing pages, portfolios, dashboards, admin views, and settings screens.
---

# Design with Taste

## Workbench use

Follow the user's brief, existing design system, accessibility needs, and project instructions before the house-style defaults below. Use the page or app workflow that matches the task; a focused component edit or review does not require rebuilding the whole page. When UI UX Pro Max is also in use, let one chosen visual direction govern the design and use Pro Max for focused UX or platform guidance.

In every command, replace `<skill>` with the absolute directory containing this SKILL.md and quote paths containing spaces. Run from the target project's root. Keep `.taste-skill/` ignored or pass a private `--out` directory; verify ignore coverage before writing screenshots or design notes. Draw history defaults to that output directory, with `TASTE_SKILL_HISTORY` available for an explicitly chosen alternative. The browser helper uses a fresh temporary profile and cleans up only its own profile and process.

The workbench distributes scripts, libraries, references, and starter assets. It does not install Node, a browser, packages, or hooks. Check runtime availability before using the helpers. Use existing project build commands and authorized local targets. Read [the app workflow](references/app-screens.md) for dashboards and other application screens, and [the critique guide](references/critique.md) when reviewing screenshots. These are web interfaces; use platform-specific guidance for native applications.

Keep changes within the requested scope. House-style failures are design findings, not universal usability requirements: preserve justified brand or product choices, use the inspector's `--allow` option for applicable exceptions, and report remaining findings honestly. Bound repair to the requested task and the three visual review rounds below; missing tooling or unresolved findings belong in the result. Add imagery and motion when they serve the brief, with reduced-motion behavior, rather than adding features solely to satisfy a count.

This upstream revision contains the shared scroll-scene stage but no scene catalogue or individual scene demos. The draw therefore supplies no scenes. Do not reference missing demos; the scene tools are available for project-authored scenes when relevant.


## Choose the relevant workflow

- **Public website or landing page:** read [the detailed page workflow](references/page-workflow.md). Establish the subject, audience, primary action, existing brand and available imagery; write the page's argument, compare three drawn directions, choose one, and build against it. The reference preserves the upstream workflow, house rules, design principles and narrow-task exceptions.
- **Web application screen:** read [the app workflow](references/app-screens.md). Dashboards, settings, admin screens and inboxes have their own style library, layout rules and `--app` inspector mode. Do not apply marketing-page image or motion quotas to working interfaces.
- **Existing interface:** record its current appearance and behavior first. For a review, report the findings. For a redesign, preserve routes, data, working interactions, stack and brand constraints; compare before and after.
- **Single component or section:** use the surrounding design direction and relevant references. Skip a new direction draw when the design is already established.

## Runtime commands

Use `node --version` and an existing Chrome, Edge or Chromium installation for the full inspector. The helpers have no npm dependencies. `CHROME_PATH` can select a browser executable. If the inspector is unavailable, use an existing browser tool for screenshots and disclose the missing automated measurements; the source lint helper runs on Node 18+.

List available choices before selecting a sector or application kind:

```sh
node "<skill>/scripts/draw.mjs" --list sectors
node "<skill>/scripts/draw.mjs" --app --list kinds
```

For example, compare directions for a website or draw a working application's style:

```sh
node "<skill>/scripts/draw.mjs" --sector saas --brief "A team planning tool" --options 3
node "<skill>/scripts/draw.mjs" --app --kind workspace --brief "A team planning tool"
```

The draw writes its chosen direction and history in `.taste-skill/` unless `--out` selects another directory. `--options` previews choices without writing; `--show` reprints the saved direction. Preserve fixed brand choices with `--keep palette,type`.

Inspect the running interface and then open the generated screenshots:

```sh
node "<skill>/scripts/lint.mjs" "<source-directory>"
node "<skill>/scripts/inspect.mjs" "<local-url>" --out .taste-skill/inspect
# For a web application screen, add --app to the inspector command.
```

The inspector measures desktop, tablet and mobile layouts and writes a report and screenshots. Review those images with [the critique guide](references/critique.md); fix the most consequential problems within the bounded review above. Measurements and aesthetic scores are separate from functional tests. Exercise the requested user flows with the project's normal browser/test tools and state what actually passed.

## Supporting guidance

Read only the references relevant to the current design decision:

| Reference | Use |
|---|---|
| [Copy](references/copy.md) | Page argument, headings, calls to action and interface writing. |
| [Type](references/type.md) | Type scale, pairing, measure and font loading. |
| [Colour](references/colour.md) | Palette roles, contrast and surface separation. |
| [Layout](references/layout.md) | Grids, spacing, navigation and responsive composition. |
| [Imagery](references/imagery.md) | Honest imagery, search, source credits and crops. |
| [Motion](references/motion.md) | Purposeful animation and reduced-motion behavior. |
| [Scenes](references/scenes.md) | Shared stage and inspection for project-authored scroll scenes; this pin has no scene catalogue or demos. |
| [Design patterns to reconsider](references/tells.md) | Upstream's dated registry of overused visual treatments. |
| [Research](references/research.md) | Source study and the limits of its evidence. |

Use the scripts to query `library/` instead of loading the full datasets. Starter CSS, chart helpers and other assets remain under `assets/`; use them when they fit the existing stack. Image search and downloads require network access and retain attribution; use the imagery reference before choosing external pictures.

Report the chosen direction, material changes, checks and remaining issues. Identify sample content or unwired actions and preserve media credits. Do not claim browser checks, real users' feedback or design quality from script success alone.

Adapted from Leonxlnx Taste Skill. See [pinned provenance and MIT license](../../reference/upstream.md).

When relevant personal facts or preferences affect this task, use [private context](../../reference/private-context.md). Load only the needed topics; ask about consequential unknowns and save confirmed updates through its tool. Keep personalized profiles and reports private.
