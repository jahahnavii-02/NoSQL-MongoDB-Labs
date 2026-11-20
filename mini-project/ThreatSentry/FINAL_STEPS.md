# Finishing ThreatSentry — step by step

## What this patch adds to your `threatsentry/` app
| Gap in your code | Fix |
|---|---|
| Chat showed only the 5 newest threats, Linux only | `retrieval.py`: detects platform + status in the question (Linux/Windows/macOS/Android/iOS × Anticipated/Active/Evolving/Resolved), filters in MongoDB, ranks by Ollama embeddings (keyword fallback) |
| Only Linux/OSV data | `ingestion/seed_curated.py` + `curated_threats.json`: 26 curated records across all 5 platforms and all 4 statuses |
| `mitigation_plans` / `audit_events` collections unused; no fixing | `mitigation_service.py` + `/api/mitigations`: `fix <pkg>` -> plan -> `approve <id>` -> run -> audit. Only confirmed-affected packages, validated names, fixed `apt-get install --only-upgrade` command, **dry-run by default** |
| Scanner hard-wired to `wsl.exe` | `SCANNER_MODE=wsl` (your Windows setup) or `local` (Linux/Docker) |
| No Docker for ThreatSentry (published image is a placeholder) | `Dockerfile` (Ubuntu 24.04 = monitored system), `Dockerfile.frontend`, `docker-compose.yml` |
| `/api/health` said "partial" without Cassandra/Neo4j; answers cut at 160 tokens | Mongo+Ollama required, others optional; token limits configurable |
| Frontend | scan button, mitigation panel with Approve/Reject, API URL via env |
I also removed `faiss-cpu==1.16.0` from requirements (unused, version looks wrong).

## 1. Apply the patch (PowerShell, from the folder containing `integrated-nosql-labs`)
```powershell
Copy-Item -Recurse -Force .\threatsentry-final-patch\threatsentry\* .\integrated-nosql-labs\threatsentry\
Copy-Item -Force .\threatsentry-final-patch\.gitignore .\integrated-nosql-labs\.gitignore
```
Your `.env` is unchanged; add the new keys from `.env.example` (SCANNER_MODE=wsl, MITIGATION_DRY_RUN=true...).

## 2. Run natively (your current Windows + WSL setup)
```powershell
cd integrated-nosql-labs\threatsentry
pip install -r requirements.txt
ollama pull llama3.2:3b ; ollama pull mxbai-embed-large
python -m ingestion.seed_curated                     # curated threats + embeddings
uvicorn backend.main:app --port 8000                 # terminal 1
streamlit run frontend/app.py                        # terminal 2
```

## 3. Run in Docker (what you submit)
```powershell
cd integrated-nosql-labs\threatsentry
docker compose up -d --build
docker compose exec ollama ollama pull llama3.2:3b
docker compose exec ollama ollama pull mxbai-embed-large
docker compose exec backend python -m ingestion.seed_curated
curl -X POST http://localhost:8000/api/intel/ubuntu/sync     # needs internet; fills OSV advisories
curl -X POST http://localhost:8000/api/scans/linux           # scans the container's Ubuntu 24.04
```
Open http://localhost:8501. If port 27133 is taken, stop your local MongoDB or change the mapping.

## 4. Demo script for your faculty
1. "What active threats affect Windows?" / "Resolved Android threats" / "Anticipated threats on Linux" — platform + status filtering.
2. "How do I mitigate regreSSHion?" — grounded answer with steps and sources.
3. Click **Run read-only scan**, ask "show latest scan results".
4. `fix <a package listed as confirmed affected>` -> plan appears -> `approve <id>` -> dry-run output (set `MITIGATION_DRY_RUN=false` in `.env`, `docker compose up -d`, repeat to really apply; verify with `dpkg-query -W <pkg>`).
5. Show `/api/mitigations/` and the `audit_events` collection as the audit trail.
If the scan finds no confirmed-affected packages, that's a valid result: say so, and demo the plan flow with `db.findings` containing an affected record from a re-sync.

## 5. Before you push to GitHub (important)
Your zip contains `.venv` (300 MB), two `.env` files, a `keyfile`, `lab7.zip` (129 MB) and a 193 MB JSON — GitHub rejects files over 100 MB and you must never publish `.env`/keyfile. The new `.gitignore` excludes them. Then:
```powershell
cd integrated-nosql-labs
git init ; git add . ; git status          # check no .env / .venv / zip appears
git commit -m "NoSQL labs 1-18 + ThreatSentry AI"
# create a PRIVATE repo on github.com, then:
git branch -M main
git remote add origin https://github.com/<you>/<repo>.git
git push -u origin main
```
GitHub -> repo -> Settings -> Collaborators -> add your faculty (before the deadline). Optionally push the image:
`docker build -t jahnavii15/threatsentry:1.0 threatsentry && docker push jahnavii15/threatsentry:1.0`.
PDF: one page with your name, USN, repo URL and (optionally) the Docker Hub link.

## Honest limits (say these in your report)
- Real scanning/fixing covers Ubuntu/Debian packages only. Windows, macOS, Android and iOS are answered from the threat knowledge base, not scanned.
- Curated records are a demo set; real feeds come from OSV (and CISA KEV if you add it).
- Fixes run inside the container (or WSL) as root: test on disposable systems.
