# CLAUDE.md

Cloud Energy (a.k.a. SPECpower model) is an XGBoost model, trained locally, that estimates the
power draw [W] of a whole machine from CPU utilization. The training data is the
[SPECpower_ssj2008](https://www.spec.org/power_ssj2008/) dataset. The model is built for
streaming, inline use (e.g. in Green Metrics Tool / Eco CI).

## Layout

- `xgb.py`: the main entry point. It trains an XGBoost model on startup from the training data, using only the columns the user supplied on the CLI. It then predicts utilization 0–100 in steps of 10,
  linearly interpolates down to 0.01 steps and keeps all of that in a dict. After that it reads
  utilization values line by line from stdin (or psutil with `--autoinput`) and prints watts
  (or joules with `--energy`). `--dump` / `--dump-hashmap` print the whole lookup table.
- `auto_detect.py`: detects machine parameters (`--auto`) from procfs/sysfs/lscpu/dmidecode.
- `ols.py`: older linear (statsmodels OLS) variant, good for exploring parameters. `statsmodels` is **not** in
  the requirements.
- `interact_validation.py`, `hyperparameter_tuning.py` (optuna, from `requirements-dev.txt`) and
  `operating_point_comparison.py`: research/validation scripts, not part of the runtime.
- `demo-reporter/`: C programs (Linux + macOS) that stream CPU utilization, plus prebuilt static binaries.
- `spec-power-data/`: git submodule with the `spec-power-data` repo (raw data, data pipeline and training data).
- `spec-power-data/data/spec_data_cleaned.csv`: the training data. This is the only data file needed at runtime and
  in CI.
- `tests/`: bash scripts that run `xgb.py` and compare its output with hard-coded expected values.
- `Dockerfile.cloud-energy*`: images that ship only `xgb.py`, `auto_detect.py` and
  the training data (dependencies come from `requirements-docker.txt`).

## Setup & commands

Python >= 3.11 (CI uses 3.13).

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt            # runtime
pip install -r requirements-dev.txt        # optuna for hyperparameter_tuning.py
git submodule update --init                # required; holds the training data

# run
./demo-reporter/static-binary-linux-amd64 | python3 xgb.py --tdp 240
python3 xgb.py --autoinput --interval 1 --silent
python3 xgb.py --dump

# tests (what CI runs in .github/workflows/tests.yml); they must be run from inside tests/
cd tests && bash validate-default.sh && bash validate-params.sh && bash validate-turbo.sh

# lint
pylint xgb.py auto_detect.py        # config in .pylintrc (max line length 120)
```

The tests compare exact float output. Any change to training data, XGBoost version, model params or
interpolation **will** change the expected values in `tests/validate-*.sh`. Update those values on purpose
and say so in the commit. Never update them just to make CI green.

## Dependencies

- Versions in `requirements*.txt` are pinned exactly and updated daily by Dependabot.
- `requirements.txt` uses PEP 508 markers: `xgboost-cpu` on Linux/Windows x86_64 and `xgboost` everywhere
  else. The two markers must stay exact complements of each other, and **both packages must have the same
  version**. They got out of sync before (commit `ceb88f5`), so bump them together.
- `requirements-docker.txt` is a separate, smaller pin list for the Docker image. Keep its versions in line.

## Training data

The training data and the code that builds it live in the
[spec-power-data](https://github.com/green-coding-solutions/spec-power-data) repo (formerly
`spec-power-raw-data`), which is included as the submodule `spec-power-data/`. There is no copy of the data in this
repo. Its `README.md` and `CLAUDE.md` describe the pipeline, its known problems and how to update the data. A
standalone clone may exist in `~/spec-power-data`; make changes there, not in the submodule, which is a separate
checkout at the pinned commit.

To update the training data:

1. Build it in `spec-power-data`, commit and push it there.
2. Bump the `spec-power-data` pointer here.
3. Update the expected values in `tests/validate-*.sh`.

The current training data has 489 machines (`CPUMake`: 300 `intel`, 182 `amd`, 6 `ampere`, 1 `nvidia`). The raw data
has 924 results, but the pipeline drops all hardware older than 2018. The previous data (619 machines, built in 2022)
is kept in `spec-power-data/data/legacy/`.

`xgb.py`, `ols.py`, the research scripts, the tests, CI (`submodules: true`) and the Docker image all read
`spec-power-data/data/spec_data_cleaned.csv`.

## Conventions

- Don't reformat code you weren't asked to touch (see the root agent guide).
- Use `git -C spec-power-data ...` for git commands in the submodule. Submodule changes are committed in their own
  repo first, then the pointer in this repo is bumped (commit message style: "Updated Submodule").
- Keep `README.md` in sync when you change CLI flags of `xgb.py`.
