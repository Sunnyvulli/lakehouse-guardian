# Failure analysis

**Observed miss:** in three seeded batches, 30 real rows per batch had both `casual` and `cnt` increased by 50. Dates, domains, uniqueness, and arithmetic remained plausible. The row detector missed all 90 altered rows. Across the full set of injected row faults this reduced recall to 0.80, while precision remained 1.00. These counts come from results/evaluation.json.

**Why:** arithmetic consistency cannot prove a sensor/source observation is true. Adding a rule that merely recognizes this fixture would overfit the evaluator. A meaningful next step is an independently labeled source, robust seasonal residual monitoring, and evaluation of investigation burden.

**False-alarm boundary:** there were zero alarms on three exact clean-source replays. This is a tiny and easy control set. A humidity threshold without seasonality may flag legitimate winter/summer changes; no low production false-positive rate is inferred.

**Workflow misuse:** tests supply a rejection, a different proposal hash, an instruction string and a string-valued boolean. None reaches publication. These are local typed-boundary tests, not a prompt-injection benchmark against a language model.

**Runtime failure:** Airflow's task supervisor could not consistently resolve its own PID through psutil in the authoring sandbox. No patch or fake success was substituted. Its CI integration uses the normal GitHub-hosted process environment; check that job before claiming a verified Airflow run.
