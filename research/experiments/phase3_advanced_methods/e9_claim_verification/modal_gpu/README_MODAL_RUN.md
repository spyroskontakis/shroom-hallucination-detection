# Modal: frozen E9-B → E10 στην ίδια A100-80GB

Το [Modal wrapper](https://github.com/spyroskontakis/shroom-hallucination-detection/blob/11822d92070cd29360445cb4dacd8d110c655248/RAG/results/phase3_e9_claim_verification/modal_gpu/modal_phase3_gpu.py) διαβάζει μόνο τα δύο ήδη παγωμένα ZIP:
`../minicheck_gpu/minicheck_gpu_portable.zip` και
`../factcg_gpu/factcg_gpu_portable.zip`. Δεν μεταφέρει το checkout ή άλλα δεδομένα.
Πρώτα τρέχει τον υπάρχοντα MiniCheck runner και validator, μετά τον υπάρχοντα
FactCG runner και validator. Ένα Modal function/container κρατά μία GPU για όλη
τη διαδοχική εκτέλεση. Κάθε runner εκτελείται ως ξεχωριστό subprocess ώστε να
απελευθερώνεται η μνήμη της GPU πριν ξεκινήσει το επόμενο μοντέλο.

Το image είναι Linux/Python 3.11. Κατά το build αντιγράφει τα δύο ZIP, τα
αποσυμπιέζει πραγματικά κάτω από
`/opt/SHROOM/SHROOM2024/RAG/results/phase3_e9_claim_verification/` και
εγκαθιστά τα υπάρχοντα `requirements_gpu.lock.txt` σε **δύο
διαφορετικά virtual environments**. Δεν φορτώνει βάρη ή GPU κατά το build.
Οι εγκαταστάσεις μπορούν να πάρουν χρόνο και χώρο, ειδικά για vLLM/PyTorch.
Το function ζητά ακριβώς `gpu="A100-80GB"` (μία GPU), 8 CPU, 64 GiB RAM,
512 GiB προσωρινό δίσκο και timeout 4 ωρών. Ελέγχει το πραγματικό όνομα/VRAM
με `nvidia-smi` πριν από inference. Οι runners διατηρούν τις δικές τους
προϋποθέσεις, precision, backend, μοντέλα και pinned revisions.

## Τοπικός έλεγχος χωρίς χρέωση GPU

Από τη ρίζα του repository:

```powershell
python -B RAG/results/phase3_e9_claim_verification/modal_gpu/modal_phase3_gpu.py --validate-local
```

Ελέγχονται οι SHA-256 των δύο ZIP, τα ενσωματωμένα frozen manifests και όλα τα
members, τα ακριβή input hashes, οι επιτρεπόμενες στήλες, 561/575 MiniCheck
samples/claims και 561 FactCG samples, τα μοντέλα/revisions και η απουσία
πρόσθετων αρχείων δεδομένων. Αυτός ο έλεγχος δεν εγκαθιστά image και δεν καλεί
remote GPU.

## Εκτέλεση στο Modal — **μόνο όταν αποφασίσετε να ξεκινήσει η χρεώσιμη εργασία**

Το Modal CLI 1.5.5 είναι ήδη authenticated. Από τη ρίζα του repository:

```powershell
python -m modal run RAG/results/phase3_e9_claim_verification/modal_gpu/modal_phase3_gpu.py --run-id phase3-001
```

Δώστε νέο `run-id` για κάθε προσπάθεια. Επιτρέπονται ASCII γράμματα, αριθμοί,
`_` και `-` (1–64 χαρακτήρες). Δεν γίνεται overwrite προηγούμενου run.
Η πρώτη εκτέλεση χτίζει το image και κατεβάζει τα δύο δημόσια checkpoints.
Δεν απαιτείται επιπλέον Modal Secret/Hugging Face token για τα δημόσια μοντέλα·
χρειάζονται τα ήδη ρυθμισμένα Modal credentials και πρόσβαση στο διαδίκτυο.
Δεν υπάρχει CPU fallback ή αλλαγή μοντέλου/quantization. Εάν αποτύχει MiniCheck
preflight/validation, η FactCG **δεν** ξεκινά και ο ακριβής λόγος διατηρείται στο
runner report και στο `FAILED.json`.

## Μόνιμα outputs και λήψη

Χρησιμοποιείται Modal Volume `shroom-phase3-frozen-gpu-results`, mounted στο
`/results`. Για το παραπάνω run, οι έξοδοι βρίσκονται στα:

```text
runs/phase3-001/minicheck_gpu_run/minicheck_scores.jsonl
runs/phase3-001/minicheck_gpu_run/MINICHECK_GPU_REPORT.json
runs/phase3-001/minicheck_gpu_run/MINICHECK_GPU_REPORT.md
runs/phase3-001/minicheck_gpu_run/environment_freeze.txt
runs/phase3-001/factcg_gpu_run/factcg_scores.jsonl
runs/phase3-001/factcg_gpu_run/FACTCG_GPU_REPORT.json
runs/phase3-001/factcg_gpu_run/FACTCG_GPU_REPORT.md
runs/phase3-001/factcg_gpu_run/environment_freeze.txt
```

Το Volume γίνεται commit αμέσως μετά το MiniCheck, μετά το FactCG και κατά
την αποτυχία. Υπάρχουν επίσης `STARTED.json`, ανά-stage `*_PASS.json`, και
`COMPLETE.json` ή `FAILED.json` στο `runs/phase3-001/`.
Για επισκόπηση και λήψη από PowerShell (με αντίστοιχο `$run`):

```powershell
$run = 'phase3-001'
$volume = 'shroom-phase3-frozen-gpu-results'
$phase = 'RAG/results/phase3_e9_claim_verification'
python -m modal volume ls $volume "runs/$run"
New-Item -ItemType Directory -Force "$phase/minicheck_gpu/returned_$run" | Out-Null
New-Item -ItemType Directory -Force "$phase/factcg_gpu/returned_$run" | Out-Null
python -m modal volume get $volume "runs/$run/minicheck_gpu_run/minicheck_scores.jsonl" "$phase/minicheck_gpu/returned_$run/minicheck_scores.jsonl"
python -m modal volume get $volume "runs/$run/minicheck_gpu_run/MINICHECK_GPU_REPORT.json" "$phase/minicheck_gpu/returned_$run/MINICHECK_GPU_REPORT.json"
python -m modal volume get $volume "runs/$run/factcg_gpu_run/factcg_scores.jsonl" "$phase/factcg_gpu/returned_$run/factcg_scores.jsonl"
python -m modal volume get $volume "runs/$run/factcg_gpu_run/FACTCG_GPU_REPORT.json" "$phase/factcg_gpu/returned_$run/FACTCG_GPU_REPORT.json"
```

Για επιπλέον logs κατεβάστε επίσης τα αντίστοιχα `.md` και
`environment_freeze.txt` με την ίδια εντολή `volume get`. Έπειτα μπορούν να
χρησιμοποιηθούν οι υπάρχοντες τοπικοί validators/importers των δύο πακέτων.
Η εκτέλεση του Modal wrapper δεν τους καλεί και δεν τρέχει Random Forest.

Modal τεκμηρίωση: [GPU types](https://modal.com/docs/guide/gpu),
[image file copy](https://modal.com/docs/guide/images),
[Volume download](https://modal.com/docs/cli/latest/volume),
[local entrypoints](https://modal.com/docs/guide/apps).
