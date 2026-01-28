#!/usr/bin/env python3
import argparse
import os
import sys
from pprint import pprint

from context7_client import Context7Client


def parse_args():
    parser = argparse.ArgumentParser(
        description="Manual runner for Context7 /v2/libs/search (GET)"
    )

    parser.add_argument(
        "--base-url",
        default=os.getenv("CONTEXT7_BASE_URL", "https://context7.com/api"),
        help="Context7 base URL (default from CONTEXT7_BASE_URL or https://context7.com/api)",
    )

    parser.add_argument(
        "--api-key",
        default=os.getenv("CONTEXT7_API_KEY"),
        help="Context7 API key (default from CONTEXT7_API_KEY). API keys usually start with 'ctx7sk'.",
    )

    parser.add_argument(
        "--library-name",
        required=True,
        help="Library name to search for (required). Example: react",
    )

    parser.add_argument(
        "--query",
        required=True,
        help="User query used for ranking (required). Example: 'How to manage state with hooks'",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    if args.api_key and not args.api_key.startswith("ctx7sk"):
        print("⚠️  Warning: provided API key does not start with 'ctx7sk' (per spec this is expected).")

    client = Context7Client(base_url=args.base_url, api_key=args.api_key)

    print(f"Context7 base URL: {args.base_url}")
    print(f"Library name: {args.library_name}")
    print(f"Query: {args.query}")
    print("-" * 80)

    try:
        results = client.search(library_name=args.library_name, query=args.query)
    except Exception as exc:
        print("❌ Search request failed:")
        print(str(exc))
        sys.exit(1)

    if not results:
        print("⚠️  No results returned.")
        sys.exit(0)

    print(f"✅ {len(results)} result(s):\n")
    for i, lib in enumerate(results, 1):
        # print compact metadata; pretty-print full object below
        lib_id = lib.get("id")
        title = lib.get("title")
        desc = lib.get("description")
        branch = lib.get("branch")
        last_update = lib.get("lastUpdateDate")
        trust = lib.get("trustScore")
        stars = lib.get("stars")
        print(f"[{i}] id={lib_id}  title={title!r}  branch={branch}  updated={last_update}  trust={trust}  stars={stars}")
        if desc:
            print(f"    {desc}")
    print("\n--- Full JSON of first result ---\n")
    pprint(results[0])


if __name__ == "__main__":
    main()
