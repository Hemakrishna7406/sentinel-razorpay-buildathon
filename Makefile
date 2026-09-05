.PHONY: help lint typecheck test security-scan docker-build deploy rollback

help:
	@echo "Sentinel Infrastructure Commands"
	@echo ""
	@echo "Development:"
	@echo "  make lint              - Run code linters (black, ruff)"
	@echo "  make typecheck         - Run mypy type checking"
	@echo "  make test              - Run pytest with coverage"
	@echo "  make security-scan     - Run security validation"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build      - Build all Docker images"
	@echo "  make docker-push       - Push images to ECR"
	@echo ""
	@echo "Deployment:"
	@echo "  make deploy            - Deploy to production"
	@echo "  make rollback          - Rollback to previous version"
	@echo ""
	@echo "Infrastructure:"
	@echo "  make terraform-init    - Initialize Terraform"
	@echo "  make terraform-plan    - Plan infrastructure changes"
	@echo "  make terraform-apply   - Apply infrastructure changes"

lint:
	black --check .
	ruff check .

typecheck:
	mypy api/ core/ ml/ security/

test:
	pytest tests/ -v --cov=. --cov-report=xml --cov-report=term

security-scan:
	./scripts/security-validator.sh
	bandit -r api/ core/ ml/ security/ -f json

docker-build:
	docker build -t sentinel-api:latest -f docker/Dockerfile.api .
	docker build -t sentinel-worker:latest -f docker/Dockerfile.worker .
	docker build -t sentinel-audit:latest -f docker/Dockerfile.audit .

docker-push:
	./scripts/push-images.sh

deploy:
	./scripts/deploy.sh production

rollback:
	./scripts/rollback.sh

terraform-init:
	cd terraform && terraform init

terraform-plan:
	cd terraform && terraform plan -out=tfplan

terraform-apply:
	cd terraform && terraform apply tfplan

k8s-status:
	kubectl get pods -n sentinel
	kubectl get svc -n sentinel
	kubectl get hpa -n sentinel

logs-api:
	kubectl logs -f deployment/sentinel-api -n sentinel

logs-worker:
	kubectl logs -f deployment/sentinel-worker -n sentinel

monitoring:
	kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80
