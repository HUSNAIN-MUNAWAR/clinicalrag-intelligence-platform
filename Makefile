.PHONY: install backend frontend seed open-corpus open-corpus-commercial eval compare test validate run-api run-web docker-up docker-down
install:
	python -m pip install -r backend/requirements.txt
	cd frontend && npm install
backend:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
frontend:
	cd frontend && npm run dev
seed:
	python scripts/seed_demo.py
open-corpus:
	python scripts/download_open_medical_corpus.py --profile portfolio
open-corpus-commercial:
	python scripts/download_open_medical_corpus.py --profile commercial
eval:
	python scripts/run_evaluation.py hybrid
compare:
	python scripts/compare_pipelines.py "What are common symptoms of hypertension?"
test:
	python -m pytest -q backend/tests
validate:
	python scripts/validate_project.py
run-api: backend
run-web: frontend
docker-up:
	docker compose up --build
docker-down:
	docker compose down
