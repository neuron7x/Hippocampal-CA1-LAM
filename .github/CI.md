# CI

`CI gate` succeeds when the Python matrix, static policy checks, and Git history scan all report success for the run's commit. Missing, skipped, cancelled, and failed results fail the gate. Every PR into `main` and every push to `main` receives a run without path filters. Matrix entries install independently resolved, hash-locked CI environments on Linux x86-64.

- The Python 3.11–3.13 matrix runs `make test`, builds a wheel and source distribution, installs the wheel, executes `ca1-test` outside the checkout, deserializes the repository's example YAML configuration, and captures installed oracle reports for all three phase contexts.
- Static checks cover Python packages and CI tooling, workflow policy, tracked JSON/YAML, tracked Unicode, and Markdown file links and anchors. The dependency audit checks all three locks and writes CycloneDX reports. Gitleaks scans the checked-out Git history and redacts findings.
- `Validate PR metadata` reruns on description edits. It accepts the repository's PR template and requires verification evidence in its own section.
- CodeQL advanced setup and external Markdown URLs have their own statuses. External URL checks run on `main`, on schedule, and on demand. HTTP errors and timeouts fail the external job. CodeQL requires enabled code scanning and available Actions runners in the canonical repository.

## Local verification

```bash
uv venv --python 3.12 .venv
uv pip sync --python .venv/bin/python --require-hashes --only-binary :all: ci/requirements-3.12.txt
source .venv/bin/activate
PYTHONHASHSEED=0 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 make check
python scripts/ci_policy_check.py
python scripts/validate_configs.py .
python scripts/unicode_scan.py
actionlint
zizmor --offline .github
bash scripts/check_docs_links.sh local
```

Run `bash scripts/lock_ci.sh` with uv 0.10.12 after changing direct dependencies. Use `--upgrade` for a deliberate refresh. Recheck the three locks and their advisory reports. Python 3.11 is the supported floor. The Python 3.10 lock resolved Pillow 12.3.0 with 42 advisory matches, and Pillow 13 requires Python 3.11+. The lock retains the fixed `filelock` floor.

The generated artifacts include the run SHA in their names. Distribution checksums identify the exact wheel and source archive exercised by the run. These engineering checks cover software behavior. Biological validation remains tracked in the [Evolution Plan](../docs/EVOLUTION_PLAN.md).
