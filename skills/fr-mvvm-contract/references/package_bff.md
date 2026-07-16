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
   atomically writes `build/bff-contracts.zip`.
4. Inspect the reported file list and archive path.
5. If the project profile declares a `sync` command, explain its destination
   and side effects and obtain explicit authorization before executing it.
   Packaging alone never authorizes copying, committing, or pushing to another
   repository.

The generic collector excludes `.git`, `.dart_tool`, `.agents/.cache`, and
`build`. Add project-relative exclusions with repeated `--exclude` arguments.
It fails when no BFF contracts exist and never replaces an existing archive
until the new ZIP is complete.

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
      package: uv run python .agents/skills/fr-mvvm-contract/scripts/package_bff.py --project-root . --output build/bff-contracts.zip
      sync: ./tool/sync_bff_contracts.sh build/bff-contracts.zip
```

Keep repository destinations, credentials, branch policy, commit rules, and
sync commands in `.agents/skills-config/fr-mvvm-contract/`. The resolver emits
commands but never executes them.
