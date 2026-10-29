# Consolidation checks

These checks use the local report and mocked readiness dependencies. They do not
access a tenant, Azure or the live product.

```powershell
python scripts/render-progress.py
python -B -m unittest discover -s tests -p 'test_*.py' -v
pwsh -NoProfile -NonInteractive -File tests/doctor-exit-codes.ps1
node tests/progress-report.test.cjs
```

The Node check uses an installed `playwright` package and its Chromium browser. If
the existing .NET harness supplies the driver package instead, pass its directory
with `--playwright-package <installed-package-directory>`. No package installation
or browser download is performed by the check.

The report check writes a sanitized `validation.json` and report-only screenshots
under `results/pr2-feedback-16072ed/`. The log records the base commit, whether the
working tree differed, exact tested source hashes, browser/Node versions and outcomes.
It blocks all HTTP(S) requests. The screenshots contain this report, not authenticated
product screens. Historical tenant evidence and final Fabrikam acceptance remain distinct.
