# riftbound-price-log

A daily log of Riftbound card prices from [TCGCSV](https://tcgcsv.com), published as static JSON for the RiftTally app at <https://prices.rifttally.com>.

A scheduled GitHub Action runs `price-log.py` once a day after TCGCSV refreshes. It writes the day's prices and the list of logged days, and `upload.sh` publishes them:

| File | Contents |
|---|---|
| `days.json` | the sorted list of logged days |
| `days/<day>.json` | `{"<productId>": {"<subTypeName>": {"market", "low", "mid"}}}` |

This repo holds only the code. The price data lives at <https://prices.rifttally.com>.

## Notice

RiftTally and this price log are unofficial and fan-made. They are not affiliated with or endorsed by Riot Games. Riftbound is a trademark of Riot Games.

Price data comes from [TCGCSV](https://tcgcsv.com), which republishes [TCGplayer](https://www.tcgplayer.com) prices. Thanks to both.
