# Branch Strategy and Merge Flow

## Branch model

`main` is the production/testing integration branch and the branch that publishes GitHub Pages.

Create all work in purpose-focused branches and merge into `main` via Pull Request:

- `feature/materials-supplies/<short-description>`
- `feature/gameplay/<short-description>`
- `feature/talent-system/<short-description>`
- `feature/item-stats/<short-description>`
- `feature/balancing/<short-description>`

### Allowed supporting branches

For non-feature work, use:

- `fix/<issue>`
- `chore/<task>`
- `docs/<topic>`
- `test/<check>`

## Workflow

1. Start from `main` and create a purpose branch.
2. Push changes to that branch.
3. Open a Pull Request targeting `main`.
4. Merge only after checks pass.
5. Delete the branch after merge.

## Do not

- Do not commit directly to `main`.
- Do not create branches outside the naming scheme above.

