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
  manually or via API access added later, as needed per phase.
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
- [ ] Set up Python environment (venv or conda) and `requirements.txt`
- [ ] Folder structure: `notebooks/`, `data/`, `src/` (shared code imported by notebooks)
- [ ] Add `.gitignore` (data files, venv, notebook checkpoints, `__pycache__`)
- [ ] Confirm league scoring settings (Full PPR — confirm roster spots, bench size, any
  scoring tweaks) and starting data source (manual export vs. API)

## Step 2: Data Layer
- [ ] Define the data schema: players, weekly stats, season totals, draft ADP, league
  roster/scoring rules
- [ ] Load historical season(s) data (manual CSV/export to start)
- [ ] Clean/normalize stats into a consistent player-week table
- [ ] (Later) Wire up `espn_api` or direct API calls once league access details are available
- [ ] (Later) Add auth handling for private league access (SWID/espn_s2 cookies), if/when
  needed

## Step 3: Projection Model (v1 Draft AI — supervised)
- [ ] Feature engineering: prior-season stats, team context, age/experience, injury history,
  schedule, etc.
- [ ] Train a regression/gradient-boosting model to project weekly or season-long fantasy
  points per player (Full PPR scoring)
- [ ] Evaluate against held-out historical weeks (basic accuracy/error metrics)
- [ ] Notebook: visualize projections vs. actuals for a sanity check

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
