# Contributing

Thanks for contributing to Newsletter AI.

## Development Setup

```bash
git clone https://github.com/conanxin/newsletter-ai.git
cd newsletter-ai
cp data/state/preferences.example.json data/state/preferences.json
```

Run core checks:

```bash
python3 scripts/run_daily_pipeline.py
python3 scripts/check_pipeline_status.py
python3 scripts/validate_release.py --with-feedback-smoke
```

## Coding Guidelines

- Keep changes small and focused.
- Preserve existing CLI behavior unless explicitly changing it.
- Prefer config-driven logic over hard-coded rules when possible.
- Add/update docs when behavior changes.

## Pull Request Process

1. Create a feature branch.
2. Ensure validation commands pass.
3. Fill the PR template with evidence (command outputs, report paths).
4. Avoid committing runtime artifacts and personal local state.

## What not to commit

- `data/normalized/*`
- `output/*`
- `data/state/preferences.json`
- Any secrets / tokens
