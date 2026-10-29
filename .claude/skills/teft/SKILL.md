---
name: teft
description: Place TEFT test calls and check what happened, with the `teft` command line. Use when asked to place a test call, check how the dialler handles a busy line, an answering machine, no answer or DTMF, or to read a TEFT verdict. Test tenants only.
---

# TEFT test calls with `teft`

TEFT plays the customer on a test call. The TEFT runner places the call through a tenant's
telephony platform, and TEFT answers it as the customer you choose: busy, ringing, an answering
machine, DTMF and so on. `teft` drives both and gives every call a verdict (ENG-823).

## Rules

- **Test tenants only.** `teft` refuses any tenant that isn't on its allowlist (exit code 2) and
  sends nothing. Never try to get around that, and never use a production tenant.
- **Every run places a real call** on that tenant's telephony platform. Don't place calls nobody
  asked for, and don't loop.
- **The API key is read at run time and kept in memory.** Never write it into a file, a result
  page, a Jira comment or the chat.
- **Report the execution ID** with every verdict, so a person can read the result again with
  `teft result <id>`.

## One-time set-up

1. The .NET 9 SDK (includes the runtime); the SDK is needed for the `dotnet` install commands below.
2. The Noetica NuGet feed, if `dotnet nuget list source` doesn't already show
   `https://nuget.pkg.github.com/Noetica/index.json`. It needs a GitHub personal access token
   (classic) with `read:packages`. Read the token from a hidden prompt, so it stays out of shell
   history, and never store it in plain text.

   On Windows, NuGet stores the password encrypted for your user account:

   ```powershell
   $token = [Net.NetworkCredential]::new('', (Read-Host 'GitHub token' -AsSecureString)).Password
   dotnet nuget add source "https://nuget.pkg.github.com/Noetica/index.json" --name NoeticaGPR `
     --username <GitHub user> --password $token
   Remove-Variable token
   ```

   On macOS and Linux, NuGet can't encrypt it. Add the source without a password, and give the token
   only to the install or update command:

   ```bash
   dotnet nuget add source "https://nuget.pkg.github.com/Noetica/index.json" --name NoeticaGPR
   read -rs GH_PACKAGES_TOKEN
   NuGetPackageSourceCredentials_NoeticaGPR="Username=<GitHub user>;Password=$GH_PACKAGES_TOKEN" \
     dotnet tool install --global NubAutoTeftRunner.Cli
   unset GH_PACKAGES_TOKEN
   ```

3. `dotnet tool install --global NubAutoTeftRunner.Cli`. Later: `dotnet tool update --global NubAutoTeftRunner.Cli`
   (on macOS and Linux, with the credential variable as above).
4. Create the config file in the platform's application-data folder: `%APPDATA%\teft\config.json`
   on Windows, `~/.config/teft/config.json` on Linux (`$XDG_CONFIG_HOME/teft/config.json` when set),
   or `~/Library/Application Support/teft/config.json` on macOS. No key goes in it:

   ```json
   { "runnerUrl": "https://telephony-testing.dev.noeticacloud.com/runner", "allowedTenants": ["fabrikam"] }
   ```

   Add another test tenant only when a person asks for it. `TEFT_CONFIG` can name a different file,
   and `TEFT_RUNNER_URL` overrides the runner URL.

## Each session

Read the key into the environment, then check the runner can see the tenant:

```powershell
$env:TEFT_API_KEY = az keyvault secret show --vault-name kv-noetica-dev-29641d05 --name teft-api-key --query value -o tsv
teft status --tenant fabrikam --json
```

`dspEnabled: true` means TEFT is connected to its DSP. If `status` fails, stop and report it:
nothing else will work.

## Placing a call

1. **Find the outcome.** Read the catalogue live; don't rely on a remembered list:

   ```powershell
   teft outcomes --tenant fabrikam --json
   ```

   Each outcome has a `performance` name to run, and at most one `parameter`, with its default.
2. **Run it and wait for the verdict:**

   ```powershell
   teft run fabrikam RingThenAnswer --param ringSeconds=5 --wait --json
   ```

   - `--param name=value` sets the outcome's parameter. Repeat it for more.
   - `--expect name=value` asks the runner to check something. Each check gets its own verdict:
     `dtmf=0123`, `acts=Answer,Hangup`, `log=<text>`, `min-ms=<ms>`, `max-ms=<ms>`,
     `webhook=<EventType>`, `session-acts=<acts>`, `session-log=<text>`.
   - With any `--expect`, the runner allows the call 60 seconds. Add `--expect timeout-ms=<ms>` for
     a longer performance, for example NoAnswer at its default 60 seconds of ringing.
   - `--timeout <seconds>` is how long `teft` waits for the verdict. It only applies with `--wait`.
3. **Read it again later:** `teft result <executionId> --json`.
4. **Without waiting:** `teft queue fabrikam Busy` prints the execution ID and returns at once.

For a dialler list rather than one call, `teft number <outcome> --param <n> --seq <n>` gives the
number a test record should dial to get that outcome. It needs the number plan switched on for that
TEFT host; when it's off, `teft number` says so.

## Reading the result

| Verdict | Meaning | What to do |
|---|---|---|
| **Pass** | The call completed and every requested check passed | Report it, saying which checks ran |
| **Fail** | The product did something wrong: a check failed, or a call leg never completed | Report it as a failure, with the failing checks |
| **Blocked** | The test couldn't run: TEFT or the runner was down, or the tenant isn't set up | Report it as blocked, not as a product failure |
| **NotRun** | A requested check never started | Report which check, and why if the result says |

**A Pass with no checks only proves the call completed.** It says nothing about how the product
handled the call. To claim a behaviour (for example "the dialler recorded the call as busy"), run the
call with `--expect` checks for it, and report the result as completed-only when `checks` is empty.

Exit codes: 0 Pass, 1 error (bad input, or the runner refused), 2 tenant refused, 3 verdict not Pass.

Each check in `checks` has a `name`, a `leg` (Dial is the customer leg, Session is the agent leg),
its own `verdict`, and `expected` and `actual`. Quote those when you report a failure.

## What the checks can and can't show

- `dtmf` confirms the digits TEFT **sent**. It can't show what the dialler received.
- `acts` matches by act name: Answer, Ring, Reject, Hold, UnHold, Wait, PlayAudio, SendDtmf, Hangup.
- A Blocked verdict says nothing about the product. Fix the set-up and run it again.

## In a verification run

When the `scenario` skill's card asks for TEFT calls, place them with this skill, and put each
call's outcome, verdict, execution ID and failing checks in the result page.
