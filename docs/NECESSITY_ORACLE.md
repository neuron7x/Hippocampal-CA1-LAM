# CA1 retrieval ablation protocol

The oracle measures the effect of phase-coded keys, novelty-weighted replay selection, and Hebbian encoder updates on synthetic associative recall. Each ablation shares seeds, episode data and cue noise with its baseline. The effect is the paired recall difference. The reported 95% intervals use a fixed percentile bootstrap over seeds.

The signed prediction registry retains SHA-256 `20be317d26223261b1ffe8434fe229a82b0a7a120e7dd7091f0e82db55a3f269`. It pins the mechanism, knockout, metric and sign. The benchmark code at the run commit fixes episode generation, cue noise, phase context and seed count.

```bash
for context in matched absent opposite; do
    python -m oracle.run_oracle --seeds 24 --phase-context "$context"
done
```

- `matched` gives the query the target episode's stored phase as external information.
- `absent` encodes the query without phase and preserves the original retrieval API behavior.
- `opposite` supplies the target phase plus π as a control. With phase coding disabled, context has no effect.

## Canonical run

Paired 24-seed assay on Python 3.12 with single-threaded BLAS. The installed CLI also runs the same protocol in CI for each supported Python version.

| Phase context | Baseline recall@1 | Phase knockout recall@1 | Paired Δ | 95% interval | Verdict |
| --- | ---: | ---: | ---: | --- | --- |
| Matched | 0.922 | 0.702 | +0.220 | [+0.202, +0.240] | PASS |
| Absent | 0.537 | 0.702 | −0.165 | [−0.193, −0.135] | REFUTED |
| Opposite | 0.000 | 0.702 | −0.702 | [−0.727, −0.676] | REFUTED |

Replay and novelty selection are NULL in all three conditions. This leaves the signed effects unresolved under the assay. A shared linear encoder can change cosine rankings. The phase-key switch also changes two dimensions of the content representation. The measured contrast concerns that implemented switch under each context. The assay provides no electrophysiological validation.

The canonical implementation reindexes all live source-backed keys after replay and persists those source states. Legacy snapshots still support retrieval. Replay refuses to mutate a populated index containing keys without source states.

## Provenance

The oracle originated in `2b496d1cf61e1799fc0fede13eed1926d17d262c`. The matched-context prototype and replay experiments are recorded in `6b5468c8414f495120f8949486c96ee382f5ae45`. Their historical protocol and results are accessible through Git. The first study used a phase-blind query and the original replay implementation. Its estimates are preserved below.

### Original phase-blind run

| mechanism | knockout | Δ(base−ko) | 95% CI | verdict |
|-----------|----------|-----------:|--------|---------|
| replay_consolidation | KO_REPLAY | +0.001 | [−0.002, +0.005] | **NULL** |
| novelty_gated_selection | KO_NOVELTY | +0.002 | [+0.000, +0.006] | **NULL** |
| theta_phase_key | KO_PHASE | −0.167 | [−0.196, −0.137] | **REFUTED** |
