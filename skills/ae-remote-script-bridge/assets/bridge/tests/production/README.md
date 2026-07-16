# Production Acceptance Suite

Run this only against a disposable After Effects project. The fixture files are
copied before use; their originals are never modified.

```bat
python client\run_production_tests.py ^
  --fixture-a "D:\path\source_a.png" ^
  --fixture-b "D:\path\source_b.png" ^
  --render
```

The suite covers composition create/update, text, Transform, keyframes, Solid,
Fill, Tint, footage import, explicit footage relink, structured inspection,
negative targets/properties/paths, frame capture, animation contact sheet, an
optional short isolated render, and cleanup.

Relinking is always explicit. The suite does not search for replacement files,
choose candidates, or automatically relink missing footage. A caller must pass
the replacement path deliberately.

Generated requests, fixture copies, output, and reports are written under
`temp/production_tests/<run-id>/` and are not source files.

Frame previews and animation contact sheets are copied into the suite run's
`artifacts/` directory immediately. This prevents the bridge's rolling
10-command log retention from deleting visual evidence before the suite ends.
