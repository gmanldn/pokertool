.PHONY: load-test load-test-headless load-test-quick mutation-test mutation-test-core mutation-test-html mutation-test-reset help

help:
	@echo "PokerTool Testing Commands:"
	@echo ""
	@echo "Load Testing:"
	@echo "  make load-test          - Run load test with web UI (recommended)"
	@echo "  make load-test-headless - Run headless load test (100 users, 60s)"
	@echo "  make load-test-quick    - Quick smoke test (10 users, 30s)"
	@echo ""
	@echo "Mutation Testing:"
	@echo "  make mutation-test      - Run mutation tests on all configured modules"
	@echo "  make mutation-test-core - Run mutation tests on core.py only (faster)"
	@echo "  make mutation-test-html - Generate HTML report from last run"
	@echo "  make mutation-test-reset - Reset mutation testing cache"

load-test:
	@echo "Starting Locust load test with web UI..."
	@echo "Open http://localhost:8089 in your browser"
	@echo "Target host will be http://localhost:5001"
	.venv/bin/locust -f tests/load/locustfile.py --host http://localhost:5001

load-test-headless:
	@echo "Running headless load test: 100 users, spawn rate 10/s, 60s duration"
	@mkdir -p results/load
	.venv/bin/locust -f tests/load/locustfile.py --headless \
		--users 100 --spawn-rate 10 --run-time 60s \
		--host http://localhost:5001 \
		--csv results/load/load_test_$(shell date +%Y%m%d_%H%M%S) \
		--html results/load/report_$(shell date +%Y%m%d_%H%M%S).html

load-test-quick:
	@echo "Running quick smoke test: 10 users, spawn rate 2/s, 30s duration"
	.venv/bin/locust -f tests/load/locustfile.py --headless \
		--users 10 --spawn-rate 2 --run-time 30s \
		--host http://localhost:5001

mutation-test:
	@echo "Running mutation tests on all configured modules..."
	@echo "This may take 10-30 minutes depending on test suite size."
	@echo "Target: 80%+ mutation score"
	@mkdir -p results/mutation
	.venv/bin/mutmut run --paths-to-mutate=src/pokertool/core.py,src/pokertool/database.py,src/pokertool/equity_calculator.py,src/pokertool/gto_calculator.py,src/pokertool/rbac.py,src/pokertool/input_validator.py
	@echo "✓ Mutation testing complete. Run 'make mutation-test-html' to view results."

mutation-test-core:
	@echo "Running mutation tests on core.py only (faster)..."
	.venv/bin/mutmut run --paths-to-mutate=src/pokertool/core.py
	@echo "✓ Core mutation testing complete."
	.venv/bin/mutmut show

mutation-test-html:
	@echo "Generating HTML mutation test report..."
	@mkdir -p results/mutation
	.venv/bin/mutmut html
	@echo "✓ Report generated: htmlcov/index.html"
	@echo "Open with: open htmlcov/index.html"

mutation-test-reset:
	@echo "Resetting mutation testing cache..."
	rm -rf .mutmut-cache
	rm -f .coverage
	@echo "✓ Cache reset complete."
