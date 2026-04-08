#!/usr/bin/env python3
"""
cidrs2ips: Expands a file of CIDR ranges to individual IPs, one per line.
Usage: python3 cidrs2ips.py <file>
"""

import sys
import ipaddress


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <file>", file=sys.stderr)
        sys.exit(1)

    path = sys.argv[1]
    try:
        with open(path) as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: file not found: {path}", file=sys.stderr)
        sys.exit(1)

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            network = ipaddress.ip_network(line, strict=False)
            for ip in network.hosts():
                print(ip)
        except ValueError:
            print(f"Warning: skipping invalid entry: {line}", file=sys.stderr)


if __name__ == "__main__":
    main()
