# Syncnext Local Agent API v1

This is the owning contract for the App API and the portable `syncnext-control` Skill. The API runs inside Syncnext's existing HTTP server, normally port `11330`. It uses the App's configured searchable sources and normal episode/player handlers. It needs no cloud service or AI key. Screenshot recognition and identifying a work with TMDB/web search belong to the calling Agent.

## Enable and connect

Open **設定 → 網絡 → 本地 Agent API → 允許本地 Agent**. It defaults off. The page uses the App's standard settings components to show the switch, HTTP address and session clear. When enabled, clients that can reach the displayed address can call `/api/v1` without an access token or `Authorization` header.

The App must stay running in the foreground. An API is not a tvOS background execution entitlement. `GET /status` reports `ready: false` during initialization; domain operations reject with `409 not_ready`. Disabling returns `503 api_disabled`. No request wakes the App or searches remotely when it is offline.

Copy the complete `Skills/syncnext-control` folder into the local Agent's skill directory. The bundled client requires Python 3.10+ with the standard library. Set:

```bash
export SYNCNEXT_URL='http://192.168.1.20:11330'
python3 scripts/syncnext.py status
```

`--url` overrides `SYNCNEXT_URL`. No other connection credential is required.

The **安裝 Agent Skill** settings row uses the App's standard QR Code view to open `http://DEVICE:11330/agent.html`. This bundled static page remains available while the API is disabled. It links to the independent public [Skill repository](https://github.com/qoli/syncnext-control) and provides a copyable installation prompt with the URL of the device serving the page. The Skill can be updated from that repository independently of App releases.

**顯示 Agent 操作通知** defaults on and is persisted locally. Every request to the enabled `/api/v1` API invokes the existing `MessageStatus` notification component with a readable operation name, including status/operation polling, search, episodes, quality probe, playback, seek, stop, cancellation and session clear. The component retains its normal display duration and duplicate-message behavior. Turning the setting off suppresses these Agent notifications without changing API behavior. Static setup-page requests are not control API operations.

## Routes

All paths below are relative to `/api/v1`. Responses are JSON with `Cache-Control: no-store`. Mutation bodies are JSON objects; unknown fields are rejected. There is no GET mutation endpoint.

| Method and path | Body / response |
| --- | --- |
| `GET /status` | `apiVersion`, `ready`, `deviceName`, `capabilities`, `handleLifetime` |
| `GET /sources` | `sources: [{id, name}]`; enabled searchable source snapshot |
| `POST /search` | `{keyword, sourceIds?}` → `202` search operation; omitted `sourceIds` searches all enabled sources |
| `GET /operations/{id}` | Current operation snapshot, including partial search results while running |
| `DELETE /operations/{id}` | Request cancellation; `cancelling` until work observes cancellation; never undoes playback already started |
| `POST /items/{id}/episodes` | `{lineId?}` → `202` episode operation |
| `POST /episodes/{id}/probe` | `{}` → `202` resolution and quality operation, without opening the player |
| `POST /playback` | `{episodeId}` → `202` play operation; real player readiness determines success |
| `GET /playback` | Real mounted player state, position, duration, media and seekability |
| `POST /playback/stop` | `{}` → playback information after closing the mounted player; already idle succeeds |
| `POST /playback/seek` | `{positionSeconds}`; finite nonnegative seconds → updated playback information |
| `DELETE /session` | Cancel operations and invalidate item, line, episode and operation handles |

Source IDs are hashes of the App's source identity, so subscription URLs containing credentials need not leave the App. Unknown requested source IDs fail explicitly with `source_not_found`; the App never broadens a restricted search. Source settings are read anew for each search. Source ordering is not a quality ranking.

## Asynchronous operations

Search, episode loading, resolution/probe and playback return `202` immediately:

```json
{"id":"OPERATION_ID","kind":"search","state":"running","stage":"search","result":{},"errors":[]}
```

Poll `GET /operations/OPERATION_ID`. `state` is `running`, `cancelling`, `succeeded`, `partial`, `failed` or `cancelled`. `stage` distinguishes source loading, search, resolve, probe and playback readiness. Results remain in App memory until session clear or API disable; they are not added to the user database. Search results stream into `result.items` as sources finish. A search result has:

```json
{
  "keyword":"反黑先鋒",
  "sourceCount":2,
  "items":[{"id":"ITEM_ID","sourceId":"SOURCE_ID","sourceName":"Example","title":"反黑先鋒","description":"1999","coverURL":""}],
  "sources":[{"sourceId":"SOURCE_ID","name":"Example","state":"completed","count":1,"elapsedMilliseconds":100}]
}
```

