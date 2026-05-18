# Quickstart

## 1. Fresh Clone

```bash
git clone https://github.com/heathsanchez/mathgraph.git
cd mathgraph
```

## 2. Quick Release Check

```bash
python scripts/run_release_check.py --quick
```

## 3. Public Demo, Advisory Mode

```bash
python scripts/run_public_demo.py --out-dir demo_out
```

## 4. Public Demo, Live Verifier If Lean Is Available

```bash
python scripts/run_public_demo.py \
  --allow-execution \
  --allow-missing-verifier \
  --accept-verified-entries-in-memory \
  --out-dir demo_out
```

## 5. Colab / Local Test Drive

```bash
python scripts/run_colab_testdrive.py --use-current-checkout --quick-smoke
```

## 6. Boundary Reminder

CLI success is not proof. Demo success is not proof. Only verifier, trusted
importer, finite validator, or chain audit evidence promotes truth.
