# Security

Report vulnerabilities privately to **vault@echostate.cloud**. Please don't open public issues for them.

Defaults: no network access; tracked roots and exclusions are explicit; `.env`, keys and credential-like names are
excluded; symlinks are not followed; restore only writes into an empty folder outside the workspace and checks every
written byte; historical contents are shown as data and never executed.

Local history keeps old file contents. If a secret was captured, rotate it, then delete the affected `.echo/objects`
blobs and versions (a purge command is on the roadmap). A hash chain on your own machine shows accidental damage; it
cannot stop someone with access to the machine from rewriting both files and hashes.
