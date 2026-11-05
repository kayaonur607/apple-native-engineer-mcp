# Convenience targets. Everything delegates to scripts/ so CI and humans run the
# same code path.

.PHONY: help verify test test-py test-js swift docs demo doctor benchmark clean

help:
	@echo "apple-native-engineer-mcp"
	@echo ""
	@echo "  make verify    run everything CI runs (validate + tests + swift)"
	@echo "  make test      Python and MCP tests only"
	@echo "  make test-py   Python unit and golden tests"
	@echo "  make test-js   MCP protocol tests (needs npm install)"
	@echo "  make swift     compile fixtures and type-check every snippet"
	@echo "  make docs      regenerate tool READMEs and the SDK reference"
	@echo "  make demo      see the toolkit work on the bundled fixtures"
	@echo "  make doctor    check that this machine can run everything"
	@echo "  make benchmark time the auditors on a synthetic 500-file project"
	@echo "  make clean     remove caches and generated scratch space"

verify:
	./scripts/verify.sh

test: test-py test-js

test-py:
	python3 -m unittest discover -s tests -t tests -v

test-js:
	cd integrations/mcp-server && npm test

swift:
	./scripts/verify-swift.sh

docs:
	python3 scripts/generate_tool_readmes.py
	python3 scripts/generate_whats_new.py
	python3 scripts/validate_repo.py --links

demo:
	./scripts/demo.sh

doctor:
	./scripts/doctor.sh

benchmark:
	python3 scripts/benchmark.py

clean:
	rm -rf .swiftwork **/__pycache__ __pycache__ tests/__pycache__
	@echo "cleaned"
