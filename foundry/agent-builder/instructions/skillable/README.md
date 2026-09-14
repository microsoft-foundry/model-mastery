# Skillable track (coming soon)

This track will deliver the same TrailMate workshop on a pre-provisioned
Skillable Windows VM.

Only the **setup** step differs from the [self-guided track](../self-guided/):

- **Self-guided:** you run `scripts/provision.sh` to create the project, deploy
  the Azure-direct models, wire up Application Insights tracing, and optionally
  add Claude.
- **Skillable:** the lab environment pre-provisions the project and **all**
  models — including Claude Sonnet and Haiku — so the GPT-vs-Claude comparison in
  model selection works out of the box. You just run `scripts/setenv.sh <rg>` to
  generate your local `.env` from the pre-provisioned resource group.

Everything after setup — model selection, building TrailMate, observing,
evaluating, and improving it with Model Router and Agent Optimizer — is
identical.

We'll build this track once the self-guided track is validated end to end.
