.PHONY: dev test eval seed demo lint package report
dev:
	docker compose up --build
seed:
	python scripts/generate_data.py
	python scripts/seed.py
test:
	python -m pytest -q
eval:
	python -m evaluation.run
demo:
	python scripts/smoke_graph.py --live
lint:
	ruff check agent apps/api gigbid_core mcp_servers rag worker simulator scripts tests evaluation conftest.py
	python scripts/repository_checks.py
package:
	python scripts/package_release.py
report:
	python scripts/build_report.py
