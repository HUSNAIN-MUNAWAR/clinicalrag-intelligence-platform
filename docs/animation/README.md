# ClinicalRAG animation artifact

Run `python scripts/generate_clinicalrag_animation.py` from the repository root. The command rebuilds the synthetic demo corpus in a temporary runtime, exercises the real local services, and regenerates the JSON scene manifest and HTML reel.

For model-backed evidence, run `python scripts/generate_real_runtime_video.py` after installing the backend requirements. That path loads the real local sentence-transformer, writes an MP4, and preserves retrieval/citation/safety/evaluation traces in [`REAL_RUNTIME.md`](REAL_RUNTIME.md).
