# v4.8.27R Recovery

The original v4.8.27 batch scan found useful cross-repo candidates but produced an oversized `ranked_all.json` because one scanned repository contained more than thirty thousand sorry rows.

Recovery action:

- removed `ranked_all.json`;
- kept compact `ready_queue.json`;
- kept compact `watch_queue.json`;
- kept `repo_summaries.json`;
- kept clone logs and report.

Key result preserved:

- total scanned rows: 33091
- ready candidates: 30
- watch candidates: 144

Best next candidate classes:

- Verified-zkEVM/ArkLib direct local-have residuals;
- ATOMSLab/LFSE2024 lecture calc-step residuals;
- Beneficial-AI-Foundation/vericoding-benchmark local bound proofs.
