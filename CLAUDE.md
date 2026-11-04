# CLAUDE.md

Cloud Energy (a.k.a. SPECpower model) is an XGBoost model, trained locally, that estimates the
power draw [W] of a whole machine from CPU utilization. The training data is the
[SPECpower_ssj2008](https://www.spec.org/power_ssj2008/) dataset. The model is built for
streaming, inline use (e.g. in Green Metrics Tool / Eco CI).

## Layout

- `xgb.py`: the main entry point. It trains an XGBoost model on startup from `data/spec_data_cleaned.csv`,
  using only the columns the user supplied on the CLI. It then predicts utilization 0–100 in steps of 5,
  linearly interpolates down to 0.01 steps and keeps all of that in a dict. After that it reads
  utilization values line by line from stdin (or psutil with `--autoinput`) and prints watts
  (or joules with `--energy`). `--dump` / `--dump-hashmap` print the whole lookup table.
- `auto_detect.py`: detects machine parameters (`--auto`) from procfs/sysfs/lscpu/dmidecode.
- `ols.py`: older linear (statsmodels OLS) variant, good for exploring parameters. `statsmodels` is **not** in
  the requirements.
- `interact_validation.py`, `hyperparameter_tuning.py` (optuna, from `requirements-dev.txt`) and
  `operating_point_comparison.py`: research/validation scripts, not part of the runtime.
- `demo-reporter/`: C programs (Linux + macOS) that stream CPU utilization, plus prebuilt static binaries.
- `data/spec_data_cleaned.csv`: the training data, a copy of the output of the pipeline in `spec-power-data`.
  This is the only data file needed at runtime and in CI.
- `data/raw`: git submodule with the `spec-power-data` repo (raw data and data pipeline).
- `tests/`: bash scripts that run `xgb.py` and compare its output with hard-coded expected values.
- `Dockerfile.cloud-energy*`: images that ship only `xgb.py`, `auto_detect.py` and
  `data/spec_data_cleaned.csv` (dependencies come from `requirements-docker.txt`).

## Setup & commands

Python >= 3.11 (CI uses 3.13).

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt            # runtime
pip install -r requirements-dev.txt        # optuna for hyperparameter_tuning.py
git submodule update --init                # optional; not needed to run or test the model

# run
./demo-reporter/static-binary-linux-amd64 | python3 xgb.py --tdp 240
python3 xgb.py --autoinput --interval 1 --silent
python3 xgb.py --dump

# tests (what CI runs in .github/workflows/tests.yml); they must be run from inside tests/
cd tests && bash validate-default.sh && bash validate-params.sh

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

The code that builds the training data was moved to the
[spec-power-data](https://github.com/green-coding-solutions/spec-power-data) repo (formerly
`spec-power-raw-data`): the `scripts/` folder plus `spec_data.csv` and `spec_data_cleaned_unmelted.csv`. Its
`README.md` and `CLAUDE.md` describe the pipeline, its known problems and how to update the data. A standalone
clone may exist in `~/spec-power-data`; make changes there, not in `data/raw`, which is a separate checkout at the
pinned commit.

To update the training data:

1. Build it in `spec-power-data` and copy `data/spec_data_cleaned.csv` to `data/spec_data_cleaned.csv` here. This
   copy is what `xgb.py`, `ols.py`, the research scripts, the tests and the Docker images read. CI does not check
   out the submodule, so the file has to stay in this repo.
2. Update the expected values in `tests/validate-*.sh`.
3. Bump the `data/raw` pointer.

The current training data has 619 machines, while the raw data has 924. A rebuild also changes the `Architecture`
values: the current data has `epyc`, `epyc-gen1`, `epyc-gen2` and `epyc-gen3`, but the pipeline now only produces
`epyc`, so `--architecture epyc-gen3` would stop working.

## Conventions

- Don't reformat code you weren't asked to touch (see the root agent guide).
- Use `git -C data/raw ...` for git commands in the submodule. Submodule changes are committed in their own
  repo first, then the pointer in this repo is bumped (commit message style: "Updated Submodule").
- Keep `README.md` in sync when you change CLI flags of `xgb.py`.
