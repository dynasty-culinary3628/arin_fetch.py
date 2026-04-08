# arin-fetch
arin-fetch fetches all registered IP addresses for a given org. It is written in python. It is valuable during external pentests to make sure you are targeting the correct CIDR ranges.

## Usage

Basic Usage
```
python3 arin_fetch.py "Organization Name'
```

Add a flag to output only the CIDR ranges to stdout
```
python3 arin_fetch.py --plain "Organization Name'
```

Add an option to output also to a file
```
python3 arin_fetch.py --plain --output=results.log 'Organization Name'
```

Or you could do it the old fashioned way. If you want to convert the output to a list of CIDR ranges, do this:

```
cat orgname.report | grep '^  ' | grep -Ev '^  \[' | grep -Ev 'No networks found' | sed 's/^[[:space:]]*//' > orgname.cidrs
```

You could also generate orgname.cidrs in one go like so:

```
 python3 arin_fetch.py "Organization Name" | grep '^  ' | grep -Ev '^  \[' | grep -Ev 'No networks found' | sed 's/^[[:space:]]*//' > orgname.cidrs
```
