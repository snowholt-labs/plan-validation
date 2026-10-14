# Reproducible report demonstration

This authored fixture demonstrates the report format and a concrete requirement mismatch. It is not an autonomous validation run, independent review, user testimonial or comparative benchmark.

The specification requires exponential retry delays capped at 30 seconds. The original plan describes exponential growth but omits the cap. `uncapped.py` follows that incomplete instruction; `corrected.py` is a reference correction. The same three acceptance tests run against both.

From the repository root:

```bash
python3 scripts/demo.py --output /tmp/plan-validation-demo
```

Use an output path that does not already exist. Open its `report.html`. Expected evidence:

| Check | Expected result |
| --- | --- |
| Uncapped fixture | Three tests, one failure; `64 != 30`; nonzero exit |
| Corrected control | Three tests pass; zero exit |
| Renderer | Eight sections and a complete remediation prompt |
| Readiness | Not ready: no independent agent review was performed |

The script checks those outcomes before generating the example. It writes actual command results to `evidence.json`, uses Unknown document scores and does not claim that an agent discovered the deliberately planted defect. Paths in captured command output are normalized to `<repository>` for sharing. No model calls, dependency installation or network access occur.

The example is deliberately small. It demonstrates a boundary assertion and report delivery; it does not establish improved accuracy, safety or net time savings on real repositories. See [the evaluation guide](../docs/evaluation.md) for useful next measurements.
