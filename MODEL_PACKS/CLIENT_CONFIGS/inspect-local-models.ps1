$ErrorActionPreference = "Stop"
$models = @(
  "ggdv-human-sol:1.0",
  "x-time-ggdv-human:1.0",
  "ggdv-human-sol-coder:1.0"
)
Write-Host "Ollama:" (ollama --version)
foreach ($m in $models) {
  Write-Host ""
  Write-Host "== $m =="
  ollama show $m
}
Write-Host ""
Write-Host "OpenAI-compatible endpoint: http://127.0.0.1:11434/v1"