# riftbound-price-log

A daily log of Riftbound card prices from [TCGCSV](https://tcgcsv.com) (TCGplayer category 89), published as static JSON for the RiftTally app's price history charts. The app lives in a private repo; this repo is public so GitHub Actions runs the job for free.

## How it works

`.github/workflows/price-log.yml` runs `price-log.py publish` at 21:17, 23:17 and 03:17 UTC, after TCGCSV's ~20:00 UTC refresh. It reads the day TCGCSV last refreshed from `last-updated.txt`. When the bucket lacks that day, the job writes two files, and `upload.sh` uploads them to a Cloudflare R2 bucket with public read:

| File | Contents | Cache |
|---|---|---|
| `days/<day>.json` | `{"<productId>": {"<subTypeName>": {"market", "low", "mid"}}}`, about 130 KB | one year; a day never changes |
| `days.json` | the sorted list of days | five minutes |

The day file uploads first, so the index never names a missing file. A run whose day is already in the bucket uploads nothing.

There is no database or server. The app only reads public URLs. The R2 write key exists only in this repo's Actions secrets.

The job skips until `PRICE_LOG_URL` is set. Each run also re-enables the workflow, because GitHub disables a public repo's schedules after 60 days without commits.

Why Actions rather than a Cloudflare Worker cron: the job is plain Python with no dependencies, and Actions is free for public repos. On the free plan a Worker gets 10 ms of CPU per run, and parsing 14 groups of price JSON is likely over that (not measured). Workers Paid ($5/month) would lift the limit, but the job would need porting to JavaScript.

## Setup (Chamiel)

1. **Cloudflare account** at dash.cloudflare.com. R2 needs a payment method on file, even within the free tier.
2. **Bucket.** Go to R2 > Create bucket. Name it, for example, `riftbound-prices`, with automatic location.
3. **Public read access.** In the bucket's Settings, choose one:
   - **Custom domain (recommended).** Under Custom Domains, select Connect a domain, for example `prices.<your domain>`. The domain must be on Cloudflare. Responses are cached at Cloudflare's edge.
   - **Public development URL.** Select Allow to get `https://pub-<id>.r2.dev`. It works, but Cloudflare rate-limits it and says it is not for production.

   The resulting `https://` URL is the **public URL**.
4. **API token.** Go to R2 > Manage API tokens > Create API token.
   - Permission: **Object Read & Write**, scoped to this bucket only.
   - Copy the Access Key ID and the Secret Access Key. Cloudflare shows the secret only once.
   - Note the **Account ID** from the R2 overview page.
5. **GitHub.** In this repo, go to Settings > Secrets and variables > Actions.
   - Secrets: `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`.
   - Variables: `R2_ACCOUNT_ID`, `R2_BUCKET` (for example `riftbound-prices`), `PRICE_LOG_URL` (the public URL, no trailing slash).

## Deploy

1. **Backfill**, on Michael's Mac. The original log is in `~/Library/Application Support/riftbound-price-log/prices.db`.
   1. Copy it somewhere safe first.
   2. Export the five values from step 5.
   3. Run `./backfill.sh /tmp/price-log "$PRICE_LOG_URL"`. It writes every logged day, merged with any days already in the bucket, then uploads them. Without the URL, it is a dry run that only writes `/tmp/price-log`.
2. **Check the bucket.**
   - `curl "$PRICE_LOG_URL/days.json"` lists the days.
   - `curl -sI "$PRICE_LOG_URL/days/2026-10-23.json"` returns 200 with `content-type: application/json`.
3. **Run the job once.** Go to Actions > Price log > Run workflow. The log shows `wrote out/days/<day>.json` or `<day> published, skipping`. After that, it runs on its schedule.
4. **Point the app at it.** Set `PriceLogURL` in the app's `Riftbound-Info.plist` to the public URL, then ship a build.

## Monthly cost

Expected: **$0/month**. If you use a custom domain and don't already have one, add about $10/year for it.

| | Use | Free allowance |
|---|---|---|
| R2 storage | ~4 MB/month added, ~50 MB/year | 10 GB |
| R2 writes (Class A) | ≤ 2 per day, ~60/month | 1 million/month |
| R2 reads (Class B) | 1 index plus new days per app open; fewer with a custom domain's cache. 1,000 users × 10 opens/day ≈ 300,000/month | 10 million/month |
| R2 egress | any | free |
| GitHub Actions | 3 short runs/day | free for public repos |

Beyond the free tier, R2 costs $0.015 per GB-month, $4.50 per million writes and $0.36 per million reads.
