# ESPN Fantasy Predictor — Roadmap

A draft assistant and weekly performance backtester for a Full PPR ESPN Fantasy Football
league. Goal: train/tune a model while *watching* it draft (pick-by-pick, adjustable speed)
and *watching* it score against real historical weeks — before trusting it on draft day.

## Approach (decided)

- **Phase 1 (notebooks first)**: build and validate the data pipeline, projection model, draft
  simulator, and backtest scorer in Jupyter notebooks. No UI yet — defer that decision until
  the modeling approach is proven out.
- **Draft AI v1**: a projection model (supervised ML) + value-based/ADP-aware simulated draft
  logic. Simpler and faster to get working than RL, and still lets you watch it draft.
- **Extension goal**: a second, reinforcement-learning draft agent that *competes against* the
  v1 model in simulated drafts (rival agents, not a replacement).
- **Extension goal**: connect to your actual ESPN account/league and have the agent make real
  draft-day picks for you.
- **Extension goal**: generalize beyond Full PPR to support Half PPR and other common
  scoring formats.
- **Data access**: no league API access needed yet — historical data will be supplied
  manually or via API access added later, as needed per phase. Decided (2026-07-13):
  primary historical stats source is `nflreadpy` (nflverse) — free, no auth, no
  manual export needed, data back to 1999. `espn_api` is used separately later
  once the user gives league access, specifically to read the *real* league's
  scoring settings/roster rules and draft history — a different job than bulk
  historical stats. ADP (average draft position, needed for Step 4's opponent
  draft logic) isn't in nflverse; recommended source is the Fantasy Football
  Calculator API (free, historical ADP by year/format) when Step 4 needs it.
- **Scope order**: draft simulator and weekly backtest scorer are built **in parallel**, since
  they share the same underlying projection model.

## Stack

- **Language**: Python (pandas, scikit-learn / XGBoost or LightGBM for projections; PyTorch
  or a lightweight RL library like `stable-baselines3` for the extension RL agent)
- **Environment**: Jupyter notebooks for Phase 1; revisit Streamlit/Dash vs. a
  React+FastAPI split (matching the Chess/personal_website stack) once the model works and a
  real UI is needed for playback controls and training visualization.
- **Data**: `espn_api` Python package (or direct ESPN Fantasy API calls) once league access is
  wired up; CSV/manual exports in the meantime.

---

## Step 1: Project Setup
- [x] Set up Python environment (venv or conda) and `requirements.txt`
- [x] Folder structure: `notebooks/`, `data/`, `src/` (shared code imported by notebooks)
- [x] Add `.gitignore` (data files, venv, notebook checkpoints, `__pycache__`)
- [ ] Confirm league scoring settings (Full PPR — confirm roster spots, bench size, any
  scoring tweaks) and starting data source (manual export vs. API). Offense scoring in
  `schema.py`'s `FULL_PPR_SCORING` is now verified against ESPN's own published defaults
  (2026-07-13) and against real 2024 season data.
