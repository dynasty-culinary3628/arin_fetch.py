#!/usr/bin/env python3
"""
arin-fetch: returns all IP ranges registered to an organization in ARIN.
Usage: python arin_fetch.py <org_name>
"""

import sys
import argparse
import yaml
import requests


def load_config(path="config.yml"):
    with open(path) as f:
        return yaml.safe_load(f)


def val(obj):
    """Unwrap ARIN's JSON scalar wrapper: {"$": "value"} -> "value"."""
    if isinstance(obj, dict):
        return obj.get("$", obj)
    return obj


def search_orgs(base_url, name):
    """Search for orgs by name. Appends * wildcard automatically."""
    if not name.endswith("*"):
        name = name + "*"
    url = f"{base_url}/orgs;name={requests.utils.quote(name, safe='*')}"
    resp = requests.get(url, headers={"Accept": "application/json"})
    if resp.status_code == 404:
        return [], False
    resp.raise_for_status()
    data = resp.json()

    orgs_data = data.get("orgs", {})
    if not orgs_data:
        return [], False

    limit_exceeded_raw = orgs_data.get("limitExceeded", {})
    limit_exceeded = val(limit_exceeded_raw) == "true"

    org_refs = orgs_data.get("orgRef", [])
    # Single result comes back as a dict, not a list
    if isinstance(org_refs, dict):
        org_refs = [org_refs]

    orgs = []
    for ref in org_refs:
        orgs.append({
            "handle": ref.get("@handle", ""),
            "name": ref.get("@name", ""),
        })

    return orgs, limit_exceeded


def get_networks(base_url, handle):
    """Fetch all network blocks for an org handle."""
    url = f"{base_url}/org/{handle}/nets"
    resp = requests.get(url, headers={"Accept": "application/json"})
    if resp.status_code == 404:
        return []
    resp.raise_for_status()
    data = resp.json()

    nets_data = data.get("nets", {})
    if not nets_data:
        return []

    net_refs = nets_data.get("netRef", [])
    if isinstance(net_refs, dict):
        net_refs = [net_refs]

    cidrs = []
    for ref in net_refs:
        start = ref.get("@startAddress", "")
        end = ref.get("@endAddress", "")
        handle_str = ref.get("@handle", "")
        name = ref.get("@name", "")
        cidrs.append({
            "handle": handle_str,
            "name": name,
            "startAddress": start,
            "endAddress": end,
        })

    return cidrs


def get_network_cidrs(base_url, net_handle):
    """Fetch CIDR blocks for a specific network handle."""
    url = f"{base_url}/net/{net_handle}"
    resp = requests.get(url, headers={"Accept": "application/json"})
    if resp.status_code == 404:
        return []
    resp.raise_for_status()
    data = resp.json()

    net = data.get("net", {})
    net_blocks = net.get("netBlocks", {})
    if not net_blocks:
        return []

    block_list = net_blocks.get("netBlock", [])
    if isinstance(block_list, dict):
        block_list = [block_list]

    cidrs = []
    for block in block_list:
        start = val(block.get("startAddress", ""))
        cidr_len = val(block.get("cidrLength", ""))
        if start and cidr_len:
            cidrs.append(f"{start}/{cidr_len}")
    return cidrs


def main():
    parser = argparse.ArgumentParser(description="Fetch all IP ranges for an ARIN organization.")
    parser.add_argument("org_name", nargs="+", help="Organization name to search for")
    parser.add_argument("--plain", action="store_true", help="Output plain list of CIDRs only")
    parser.add_argument("--output", metavar="FILE", help="Save output to file in addition to stdout")
    args = parser.parse_args()

    org_name = " ".join(args.org_name)
    config = load_config()
    base_url = config["arin"]["base_url"]

    log_file = open(args.output, "w") if args.output else None

    def output(line=""):
        print(line)
        if log_file:
            log_file.write(line + "\n")

    if not args.plain:
        output(f"Searching for org: {org_name}")

    orgs, limit_exceeded = search_orgs(base_url, org_name)

    if not orgs:
        if not args.plain:
            output("No organizations found.")
        if log_file:
            log_file.close()
        sys.exit(0)

    if not args.plain:
        if limit_exceeded:
            output(f"Warning: search returned more than 10 results; only the first 10 are shown. Try a more specific name.")
        output(f"Found {len(orgs)} org(s):\n")
        for org in orgs:
            output(f"  [{org['handle']}] {org['name']}")
        output()

    for org in orgs:
        handle = org["handle"]
        net_refs = get_networks(base_url, handle)

        if not net_refs:
            continue

        all_cidrs = []
        for ref in net_refs:
            cidrs = get_network_cidrs(base_url, ref["handle"])
            if cidrs:
                all_cidrs.extend(cidrs)
            else:
                all_cidrs.append(f"{ref['startAddress']} - {ref['endAddress']}")

        if args.plain:
            for cidr in all_cidrs:
                output(cidr)
        else:
            output(f"=== {org['name']} ({handle}) ===")
            for cidr in all_cidrs:
                output(f"  {cidr}")
            output()

    if log_file:
        log_file.close()


if __name__ == "__main__":
    main()
