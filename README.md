# LeetCode Leaderboard

A free dashboard, hosted on GitHub Pages, that shows how many LeetCode problems
you and your friends have solved. A scheduled GitHub Action fetches everyone's
stats a few times a day, so the page stays up to date on its own.

## How it works

LeetCode's data lives behind a GraphQL endpoint that a browser page **can't**
call directly (it blocks cross-origin requests). So instead of the page fetching
LeetCode, a GitHub Action does it on a schedule, saves the result to
`docs/data.json`, and the static page just reads that file. No server, no API
keys, nothing to pay for.

```
GitHub Action (every 6h)  ──►  leetcode.com/graphql  ──►  docs/data.json
                                                              │
                                          GitHub Pages serves docs/  ──►  your friends
```

## Setup (about 5 minutes)

1. **Create a new repository** on GitHub (public is required for free Pages) and
   push these files to it, keeping the same folder structure.

2. **Add your usernames.** Edit `usernames.json`:

   ```json
   {
     "users": [
       { "leetcode": "your-leetcode-username", "name": "You" },
       { "leetcode": "friends-username", "name": "Alex" }
     ]
   }
   ```

   `leetcode` must be the exact username from the profile URL
   (`leetcode.com/u/THIS-PART/`). `name` is just the label shown on the board.

3. **Turn on GitHub Pages.** In the repo: **Settings → Pages → Build and
   deployment → Source: Deploy from a branch**, then pick branch `main` and
   folder **`/docs`**. Save. Your site will be at
   `https://YOUR-USERNAME.github.io/YOUR-REPO/`.

4. **Run the fetch once.** Go to the **Actions** tab, pick **Update LeetCode
   stats**, and click **Run workflow**. (The first time, you may need to click
   the green button to enable Actions on the repo.) It'll pull everyone's stats
   and commit `docs/data.json`.

That's it. After that it refreshes automatically every 6 hours, and re-runs
whenever you edit `usernames.json`.

## Running it locally (optional)

To preview before pushing, or to regenerate data by hand:

```bash
python scripts/fetch_stats.py          # writes docs/data.json
cd docs && python -m http.server 8000  # open http://localhost:8000
```

Only the Python standard library is used — no `pip install` needed.

## Good to know

- **The shipped `docs/data.json` is sample data** so the page looks alive before
  your first run. Your real data overwrites it.
- **Scheduled Actions only run on the default branch**, can be delayed by a few
  minutes on the free tier, and GitHub pauses them after ~60 days with no repo
  activity. If it goes quiet, open the Actions tab and run it once to wake it up.
- **Occasionally LeetCode may rate-limit** the Action's shared IP; if a run
  fails, just re-run it. A one-second pause between users is already built in.
- Everything shown comes from **public** LeetCode profiles. If a friend's
  profile is private, their counts won't be available.

## Customizing

- **Refresh rate:** change the `cron` line in `.github/workflows/update.yml`
  (`"0 */6 * * *"` = every 6 hours).
- **Look and title:** all styling and the "The Grind" heading live in
  `docs/index.html`. Colors are CSS variables at the top of the `<style>` block.
- **Sort default:** the board sorts by total solved; the Hard/Medium/Easy
  buttons re-sort live.
