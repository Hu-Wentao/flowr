# Generic BFF Packaging

Package generated BFF delivery artifacts only after their component contracts
have passed validation.

## Workflow

1. Resolve this task with `resolve.py --task package_bff` and read the resolved
   instructions for a new `instructions_id`.
2. Generate or refresh every required `*.bff.md` and validate that none are
   missing or stale.
3. Run the resolved `package` command. The generic command recursively
   collects project `*.bff.md` files, preserves project-relative paths, and
   atomically writes `build/bff-contracts.zip`. Local and HTTP(S) OpenAPI
   documents remain independently owned references and are not copied into the
   archive.
4. Inspect the reported file list and archive path.
5. If the project profile declares a `sync` command, explain its destination
   and side effects and obtain explicit authorization before executing it.
   Packaging alone never authorizes copying, committing, or pushing to another
   repository. A user request to sync, publish, or update the configured shared
   repository is itself authorization for the required push to its configured
   ref; do not ask for a second push confirmation. Once authorization is
   explicit, run the resolved `sync` command unconditionally after packaging.
   Do not skip it because generated BFF files were already current or the source
   repository has no BFF diff. Those checks prove source freshness, not destination parity.
   Let the sync command compare the destination and decide whether a commit or
   no-op is appropriate. Stop for a scope conflict if the push would also
   publish unrelated commits.
6. Classify the result only as `packaged` or `published`: `packaged` exists only
   in the source repository; `published` means the exact remote ref was read
   back and contains the exact destination commit. A local checkout or commit
   is an implementation detail, not a delivery outcome. Record the remote, ref,
   and commit as publication evidence.
7. A request to sync, publish, deliver, or update a shared authority repository
   is complete only in `published` state. Never describe a local commit as an
   updated repository. Without publication authorization, report the current
   non-published result and request authorization. With authorization, push and
   verify; a sync command that omits remote evidence has not completed the task.

Project profiles may define user phrases that constitute publication
authorization. Apply those phrases as written and do not ask twice, while
keeping unrelated repositories and branches outside that authorization.

The generic collector excludes `.git`, `.dart_tool`, `.agents/.cache`, and
`build`. Add project-relative exclusions with repeated `--exclude` arguments.
It fails when no BFF contracts exist and never replaces an existing archive
until the new ZIP is complete. Contract validation, rather than packaging,
resolves and verifies local or network OpenAPI references.

## Project Configuration

Projects may override packaging and declare synchronization without changing
the reusable skill:

```yaml
schema: fr-mvvm-contract.config.v1
profile: example-project
tasks:
  package_bff:
    base: references/package_bff.md
    profile: package_bff.md
    commands:
      package: uv run --script .agents/skills/fr-mvvm-contract/scripts/package_bff.py --project-root . --output build/bff-contracts.zip
      sync: ./tool/sync_bff_contracts.sh build/bff-contracts.zip
```

Keep repository destinations, credentials, branch policy, commit rules, and
sync commands in `.agents/skills-config/fr-mvvm-contract/`. The resolver emits
commands but never executes them.
