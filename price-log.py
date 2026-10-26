#!/usr/bin/env python3
"""The daily Riftbound price log, published as static JSON to a public Cloudflare R2 bucket for the RiftTally app.

  price-log.py publish <dir> <url>
      Writes TCGCSV's latest category 89 prices to <dir>/days/<day>.json, as
      {"<productId>": {"<subTypeName>": {"market", "low", "mid"}}} with null prices left out, and the sorted list of days
      to <dir>/days.json, merged with the index published at <url>. Writes nothing when <url> has the day. The day is the
      UTC day TCGCSV last refreshed (last-updated.txt, ~20:00 UTC daily), not the clock.
  price-log.py export <dir> <prices.db> [<url>]
      Writes every day in the Mac's original price log the same way, for backfill.sh.
"""
import json, os, re, sqlite3, sys, time, urllib.error, urllib.request

USER_AGENT = "riftbound-price-log/1.0 (+https://github.com/michael-huang87/riftbound-price-log)"


def get(url):
    time.sleep(0.25)  # TCGCSV usage guidelines
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": USER_AGENT}), timeout=60) as r:
        return r.read()


def today():
    """TCGCSV's groups and the UTC day it last refreshed the prices. Not the groups file's Last-Modified: that moves
    only when a set is added, and the prices refresh daily under it."""
    day = get("https://tcgcsv.com/last-updated.txt").decode()[:10]  # "2026-10-25T20:05:50+0000"
    # The day names a file and a bucket key: never let a malformed response write outside days/.
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day):
        sys.exit(f"unexpected last-updated.txt: {day!r}")
    return json.loads(get("https://tcgcsv.com/tcgplayer/89/groups"))["results"], day


def fetch(groups):
    """Every group's prices, as the JSON the app reads for a day."""
    prices = {}
    for group in groups:
        for row in json.loads(get(f"https://tcgcsv.com/tcgplayer/89/{group['groupId']}/prices"))["results"]:
            quote = {k: row[f"{k}Price"] for k in ("market", "low", "mid") if row[f"{k}Price"] is not None}
            if quote:
                prices.setdefault(str(row["productId"]), {})[row["subTypeName"]] = quote
    if not prices:
        sys.exit("no prices returned, not logging an empty day")
    print(f"fetched {sum(map(len, prices.values()))} prices for {len(prices)} products")
    return json.dumps(prices, sort_keys=True, separators=(",", ":"))


def published(url):
    """The days already in the bucket. The query string skips a cached copy, so a stale index never drops a day."""
    try:
        return json.loads(get(f"{url}/days.json?{int(time.time())}"))
    except urllib.error.HTTPError as e:
        if e.code == 404:  # an empty bucket
            return []
        raise


def write(out, days, day, prices):
    """One day's file, then the index naming it."""
    os.makedirs(os.path.join(out, "days"), exist_ok=True)
    with open(os.path.join(out, "days", f"{day}.json"), "w") as f:
        f.write(prices)
    days.append(day)
    with open(os.path.join(out, "days.json"), "w") as f:
        json.dump(sorted(set(days)), f)
    print(f"wrote {out}/days/{day}.json")


def publish(out, url):
    groups, day = today()
    days = published(url)
    if day in days:
        print(f"{day} published, skipping")
        return
    write(out, days, day, fetch(groups))


def export(out, db, url=None):
    days = published(url) if url else []
    for day, prices in sqlite3.connect(f"file:{db}?mode=ro", uri=True).execute("select day, prices from price_days order by day"):
        write(out, days, day, prices)


if __name__ == "__main__":
    if sys.argv[1:2] == ["publish"] and len(sys.argv) == 4:
        publish(*sys.argv[2:])
    elif sys.argv[1:2] == ["export"] and len(sys.argv) in (4, 5):
        export(*sys.argv[2:])
    else:
        sys.exit(__doc__)
