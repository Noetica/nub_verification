# Dependabot ride

Read from `implement` step 6a, `create-pr` step 5 and after `create-pr` step 16. Routine dependency
updates do not ship alone: every push to `main` is a release, so the repository's ride candidates
(open patch, minor and GitHub Actions Dependabot PRs, classified below) ride the next feature PR as
separate commits and are reviewed and released with it, while framework-major PRs stay open
(ENG-18). This resource does not merge PRs and is never invoked on its own.

## Classify the open Dependabot PRs

```
gh pr list --author app/dependabot --state open --limit 1000 --json number,title,headRefName,headRefOid,url
```

- **Ride candidate**: a grouped PR other than a majors group; any PR whose head branch starts with
  `dependabot/github_actions/`; or an individual `npm` or `nuget` PR (head branch
  `dependabot/npm_and_yarn/…` or `dependabot/nuget/…`) whose title's "from X to Y" keeps the major
  version (a patch or minor update, often a security update in a repository without the hub's
  groups). The hub-owned major and hub pins below never are. A grouped PR names its group in the
  title, in either form and any letter case or commit-message prefix: "bump the `<group>` group …"
  (several updates) or "bump `<dependency>` from X to Y in the `<group>` group …" (one). A group
  that spans several directories is titled "bump `<dependency>` and N others" without its name, so a
  PR is also grouped when its head branch ends with the group's name and a hash
  (`dependabot/nuget/dot-config/nuget-patch-minor-a21efbfcb3`). The hub seeds' groups are
  `npm-patch-minor`, `npm-security`, `nuget-patch-minor`, `nuget-security`, `github-actions` and
  `github-actions-security`; a repository's own configuration may name others. The hub seeds ignore
  npm and NuGet major version updates, so there a framework major appears only as an individual
  security PR whose fix needs one.
- **Framework major**: a majors group PR, or an individual `npm` or `nuget` PR (same branch
  prefixes) whose title's "from X to Y" changes the major version. A grouped `npm` or `nuget` PR is
  a majors group when its group in the repository's `.github/dependabot.yml` allows major updates:
  `update-types` includes `major`, or is omitted, which means every update type. A group the file
  does not define is a majors group when any update its PR lists changes the major version. Names
  never decide it. It stays open as the record of pending upgrades; a person raises the card.
- **Hub-owned major**: the `codeql-action-major` group. The workflows it edits are overwritten by
  the standards sync, so a bump here would be reverted; the PR stays open as the signal for the hub
  to update its templates, and is listed with the framework majors.
- **Hub pins**: in `nub_model_repository`, every `github_actions` PR.
  `scripts/update-pinned-actions.rb` owns the hub's action pins and rewrites a newer major back to
  the one its allowlist freezes, so a ridden bump would be reverted. The PR stays open for whoever
  updates that allowlist, and is listed with the framework majors.
- Anything else (another ecosystem, or a title with no version change to judge) is neither: leave
  it.

A result of exactly 1000 may be incomplete: say so. No Dependabot PRs, or `gh` unavailable: say so
in one line and carry on. This step never blocks the feature work.

No skill closes a Dependabot PR. A ridden PR stays open, with a comment once the feature PR exists
(last section), and Dependabot closes it itself once `main` carries those versions. So an abandoned
branch or draft never strands an unshipped bump behind a closed PR, and the quarterly backstop still
sees an open security PR until the fix is on `main`.

## Bring a candidate in

Work on the feature branch before any feature change, one candidate at a time, security groups
before version groups (so a conflict between the two defers the routine bump). First check that
`git status --porcelain` prints nothing (ignored files, such as the plan file, are not listed). If
it prints anything, bring nothing in: record every candidate as not brought in because the working
tree is not clean, and never reset it. Each candidate needs its own commit, so a local-only run
without commit authority (`implement` step 7a) brings nothing in and records the candidates as not
brought in. A candidate with a `Dependabot #<number>` commit already on the branch (a resumed run)
is included: that commit is made only after its build and tests pass.

Then `git fetch origin main` and confirm `git merge-base --is-ancestor origin/main HEAD`. A branch
behind `origin/main` would carry `main`'s newer commits into a ride commit through a rebased
Dependabot branch, so bring nothing in: record every candidate as not brought in because the branch
is behind `origin/main`.