Source outcomes follow the search engine: `completed`, `failed`, `cancelled`. A successful empty search is `succeeded` with `items: []`. Some sources failing yields `partial` with preserved candidates and per-source errors. All sources failing yields `failed` with `all_sources_failed`, never a successful empty result. No enabled searchable source yields `no_searchable_sources`.

The Python client waits automatically for operations. `--no-wait` returns the initial snapshot; `operation ID` waits/queries it, and `cancel ID` requests cancellation. Ctrl-C requests cancellation of an operation created by that invocation. `--request-timeout` bounds each HTTP request (default 30 seconds); `--wait-timeout` optionally stops observation without cancelling the App operation. Neither setting retries a request. After a connection error on a mutation, inspect known operation/player state before issuing another mutation: the App may already have accepted it.

Client exit codes: `0` successful request/result (including an accepted cancellation request), `2` API/operation/configuration error, `3` partial search, `130` interrupted or observed cancelled operation. JSON is printed for API results and errors. Error responses use `{error: {code, message}}`; failed operations have `errors: [...]` instead.

## Episodes and source lines

The episode operation's `result` is:

```json
{
  "itemId":"ITEM_ID",
  "episodes":[{"id":"EPISODE_ID","mediaTitle":"Example","title":"第02集","episodeNumber":2,"line":"原畫","probeSupported":true}],
  "lines":[{"id":"LINE_ID","name":"原畫","selected":true}]
}
```

Line controls come from the existing source's episode panel actions. Some sources expose all lines in the episode list and return `lines: []`; use each episode's `line` in that case. For sources with panel actions, request episodes once to get line handles, then `episodes ITEM_ID --line-id LINE_ID` to select and refetch that line. It changes that source instance's selected line just as the App UI does. Returned episode handles retain their own handlers, so playback uses the chosen episode.

The API serializes episode loading, resolution/probe and playback because existing source handlers may share selected-line and parser state. A second such operation receives `409 operation_busy`; search operations can run independently. A player already mounted receives `409 player_busy` on a new play request. Close it with `POST /playback/stop` before starting another. Session clear/cancellation does not stop an already mounted player.

An empty episode result is `episodes_unavailable`; many existing source handlers return an empty list after an upstream detail error, so the API cannot infer whether the work has no episodes or its detail request failed. It does not invent an episode. Unknown/expired handles receive `404` with `item_not_found`, `episode_not_found`, `line_not_found` or `operation_not_found`.

Item/episode/line handles are process-local and invalidate on background entry, restart, disable or session clear. A cancelled operation's previously published results may be incomplete. Request fresh results after cancellation before choosing an episode. There is no fixed result count or retention timer; clear a long Agent session explicitly.

## Quality probe and selection

The probe invokes the chosen episode's existing resolver, preserving its required HTTP headers, then calls Hybrid's AetherEngine demux-only FFmpeg probe on a background task. HLS input uses the engine's existing reader. It does not create a playback session, AVPlayer/AVPlayerItem, renderer or audio session. Cancellation is forwarded through the engine's probe cancellation token. Normal HTTP VOD, T4 and website/embedded cat plugin episodes expose resolvers. Other episode providers return `probeSupported: false` and `422 probe_unsupported`. Resolution/container errors produce failed operations; missing stream metadata stays unknown. The App does not implement a second media parser.

The probe's `result` separates `declared` episode/line labels from `measured` data:

| Measured field | Meaning |
| --- | --- |
| `method`, `measuredAt` | `aether-ffmpeg`, timestamp of this inspection |
| `containerOpened` | FFmpeg opened the container and read stream information; not proof of decoded playback |
| `videoTracks` | Source width/height, codec, frame rate, bit depth, pixel format, profile, color primaries, transfer and dynamic range |
| `audioTracks` | Codec, channel count, language and declared audio bitrate where available |
| `durationSeconds` | Known positive duration, otherwise `null` |
| `probeElapsedSeconds` | Resolver-independent metadata inspection time, not startup latency |
| `throughputBytesPerSecond` | `null`; this version does not measure sustained throughput |
| `limitations` | Limits of metadata-only inspection |

