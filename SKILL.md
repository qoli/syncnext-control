---
name: syncnext-control
description: Search the user's running Syncnext, read paged playback history, inspect episodes and source quality, start or stop playback, and query playback through its local HTTP API. Use for media tasks on a reachable Syncnext instance.
---

# Syncnext Control

Use the running App's sources and playback engine. Syncnext must be in the foreground, with **Settings → Network → Local Agent API** enabled. Get its displayed HTTP address from the user or the task's existing configuration. The API needs no access token.

Install and update from [qoli/syncnext-control](https://github.com/qoli/syncnext-control) following its README. The App's **Install Agent Skill** settings row shows a QR Code for its built-in setup page, with a copyable prompt containing this device's HTTP address. Accepted operations show start and terminal notifications by default; read requests and polling stay quiet. The user can turn off **Show Agent operation notifications** in the same settings section.

This folder is a portable skill. Copy it into the Agent's skill directory. The client needs Python 3.10+ and no third-party packages. Configure `SYNCNEXT_URL` (for example `http://192.168.1.20:11330`), or pass `--url`. Use the displayed address of the intended device. `127.0.0.1` refers to the Agent's own host and works for a local Simulator, not a separate Apple TV.

Run the client relative to this skill's location:

```bash
python3 scripts/syncnext.py status
python3 scripts/syncnext.py sources
python3 scripts/syncnext.py history
python3 scripts/syncnext.py history --page 2
python3 scripts/syncnext.py search '反黑先鋒'
python3 scripts/syncnext.py episodes ITEM_ID
python3 scripts/syncnext.py probe EPISODE_ID
python3 scripts/syncnext.py play EPISODE_ID
python3 scripts/syncnext.py playback
python3 scripts/syncnext.py stop
```

Use IDs returned by this App instance. Items, episodes and lines are temporary handles; request fresh results after an App restart, background transition, API disable, or session clear. Source IDs identify enabled sources without exposing subscription URLs. `search --source-id ID` restricts the search to that source; repeat it to select several. Without the flag, the App searches all enabled searchable sources.

When asked to review viewing history or preferences, use `history` and follow `nextPage` until it is `null`; each page contains up to 1000 records. History includes older episodes hidden from the home screen. These are saved resume positions, not viewing sessions: position and progress do not measure time actually watched, and record counts do not measure repeat views. `playedAt` is the saved playback-start timestamp. Missing values remain unknown. These records have no viewer identity, and `sourceType` is a technical source kind rather than a cat-source subscription or provider. Keep preference inferences distinct from observed records. Each page reads current App data, so changes during pagination can shift records between pages.

Search results are candidates, not proof of the intended work. Match title and the available year/description, then fetch episodes. Resolve ambiguity that changes the work or episode before playing. When the user has asked for a specific work and episode and the match is clear, execute playback within that request. Successful `play` means the real player reached readiness; query `playback` to report its current state and progress.

To switch content, identify the new episode first. If `playback` shows a mounted player, run `stop`, then `play NEW_EPISODE_ID` and query `playback`. `stop` closes the player through the App's normal exit flow and returns after dismissal; it also succeeds when already idle. It preserves episode handles. A running play operation that has not mounted a player must be cancelled with `cancel ID` before switching. Session `clear` and operation cancellation do not close an already playing item.

For the best source, probe the requested episode across the relevant candidates. `episodes` also returns source lines where supported; select one with `episodes ITEM_ID --line-id LINE_ID`, then probe its returned episode handle. Compare FFmpeg-probed video dimensions, codec, frame rate, bit depth and HDR metadata against the user's display and preferences. A source's “4K” label is a declaration. A missing measurement remains unknown. The probe does not expose video bitrate or measure network throughput. Report which measured facts support the choice and any candidates that could not be assessed. Do not claim a universal best source when probes are incomplete.

The client waits for asynchronous operations by default. `--no-wait` returns the operation immediately; `operation ID` queries it, and `cancel ID` cancels it. `partial` preserves successful results alongside source errors and exits with code 3. Do not treat all-source failures as “no results,” silently expand a restricted search, choose an alternate work, or replay a failed playback request. If the App is unreachable or not ready, report that state; this skill does not wake Syncnext or host a cloud search service.

Read [HTTP API](references/http-api.md) for raw requests, error states, lifecycle, quality limitations, client options, and the reproducible Simulator acceptance command.
