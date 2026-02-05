#!/usr/bin/env python3
import argparse
import os
import sys
from pprint import pprint
from typing import Any

import requests

from context7_client import Context7Client


def parse_args():
    parser = argparse.ArgumentParser(description="Runner for Context7 search/context endpoints")

    parser.add_argument(
        "--base-url",
        default=os.getenv("CONTEXT7_BASE_URL", "https://context7.com/api"),
        help="Context7 base URL (env CONTEXT7_BASE_URL). Default: https://context7.com/api",
    )

    parser.add_argument(
        "--api-key",
        default=os.getenv("CONTEXT7_API_KEY"),
        help="Context7 API key (env CONTEXT7_API_KEY). Usually starts with 'ctx7sk'.",
    )

    parser.add_argument(
        "--action",
        choices=("search", "context", "both"),
        default="search",
        help="Action to perform: search | context | both (search -> context on first result). Default: search",
    )

    # For search
    parser.add_argument("--library-name", help="Library name for search (e.g. react). Required for 'search' and 'both' actions.")
    # For context
    parser.add_argument("--library-id", help="Library ID for get_context (e.g. /vercel/next.js). Required for 'context' action.")
    parser.add_argument("--query", help="User query used for ranking / context (required).")

    parser.add_argument("--type", choices=("json", "txt"), default="json", help="Format type for get_context. Default: json")

    return parser.parse_args()


def exit_with(err: Exception, code: int = 1):
    print("❌", str(err))
    sys.exit(code)


def print_context_json(data: Any):
    """
    Nicely print structured context response (codeSnippets + infoSnippets)
    If non-dict (text), print raw.
    """
    if not isinstance(data, dict):
        print(str(data))
        return

    code_snippets = data.get("codeSnippets", [])
    info_snippets = data.get("infoSnippets", [])

    print(f"codeSnippets: {len(code_snippets)}")
    for i, c in enumerate(code_snippets, 1):
        title = c.get("codeTitle")
        lang = c.get("codeLanguage")
        tokens = c.get("codeTokens")
        page = c.get("pageTitle")
        print(f"[{i}] {title!r} ({lang}, tokens={tokens}) page={page}")
        # print first example snippet if available
        code_list = c.get("codeList", [])
        if code_list:
            example = code_list[0]
            print("    Example:", example.get("language"))
            # Print a short preview of the code
            code_preview = example.get("code", "").splitlines()[:8]
            for line in code_preview:
                print("     ", line)
            if len(example.get("code", "").splitlines()) > 8:
                print("     ... (truncated)")

    print("\ninfoSnippets:", len(info_snippets))
    for i, inf in enumerate(info_snippets, 1):
        breadcrumb = inf.get("breadcrumb")
        tokens = inf.get("contentTokens")
        preview = inf.get("content", "").splitlines()[:6]
        print(f"[{i}] {breadcrumb} (tokens={tokens})")
        for line in preview:
            print("    ", line)
        if len(inf.get("content", "").splitlines()) > 6:
            print("    ... (truncated)")


def main():
    args = parse_args()

    if args.api_key and not args.api_key.startswith("ctx7sk"):
        print("⚠️  Provided API key does not start with 'ctx7sk' (expected per spec).")

    if args.action in ("search", "both") and not args.library_name:
        exit_with(ValueError("--library-name is required for action 'search' or 'both'"))
    if args.action == "context" and not args.library_id:
        exit_with(ValueError("--library-id is required for action 'context'"))
    if not args.query:
        exit_with(ValueError("--query is required"))

    client = Context7Client(base_url=args.base_url, api_key=args.api_key)

    try:
        if args.action == "search":
            results = client.search(library_name=args.library_name, query=args.query)
            print_search_results(results)

        elif args.action == "context":
            # call get_context directly
            resp = client.get_context(library_id=args.library_id, query=args.query, type_=args.type)
            print_context_json(resp)

        elif args.action == "both":
            # search -> take first result -> call get_context with its id
            results = client.search(library_name=args.library_name, query=args.query)
            if not results:
                print("⚠️  No search results returned; aborting 'both'.")
                sys.exit(0)
            first = results[0]
            lib_id = first.get("id")
            if not lib_id:
                print("⚠️  First search result has no 'id'; aborting.")
                sys.exit(1)
            print(f"Using first search result id={lib_id} title={first.get('title')!r}")
            resp = client.get_context(library_id=lib_id, query=args.query, type_=args.type)
            print_context_json(resp)

    except requests.HTTPError as e:
        # requests.HTTPError often includes the body (we raised with helpful message)
        exit_with(e)
    except Exception as e:
        exit_with(e)


def print_search_results(results):
    if not results:
        print("⚠️  No results.")
        return
    print(f"✅ {len(results)} result(s):\n")
    for i, lib in enumerate(results, 1):
        lib_id = lib.get("id")
        title = lib.get("title")
        desc = lib.get("description")
        branch = lib.get("branch")
        last_update = lib.get("lastUpdateDate")
        trust = lib.get("trustScore")
        stars = lib.get("stars")
        print(f"[{i}] id={lib_id} title={title!r} branch={branch} updated={last_update} trust={trust} stars={stars}")
        if desc:
            print("    ", desc)
    print("\n--- Full JSON of first result ---\n")
    pprint(results[0])


if __name__ == "__main__":
    main()
