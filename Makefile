.PHONY: pipeline dashboard test up

pipeline:
	python -m src.pipeline

dashboard:
	streamlit run dashboard/app.py

test:
	pytest -q

up:
	docker compose up --build

