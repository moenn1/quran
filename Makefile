.PHONY: lint docs backend-test frontend-test cli-test data-validation e2e smoke-compose release-readiness

lint:
	./scripts/lint-repo.sh

docs:
	./scripts/check-docs.sh

backend-test:
	./scripts/run-backend-tests.sh

frontend-test:
	./scripts/run-frontend-tests.sh

cli-test:
	./scripts/run-cli-tests.sh

data-validation:
	./scripts/run-data-validation.sh

e2e:
	./scripts/run-e2e.sh

smoke-compose:
	./scripts/smoke-compose.sh

release-readiness:
	./scripts/release-readiness.sh
