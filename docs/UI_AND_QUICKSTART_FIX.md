# UI and Quickstart Fix

## Evidence

- The quickstart UI registered `UIStartListener` while PubSub stored listeners as weak references.
- The listener could be collected before the `HummingbotUIEvent.Start` event, leaving the UI at the `>>>` prompt.
- The old left panel combined fixed branding and runtime output in one scrollable `TextArea`.
- The old header contained legacy UTF-8/Windows-1252 mojibake and trailing tab characters.

## Implementation

- `bin/hummingbot_quickstart.py` now retains the quickstart listener on the application object.
- `bin/hummingbot.py` retains the listener for the regular UI entry point as well.
- `hummingbot/client/ui/layout.py` separates the fixed art/title, dynamic dashboard, and scrollable output.
- Runtime dashboard values are derived from the active script/controller configuration.
- Output is focusable and read-only so it can be selected/copied without editing the log buffer.
- The dashboard commands are translated to Indonesian and arranged in two columns.
- `conf/conf_client.yml` uses `#39FF14` as the primary Matrix-green UI color.

## Verification

- Python compilation passed for the modified UI and quickstart modules.
- Rendered static header contains no tab characters or mojibake.
- The pre-fix reproduction showed the listener was collected after garbage collection; the retained-reference model keeps it alive.
- The previous Demo log still records the old connector error and must not be treated as evidence of a post-patch run. A fresh Demo run is required for runtime confirmation.