Dynamic range comes from Aether's source metadata; an untagged SDR default remains unknown when transfer information is absent. The base probe does not run the optional Atmos/HDR10+ detail passes. Aether's public source probe does not expose video bitrate, so `estimatedBitrateBps` remains `null`; it is not replaced by network speed or a source label. The API provides no fabricated quality score and does not promise exhaustive adaptive variant inspection or decoded compatibility on another device.

Probe results are approximate stream samples for candidate ranking, not a frame-by-frame assessment of the whole episode. In particular, an HLS sample can differ from the beginning or currently displayed stream. Confirm the actual player's output after selection. Do not extend Aether's probe with exhaustive segment/variant analysis merely to make the ranking precise. Report unmeasurable candidates honestly. Probing does not change playback or pass the resolved URL to the Agent. Starting playback resolves again so expiring media URLs are not reused from an earlier probe.

## Playback

The API populates the same shared media/episode state used by the App and calls the episode's normal play handler. `succeeded` means the player reported readiness, not just that a URL was found. Player/source errors fail the play operation; the API never switches sources automatically.

`POST /playback/stop` closes the mounted player through its normal dismissal and teardown, including progress saving and Hybrid resource cleanup. It returns `200` with playback information after dismissal, normally `idle`; calling it while idle also succeeds. It preserves search and episode handles and does not cancel source operations. If a play operation is still resolving and has not mounted a player, cancel that operation first. To switch content with the Skill client:

```bash
python3 scripts/syncnext.py stop
python3 scripts/syncnext.py play NEW_EPISODE_ID
python3 scripts/syncnext.py playback
```

`GET /playback` returns `state` (`idle`, `loading`, `playing`, `paused`, `waiting`, `failed`), `media` (available `title`, `episode`, `sourceType`, `coverURL`), `positionSeconds`, `durationSeconds`, `rate`, `canSeek`, and `seekableRanges: [{startSeconds, endSeconds}]`. Without a mounted player the state is `idle`, media/time/rate are `null`, `canSeek` is false and ranges are empty. Unknown duration stays `null`. Seek targets must lie in a reported seekable range; the response reports the actual landing time and preserves playing/paused state. A `waiting` response can mean decoding/buffering is still pending. In the source checkout, the engine's owning reference is `Docs/SPEC/playback_http_runtime.md`.

## Reproducible Simulator acceptance

Build the Debug App for an arm64 tvOS Simulator with Xcode, then run from the repository:

```bash
python3 Scripts/run_local_agent_api_simulator.py --app /absolute/path/to/Debug-appletvsimulator/SyncNext.app
```

The runner requires installed `ffmpeg` and the tvOS 27.0 Simulator runtime. It creates and deletes its own temporary Apple TV Simulator, with isolated HTTP/WebSocket ports. It never targets `SyncNext Data`. It generates MP4, HLS and MKV media and local VOD/T4 fixtures, then drives this exact Skill client through search, episode choice, metadata probing, authenticated T4 resolution, real playback, seek, stop and switching to another source/episode. It checks idle stop, rejection of malformed stop requests, playback progress, partial/all-source errors, successful empty results, in-flight engine-probe cancellation, unknown IDs, token-free requests, disabled state and the bundled setup page. The native Debug case checks notification suppression/display and persistence, the App's source-diagnostic resolution label, selected episode, mounted AVPlayer clock progress and cleanup. Hybrid's AVKit carrier dimensions do not represent source resolution.

Evidence is retained under `.artifacts/local-agent-api/RUN_ID/` (JSON, fixture requests, App console). For visual acceptance, first create/boot a task-owned temporary device and attach its display with Xcode's device interaction session; pass `--temporary-simulator-udid UUID --await-ui-check`. The runner pauses first at `ui-stop-checkpoint.json` to inspect the closed player and then at `ui-checkpoint.json` to inspect the new playback. Capture the current screenshot/hierarchy for each, writing the corresponding `ui-stop-check.json` or `ui-check.json` containing `{"passed":true}` only after inspection, or `false` with the observed failure. End the interaction session before submitting the final check. The runner then completes native assertions and deletes the temporary device. Do not pass a shared or retained device: the temporary-UDID option transfers ownership for deletion.

`python3 Tests/LocalAgent/test_client.py` separately verifies URL-only connection without an authorization header, the stop request/response, partial-result exit codes, cancellation on interrupt, no resubmission after an HTTP error, and stopping observation without cancelling a playback operation. The source checkout's existing search/session and local-server tests cover their respective engines.

This acceptance proves the local App/Skill/engine flow with controlled sources. It does not prove availability of third-party subscriptions or physical Apple TV playback.
