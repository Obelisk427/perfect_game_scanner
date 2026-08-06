# PG Tournament Alert

Polls a Perfect Game tournament event page every 15 minutes and pings a Discord
webhook the first time the **Schedule/Scores** link appears.

- Target event: `151618`
- Test event: `146167` (already completed, used to verify the detector + Discord wiring)

## Setup

1. Create a new GitHub repo and push this folder to it.
2. In the repo, go to **Settings → Secrets and variables → Actions → New repository secret** and add:
   - Name: `DISCORD_WEBHOOK`
   - Value: your Discord webhook URL
3. Go to **Actions** and enable workflows if prompted.

## Test it

In the **Actions** tab, open *PG Tournament Alert* → **Run workflow** → check the
"Run against the completed test tournament" box → **Run workflow**.

You should get a Discord message starting with `[TEST]` within a minute. The job
will commit a `state.json` so it won't re-fire the test alert on the next run.

To re-run the test later, delete the `fired_test` key from `state.json` (or the
whole file).

## Go live

Once the test works, you're done — the cron runs every 15 min automatically.
When the schedule is posted for the target event, you'll get one Discord ping and
`state.json` will be committed with `fired: true` so you won't get duplicates.

## Run locally (optional)

```bash
DISCORD_WEBHOOK="https://discord.com/api/webhooks/..." python3 check.py --test
```

No dependencies — uses only the Python standard library.

## Notes

- GitHub Actions cron is best-effort; slots can run 5–15 min late or occasionally skip.
  For a "bracket posted" alert that's fine.
- If you want to reset and re-arm the live alert, delete `state.json` (or the
  `fired` key) and push.