- [x] Confirmed against the user's actual league (2026-08-16): connected via `espn_api` to
  league id `2091358422` ("Vicious Victories", 2025 season, the user's most recently
  completed league) using cookies stored in a new gitignored `.env` (see `.env.example`,
  `src/espn_league.py`). `FULL_PPR_SCORING` matched exactly — no changes. `KICKER_SCORING`
  and `DST_SCORING` did not: real FG 50+ splits into 50-59/60+ tiers, missed PATs score 0
  (not -1), all defensive TD types score a flat 6 (not the split 3/3/4 guessed from a
  generic ESPN scoring list), points-allowed tiers use different (smaller) magnitudes, and
  the league also scores a separate total-yards-allowed ladder that wasn't modeled before
  at all. `LEAGUE_SETTINGS` bench size was also off (7, not 6) and missing an IR slot. All
  fixed in `schema.py` — see that file's updated comments for exact values and the two
  fields (`1PSF`, `FTD`) whose exact mechanic is still unclear from the API alone. A second
  league id, `1024327784` (this year's, from an invite link), is also stored in `.env` for
  whenever that league's own settings need checking later — not queried yet.

## Step 2: Data Layer
- [x] Define the data schema: players, weekly stats, season totals, draft ADP, league
  roster/scoring rules
- [x] Load historical season(s) data (`src/nflverse_loader.py`, via `nflreadpy` — real
  2024 season loaded and validated, no manual export needed; add more seasons as needed)
- [x] Clean/normalize stats into a consistent player-week table (verified against real
  2024 season data — see `notebooks/01_data_layer.ipynb`)
- [x] Wire up `espn_api` for league settings (2026-08-16, see Step 1 above — `src/espn_league.py`
  is the reusable connector). Draft *history* specifically not pulled yet, only settings.
- [x] Add auth handling for private league access (SWID/espn_s2 cookies) — done as part of
  the Step 1 espn_api wiring above, since the "public" league turned out to require them
  anyway.

## Step 3: Projection Model (v1 Draft AI — supervised)
- [x] Feature engineering (2026-08-16, `src/features.py`): trailing-3/5-game rolling
  averages (causal, carry across season boundaries), season-to-date average (resets each
  season), prior-season total/games/average (covers the early-season cold-start gap),
  position/team as categorical. Deliberately dropped a planned "bye-week flag" — every row
  already represents a played game, so it could never be True. Age/experience, injury
  history, and opponent-matchup-strength are real gaps *not* covered this pass — no data
  source wired up for them yet, noted as fast-follows rather than blocking v1.
- [x] Train a model (2026-08-16, `src/projection_model.py`): weekly (not season-long)
  fantasy points, LightGBM, scoped to QB/RB/WR/TE only (K's fantasy_points is a data gap
  pretending to be a real zero — kicker FG/PAT stats aren't wired into
  `WEEKLY_STATS_SCHEMA` yet; DB/DL/LB/P gadget-play rows are noise, ~54 rows total). Trained
  2019-2022, early-stopped against a 2023 validation set, 2024 held out untouched until
  final evaluation. A trailing-3-game-average baseline (with a prior-season/position-average
  fallback chain) was built first as the bar to beat.
- [x] Evaluate against held-out weeks (2026-08-16): on the untouched 2024 test set, LightGBM
  beat the baseline at every position on both MAE and RMSE (MAE improvement: QB +3.65%, RB
  +1.85%, WR +4.35%, TE +3.31%) — modest but consistent gains for a first-pass model.
- [x] Notebook: visualize projections vs. actuals (2026-08-16, `notebooks/02_projection_model.ipynb`,
  scatter plots per position against the actual=projected line).

## Step 4: Draft Simulator (parallel with Step 5)
- [ ] Model opponent draft behavior (ADP-based or simple value-based picks) for the other
  teams in a mock draft
- [ ] Implement turn-based draft loop: each team (including your "AI") picks in snake-draft
  order based on roster needs + projections
- [ ] Track draft state (who's drafted, by which team, roster slots filled)
- [ ] Notebook: print/log each pick as it happens — this is the seed for the eventual
  pick-by-pick playback UI

## Step 5: Weekly Backtest Scorer (parallel with Step 4)
- [ ] Given a drafted roster, simulate weekly lineup decisions (best legal starting lineup
  per week) using that year's actual results
- [ ] Score each week using Full PPR rules, accumulate season totals
- [ ] Compare against your actual historical team performance (if available) as a sanity
  baseline
- [ ] Notebook: chart projected vs. actual weekly score over a season

## Step 6: UI Decision Point
- [ ] Revisit UI choice now that the model/data pipeline works: Streamlit/Dash (fastest) vs.
  React + FastAPI (matches other projects' stack, more control)
- [ ] Build: draft playback view (pick-by-pick, adjustable speed slider/control)
- [ ] Build: weekly backtest view (week-by-week score chart, running season total)
- [ ] Build: basic training/tuning controls (re-run draft sim, adjust model hyperparameters,
  see results update)

## Step 7 (Extension): Rival RL Draft Agent
- [ ] Define a draft environment (state = draft board + roster needs, action = pick a
  player, reward = team's eventual backtested season score)
- [ ] Train an RL agent (e.g. `stable-baselines3`) via repeated simulated drafts against the
  v1 projection-based agent and/or other RL copies
- [ ] Add a way to watch training progress live (reward curve, draft outcomes per episode)
- [ ] Run v1 (projection-based) vs. v2 (RL) in head-to-head mock drafts, compare backtested
  season scores

## Step 8 (Extension): Live Account Integration
- [ ] Connect to your real ESPN league/account (auth via SWID/espn_s2 cookies)
- [ ] Read live draft-room state during your actual draft
- [ ] Have the chosen agent recommend or auto-submit picks in real time
- [ ] Add safety rails (confirm-before-pick mode vs. full auto-draft mode)

## Step 9 (Extension): Support Multiple Scoring Formats
- [ ] Generalize the scoring logic (currently Full PPR only) into a configurable scoring
  rule set — Half PPR, Standard (no PPR), and other common league variants
- [ ] Parameterize the projection model and backtest scorer to take a scoring format as
  input rather than hardcoding Full PPR math
- [ ] Re-validate projections/backtests across formats (a model trained only on Full PPR
  data may rank players differently under Half PPR or Standard scoring)
- [ ] Add a way to select scoring format in the eventual UI (Step 6)
