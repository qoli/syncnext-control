#!/usr/bin/env python3
"""Portable stdlib client for Syncnext Local Agent API v1."""

import argparse
import json
import os
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen


class ClientError(Exception):
    def __init__(self, payload, exit_code=2):
        self.payload = payload
        self.exit_code = exit_code


class Client:
    def __init__(self, url, request_timeout=30):
        parts = urlsplit(url)
        if parts.scheme not in ("http", "https") or not parts.netloc or parts.query or parts.fragment:
            raise ClientError({"error": {"code": "invalid_url", "message": "Use the App's HTTP base URL."}})
        self.url = url.rstrip("/")
        self.request_timeout = request_timeout

    def request(self, method, path, body=None):
        data = None if body is None else json.dumps(body, ensure_ascii=False).encode()
        request = Request(self.url + "/api/v1/" + path, data=data, method=method,
                          headers={"Content-Type": "application/json"})
        try:
            with urlopen(request, timeout=self.request_timeout) as response:
                return response.status, json.load(response)
        except HTTPError as error:
            try:
                payload = json.load(error)
            except (ValueError, UnicodeError):
                payload = {"error": {"code": "http_error", "message": "Non-JSON API error response."}}
            raise ClientError({"httpStatus": error.code, **payload}) from None
        except (URLError, TimeoutError, OSError):
            # Avoid echoing credential-bearing URLs or an upstream error page.
            raise ClientError({"error": {"code": "connection_failed",
                                        "message": "Cannot reach this Syncnext instance. No request was retried."}}) from None
        except (ValueError, UnicodeError):
            raise ClientError({"error": {"code": "invalid_response", "message": "Expected a JSON API response."}}) from None

    def wait(self, operation, timeout=None):
        deadline = None if timeout is None else time.monotonic() + timeout
        while operation.get("state") in ("running", "cancelling"):
            if deadline is not None and time.monotonic() >= deadline:
                raise ClientError({"error": {"code": "wait_timeout",
                                            "message": "Stopped waiting; the operation is still owned by the App."},
                                   "operation": operation})
            time.sleep(0.25)
            _, operation = self.request("GET", "operations/" + quote(operation["id"], safe=""))
        return operation


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--url", default=os.environ.get("SYNCNEXT_URL"))
    result.add_argument("--request-timeout", type=float, default=30,
                        help="HTTP request timeout in seconds; never retries a mutation (default: 30)")
    result.add_argument("--wait-timeout", type=float, help="Stop observing after this many seconds; does not cancel")
    result.add_argument("--no-wait", action="store_true", help="Return asynchronous operation immediately")
    commands = result.add_subparsers(dest="command", required=True)
    for name in ("status", "sources", "playback", "stop", "clear"):
        commands.add_parser(name)
    for name, help_text in (("history", "Read resume checkpoints"),
                            ("activities", "Read viewing activities with archived TMDB JSON")):
        history = commands.add_parser(name, help=help_text + ", 1000 records per page")
        history.add_argument("--page", type=int, default=1, help="Page number, starting at 1 (default: 1)")
    search = commands.add_parser("search")
    search.add_argument("keyword")
    search.add_argument("--source-id", action="append")
    episodes = commands.add_parser("episodes")
    episodes.add_argument("id")
    episodes.add_argument("--line-id")
    open_playlist = commands.add_parser("open-playlist", help="Open an item's playlist on the TV without starting playback")
    open_playlist.add_argument("id")
    for name in ("probe", "play", "operation", "cancel"):
        command = commands.add_parser(name)
        command.add_argument("id")
    seek = commands.add_parser("seek")
    seek.add_argument("seconds", type=float)
    return result


def command_request(args):
    if args.command in ("status", "sources", "playback"):
        return "GET", args.command, None
    if args.command == "history":
        return "GET", "history?page=" + str(args.page), None
    if args.command == "activities":
        return "GET", "viewing-activities?page=" + str(args.page), None
    if args.command == "search":
        body = {"keyword": args.keyword}
        if args.source_id is not None:
            body["sourceIds"] = args.source_id
        return "POST", "search", body
    if args.command == "episodes":
        return "POST", "items/" + quote(args.id, safe="") + "/episodes", (
            {"lineId": args.line_id} if args.line_id else {})
    if args.command == "open-playlist":
        return "POST", "items/" + quote(args.id, safe="") + "/open", {}
    if args.command == "probe":
        return "POST", "episodes/" + quote(args.id, safe="") + "/probe", {}
    if args.command == "play":
        return "POST", "playback", {"episodeId": args.id}
    if args.command == "stop":
        return "POST", "playback/stop", {}
    if args.command == "seek":
        return "POST", "playback/seek", {"positionSeconds": args.seconds}
    if args.command == "clear":
        return "DELETE", "session", None
    return ("DELETE" if args.command == "cancel" else "GET"), "operations/" + quote(args.id, safe=""), None


def emit(payload):
    print(json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False))


def main(argv=None):
    args = parser().parse_args(argv)
    client = None
    owned_operation = None
    try:
        if not args.url:
            raise ClientError({"error": {"code": "configuration_required",
                                        "message": "Set SYNCNEXT_URL to the App's HTTP base URL."}})
        if args.request_timeout <= 0 or args.wait_timeout is not None and args.wait_timeout <= 0:
            raise ClientError({"error": {"code": "invalid_timeout", "message": "Timeouts must be positive."}})
        client = Client(args.url, args.request_timeout)
        status, payload = client.request(*command_request(args))
        if status == 202:
            owned_operation = payload["id"]
        if not args.no_wait and (status == 202 or args.command == "operation"):
            payload = client.wait(payload, args.wait_timeout)
        emit(payload)
        return 0 if args.command == "cancel" else {"failed": 2, "partial": 3, "cancelled": 130}.get(payload.get("state"), 0)
    except KeyboardInterrupt:
        if client and owned_operation:
            try:
                _, payload = client.request("DELETE", "operations/" + quote(owned_operation, safe=""))
                emit(payload)
            except ClientError as error:
                emit(error.payload)
        return 130
    except ClientError as error:
        emit(error.payload)
        return error.exit_code


if __name__ == "__main__":
    sys.exit(main())
