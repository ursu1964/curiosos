# curios_ollama

`curios_ollama` is the TASK-BOOT-020 Ollama provider boundary package.

The package depends inward on `curios_contracts` and `curios_core`. It exposes a
`ProviderCatalog` implementation that translates Ollama-local inventory checks
into frozen Curios `ProviderDescriptor` and `Result` contracts.

It does not define canonical contracts, route models, invoke models, download
models, run agents, implement orchestration, authorize work, persist state,
export telemetry, or require a live Ollama server during ordinary tests.
