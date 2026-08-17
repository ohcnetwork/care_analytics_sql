#!/usr/bin/env python3
"""Helpers for diagnosing JIRA API access in the analytics-review workflow.

Parses the JSON that `GET https://api.atlassian.com/oauth/token/accessible-resources`
returns (the list of Atlassian sites a credential can reach) and answers two
questions for the workflow's JIRA pre-step:

    jira_sites.py cloud-id <resources.json> <configured-base-url>
        Print the cloudId to use with the scoped-token endpoint
        (https://api.atlassian.com/ex/jira/<cloudId>), chosen as: the site
        whose `url` equals the configured base URL, else the cloudId already
        embedded in an .../ex/jira/<id> base, else the only site when exactly
        one is accessible. Prints nothing when no confident answer exists.

    jira_sites.py summary <resources.json>
        Print a one-line "url (cloudId ...)" list for diagnostics.

Site URLs and cloudIds are not credentials (cloudIds appear in every browser
request to a JIRA site); nothing secret is ever read or printed here. Exit
code is always 0 — this feeds a diagnostics path that must never fail the job.
"""

import json
import sys


def load_sites(path):
    try:
        with open(path) as fh:
            data = json.load(fh)
    except Exception:
        return []
    return [s for s in data if isinstance(s, dict)] if isinstance(data, list) else []


def main():
    if len(sys.argv) < 3:
        return
    mode, path = sys.argv[1], sys.argv[2]
    sites = load_sites(path)
    if mode == "summary":
        line = "; ".join(
            "%s (cloudId %s)" % (s.get("url", "?"), s.get("id", "?")) for s in sites
        )
        print(line or "no sites accessible to this token")
    elif mode == "cloud-id":
        base = (sys.argv[3] if len(sys.argv) > 3 else "").rstrip("/")
        match = [s for s in sites if str(s.get("url", "")).rstrip("/") == base]
        if not match and "/ex/jira/" in base:
            cid = base.split("/ex/jira/", 1)[1].split("/")[0]
            match = [s for s in sites if s.get("id") == cid]
        if not match and len(sites) == 1:
            match = sites
        if match:
            print(match[0].get("id", ""))


if __name__ == "__main__":
    main()
