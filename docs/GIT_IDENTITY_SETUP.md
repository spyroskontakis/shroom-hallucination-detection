# Future public Git identity — instructions only

Before any commit, obtain explicit confirmation of both the public Git author name and the exact noreply email copied from the owner's GitHub email settings. Do not derive an address from a username or account ID. The copyright holder approval does not select the commit identity.

Only after separate approval to initialize a new repository, configure repository-local identity there (never global settings or the private archive):

```text
git config --local user.name "<APPROVED PUBLIC NAME>"
git config --local user.email "<EXACT APPROVED GITHUB NOREPLY EMAIL>"
git config --local user.useConfigOnly true
```

These placeholders are instructions, not executable values. After configuration, inspect the local name/email and effective author/committer identities, including any environment overrides, before creating a commit. Confirm both identities use the approved values. Do not copy the private repository's configuration, old commits, tags or identities.

No commands in this guide were executed during PHASE 4D. Repository initialization, commits, push and publication require new approval.
