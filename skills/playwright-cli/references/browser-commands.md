# Browser commands and diagnostics

Adapted from Microsoft Playwright CLI; condensed and modified for named sessions and local evidence. See [provenance and Apache-2.0 license](../../../reference/upstream.md). These examples assume an already-open `ui-check` session and ignored `.local/playwright/` output. Substitute the established local executable prefix when using a project installation. Consult `<command> --help` when options differ.

## Locate and interact

```sh
playwright-cli -s=ui-check snapshot
playwright-cli -s=ui-check fill e3 "Example item"
playwright-cli -s=ui-check press Enter
playwright-cli -s=ui-check click "getByRole('button', { name: 'Save' })"
playwright-cli -s=ui-check click "getByTestId('save-button')"
playwright-cli -s=ui-check select e8 "option-value"
playwright-cli -s=ui-check check e10
playwright-cli -s=ui-check reload
playwright-cli -s=ui-check snapshot
```

Refs such as `e3` come from the current snapshot. If a control is ambiguous or the page changes, inspect again. For a large page, try a scoped snapshot or search when the installed version supports it:

```sh
playwright-cli -s=ui-check snapshot "#main"
playwright-cli -s=ui-check snapshot --depth=4
playwright-cli -s=ui-check find "Save"
```

Use `run-code` for a bounded operation or explicit assertion that the CLI does not express directly. It accepts a function expression with a Playwright `page`, not a full Node program with imports or `require`:

```sh
playwright-cli -s=ui-check run-code "async page => {
  await page.getByRole('heading', { name: 'Saved' }).waitFor({ state: 'visible' });
  return { saved: await page.getByRole('heading', { name: 'Saved' }).isVisible() };
}"
```

Check the returned result and any reported errors. Some versions report a tool error inside output even when the shell command succeeds. Waiting for a specific element or application condition gives stronger evidence than a fixed delay or network-idle guess.

## Diagnose and capture evidence

```sh
playwright-cli -s=ui-check console error
playwright-cli -s=ui-check requests
playwright-cli -s=ui-check screenshot --filename=.local/playwright/after.png
playwright-cli -s=ui-check snapshot --filename=.local/playwright/after.yaml
playwright-cli -s=ui-check tracing-start
# Reproduce the relevant interaction.
playwright-cli -s=ui-check tracing-stop
```

Trace files use the configured output directory. Request details can contain credentials and private data; inspect a specific request only when needed, and summarize the relevant result. Keep artifacts private until reviewed and publication is authorized. Visual evidence supports the recorded observation; it does not replace a behavioral assertion.

For layout checks, use `resize WIDTH HEIGHT` and repeat the relevant observation. For another tab, use `tab-list`, `tab-new URL` and `tab-select INDEX`; snapshots and refs apply to the selected tab.

## State reuse and borrowed browsers

Use storage reuse only when authorized for the target account and environment. Keep state files under the private output directory, restrict their permissions, and avoid placing secrets directly in shell commands:

```sh
playwright-cli -s=ui-check state-save .local/playwright/session.auth-state.json
# In a new isolated session, open the target before loading approved state.
playwright-cli -s=ui-check state-load .local/playwright/session.auth-state.json
playwright-cli -s=ui-check reload
```

Saved state may include authentication tokens. Do not assume it captures all browser state. Preserve user-owned state files unless deletion is authorized; clean up disposable state created for the task when it is no longer needed.

When a task explicitly calls for an existing browser, consult `attach --help` and use the approved endpoint or channel. Finish with `playwright-cli -s=ui-check detach` so that the external browser stays running. Do not use broad session cleanup commands.

## Existing automated tests

Use the project's test script, configuration and fixtures. If Playwright is already installed locally, a focused run can use:

```sh
PLAYWRIGHT_HTML_OPEN=never ./node_modules/.bin/playwright test tests/example.spec.ts
```

When the installed version supports CLI debugging, run the focused test with `--debug=cli` in the background, wait for the printed debugging instructions, and attach to the exact supplied session. Preserve fixture setup and stop that debug process when finished. Rerun the test normally after a fix; a paused or rehearsed debug session does not establish a passing test.

When generating a test from browser exploration, use stable locators and explicit assertions. Follow existing file layout and fixture conventions. If observed behavior conflicts with intended behavior, investigate the regression rather than silently changing the expected outcome.
