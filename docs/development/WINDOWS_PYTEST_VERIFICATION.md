# Windows: verifying pytest without false failures

## Why `findstr` breaks green runs

On Windows, **`findstr` exits with code 1 when no lines match**. Piping pytest into it to “detect” failures is unsafe:

```text
python -m pytest -q --tb=short | findstr /I "FAILED"
```

If the suite is **fully green**, pytest prints no `FAILED` lines, **`findstr` finds nothing**, and the pipeline’s exit code can be **1** even though **pytest succeeded**. That is **not** the same as “pytest failed.”

**Do not use grep/findstr on pytest stdout as the pass/fail signal.** Use **pytest’s own exit code** (0 = success, non-zero = failures/errors).

## Recommended: run pytest directly

**cmd.exe:**

```bat
python -m pytest -q --tb=short
echo Exit code: %ERRORLEVEL%
```

**PowerShell:** after the command, inspect the **last native exit code** (not the pipe):

```powershell
python -m pytest -q --tb=short
$pytestExit = $LASTEXITCODE
if ($pytestExit -ne 0) { exit $pytestExit }
```

In older PowerShell, `$LASTEXITCODE` is set after running a native executable such as `python`.

## CI-equivalent local gate

Prefer the repo script (it already uses **subprocess return codes**, not text grep):

```powershell
python scripts/ci_local_verify.py --json
```

## If you need a filtered log *and* a correct exit code

Run pytest first, capture exit code, then search a log file—**do not** tie overall success to `findstr`:

```powershell
python -m pytest -q --tb=short 2>&1 | Tee-Object -FilePath pytest.log
$pytestExit = $LASTEXITCODE
Select-String -Path pytest.log -Pattern "FAILED"   # human convenience only
exit $pytestExit
```

Or write pytest output to a file with **`subprocess`/shell redirection** while still checking **`$LASTEXITCODE`** from the pytest process (not from a filter).
