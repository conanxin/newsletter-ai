## Summary

- What does this PR change?
- Why is this change needed?

## Changes

- [ ] Core logic
- [ ] Config / data schema
- [ ] Docs
- [ ] Tests / validation

## Validation

Please paste key command outputs used to verify:

```bash
python3 scripts/run_daily_pipeline.py
python3 scripts/check_pipeline_status.py
python3 scripts/validate_release.py --with-feedback-smoke
```

## Checklist

- [ ] No sensitive local data added (e.g. `preferences.json`, runtime `output/` artifacts)
- [ ] `.gitignore` still excludes runtime/state files
- [ ] README / docs updated if behavior changed
- [ ] Backward compatibility considered