1. `git fetch origin <headRefName>` then `git merge --squash origin/<headRefName>`. This is a
   three-way merge, so a stale Dependabot branch cannot undo later changes on `main`. When the only
   conflicts are in lockfiles on the list in step 3 (a group brought in just before touched the same
   lockfile), keep the merged manifests, regenerate those lockfiles with the repository's install or
   restore, stage them and continue; any other conflict defers the candidate. Nothing staged means
   this branch already contains it. It is already on `main` (Dependabot has not closed it yet) when
   `git diff --quiet origin/main HEAD --` the files the PR changes
   (`gh pr diff <number> --name-only`) shows no difference: record that and move on. Otherwise an
   earlier commit carried it unlabelled: record it as not brought in on this branch.
2. Outside `nub_model_repository`, drop the files the standards sync owns, whose pins the hub keeps
   current and the next sync would overwrite: `git restore --staged --worktree --` each of
   `.github/workflows/sync-model-repo.yml`, `.github/workflows/codeql-pr.yml`,
   `.github/workflows/codeql-full.yml`, `.github/workflows/jira-postmerge-docsonly.yml`,
   `.github/workflows/repomap.yml` and `.github/actions/notify-failure/action.yml` that is staged.
   (In the hub, `github_actions` PRs never ride, so there is nothing to drop.) Nothing left staged:
   the candidate brings nothing this repository owns; record it as deferred with that reason.
3. Check the staged files (`git diff --cached --name-only`): exactly what this commit will change on
   top of the branch, which starts from `origin/main`. Allowed, by file name at any depth:
   `package.json`, `package-lock.json`, `npm-shrinkwrap.json`, `yarn.lock`, `pnpm-lock.yaml`,
   `*.csproj`, `*.fsproj`, `*.vbproj`, `Directory.Packages.props`, `packages.config`,
   `packages.lock.json`, `global.json`, `dotnet-tools.json`; and for a `github-actions` PR, workflow
   and action files under `.github/`. Anything else is outside the bump (in September 2026,
   Dependabot PRs whose diff against `main` deleted live WCF endpoints were green and mergeable),
   which is what this check catches. A NuGet group that rewrites `web.config` or `app.config`
   binding redirects is therefore deferred.
4. Build the repository and run its tests on the staged change, as its `AGENTS.md` or context pack
   describes. If the build rewrote a tracked file (`npm install` normalising a lockfile, a NuGet
   restore regenerating `packages.lock.json`), stage it when its name is on the list above; any
   other change defers the candidate. `git status --porcelain` must then show only staged files.
5. Only then commit it alone, with subject `Dependabot #<number>: <PR title> (<KEY>)` and the body
   line `Dependabot-Head: <sha>`, where `<sha>` is `git rev-parse origin/<headRefName>` from the
   fetch in step 1: the revision actually merged. `create-pr` finds included bumps by that subject
   prefix and names the revision from that line, so keep both exact.

A candidate that conflicts, stages a file outside the list, or fails or cannot run the build or
tests here (for example a .NET Framework build on a machine without MSBuild) is **deferred**:
`git reset --hard HEAD`, then `git clean -fd` for untracked files (the tree was checked clean before
the first candidate, so both touch only this candidate's changes), confirm `git status --porcelain`
prints nothing, and remove the ignored build output its build wrote (`bin/`, `obj/`, `node_modules/`
or the repository's own clean step) so the next build starts from the reset sources. Then record the
reason. A deferred PR is left open and untouched.

Record each outcome where the run keeps its state: the plan file's first section, or the chat steps
in minor work.

## Record it in the PR

`create-pr` writes up to three lines in `Summary`, each only when it applies:

- `Dependency updates included: #12, #15`: one entry per commit whose subject starts `Dependabot #`
  and that the branch has not since reverted.
- `Dependency updates deferred: #14 (fails the local build: <error>)`: one entry per ride candidate
  still open, not included and not recorded as already on `main`, with the reason the plan or
  session recorded.
- `Deferred majors: #21 (breaking-updates majors group, 5 updates), #9 (Newtonsoft.Json 12 to 13)`:
  every open framework-major, hub-owned major and hub pins PR.

A ride candidate that is open, not included and has no recorded outcome was not brought in on this
branch. Say so to the developer before the PR opens. It is advisory, not a gate, and it is listed as
deferred with the reason "not brought in on this branch".

## Comment once the feature PR exists

After `create-pr` has opened the draft PR, comment on each included Dependabot PR that is still
open. A comment is visible to the whole team, so this happens only under `create-pr`'s delivery
authority. Name the revision brought in, because Dependabot may have refreshed the PR since. Skip a
Dependabot PR whose comments already name this feature PR and revision, so a rerun of `create-pr`
step 16 adds nothing:

```
gh pr comment <number> --body "Revision <Dependabot-Head, first 7> brought into <feature PR URL> (branch <branch>, <KEY>) as a separate commit. Left open: Dependabot closes this once main carries these versions."
```
