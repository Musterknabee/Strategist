# Populate Research OS artifacts inside strategist-local-api so GET /ui/research-os/status
# reads the same paths as STRATEGY_VALIDATOR_ARTIFACT_ROOT (/var/lib/strategy-validator/artifacts).
# Prerequisites: image rebuilt; container running with deployment.env (see run_local_docker_api.ps1).
$ErrorActionPreference = "Stop"
$container = "strategist-local-api"
$art = "/var/lib/strategy-validator/artifacts"
$runId = if ($args[0]) { $args[0] } else { "runtime-gauntlet-demo" }
docker exec $container strategy-validator-research-os-runtime-demo `
  --artifact-root $art `
  --run-id $runId `
  --allow-synthetic-demo `
  --overwrite `
  --skip-benchmark `
  --json
