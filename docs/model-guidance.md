# Private model guidance

The model comparison tool combines public benchmark evidence with the user's private hardware profile. All generated reports and fetched caches stay outside repositories. The public model reference describes how to choose; it contains no user's inventory, access profile, or locally observed launch settings.

## Configure your situation

Run `python3 awb.py context setup` from the checkout. The guided conversation records available assistants, declared access, provider rotation and model preferences, and optional inference hardware. It asks one question at a time, supports unknown values, reviews the answers, and saves only after confirmation. Existing answers are retained; setup never reads credentials or changes authentication.

The default root is `~/.agents/agent-workbench/`. Use `--context-dir` or `AWB_CONTEXT_DIR` to choose another external directory. See the [private-context contract](../reference/private-context.md) for assistant-led updates and additional topics.

Hardware memory is usable GPU or shared inference memory in GiB, not necessarily total system RAM. Reserve space for the runtime and context cache. Unknown capacity produces no fit claims. Multiple machines are separate budgets; CPU offload and pooled memory are excluded.

## Refresh your report

```sh
python3 -m workbench.model_guidance
python3 -m workbench.model_guidance --apply
python3 -m workbench.model_guidance --offline --check
```

Defaults are `context/hardware.json`, `cache/artificial-analysis.json`, and `generated/model-guidance.md` beneath the private root. Missing hardware stays unknown. Preview may refresh the cache but does not replace the report. Use `--diff` to display the private report difference locally. `--apply` saves the report; `--check` exits 0 for current evidence, 1 for differences, and 2 for an error. These outputs do not need installer updates.

`--output` selects an alternative external report; `--reference` remains a compatibility alias. `--cache` selects an external cache and `--hardware` selects an input profile. Git worktree destinations are rejected before fetching or writing, including symlink aliases. Private context stays independent of the invoking directory and installed release.

Installed skills use `python3 -B <release>/runtime/awb-local.py models ...` with their recorded `--context-dir`. The bundled runtime works without the source checkout.

The fetcher uses Python 3.11+ and its standard library, with no API key or inference calls. It reads Artificial Analysis's public model and leaderboard pages; detail pages use four workers and a 24-hour cache. Use `--workers 1` or `--detail-max-age 0` when needed. Offline runs preserve the original evidence date. Source-format changes fail explicitly; incomplete results cannot become an applied report.

Estimates use total model parameters and default to 8-bit weights plus 15% metadata allowance. `--bits 6` and `--bits 16` are supported. Runtime memory, quantization availability, licensing, context length, and actual performance still need verification. Benchmark rankings never change user preferences or client defaults automatically.

## Import older local data

`python3 awb.py context migrate --from /outside/repositories/legacy` previews imports of `model-hardware.json`, `artificial-analysis.json`, and optional `models.md` notes. Add `--apply` after review. Different existing destination content blocks migration; compare it and use a topic update instead. Import preserves original dates and unknowns and never deletes its source.
