.PHONY: help install build up down restart logs logs-api logs-collector clean test

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install Python dependencies locally
	pip install -r requirements.txt

build: ## Build Docker containers
	docker-compose build

up: ## Start all services
	docker-compose up -d

down: ## Stop all services
	docker-compose down

restart: ## Restart all services
	docker-compose restart

logs: ## View logs from all services
	docker-compose logs -f

logs-api: ## View API logs
	docker-compose logs -f api

logs-collector: ## View collector logs
	docker-compose logs -f collector

logs-db: ## View database logs
	docker-compose logs -f db

clean: ## Remove containers and volumes
	docker-compose down -v
	rm -rf logs/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

test: ## Run tests
	pytest tests/ -v

dev-api: ## Run API locally (without Docker)
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-collector: ## Run collector locally (without Docker)
	python -m app.collector.scheduler

db-shell: ## Access PostgreSQL shell
	docker-compose exec db psql -U streamdata -d streaming_platform

db-backup: ## Backup database
	docker-compose exec db pg_dump -U streamdata streaming_platform > backup_$$(date +%Y%m%d_%H%M%S).sql

db-restore: ## Restore database from backup (usage: make db-restore FILE=backup.sql)
	docker-compose exec -T db psql -U streamdata streaming_platform < $(FILE)

stats: ## Show database statistics
	docker-compose exec db psql -U streamdata -d streaming_platform -c "SELECT COUNT(*) as total_channels FROM channels;"
	docker-compose exec db psql -U streamdata -d streaming_platform -c "SELECT COUNT(*) as total_snapshots FROM live_snapshots;"
	docker-compose exec db psql -U streamdata -d streaming_platform -c "SELECT platform, COUNT(*) as count FROM channels GROUP BY platform;"

quick-start: ## Quick start with setup check
	bash start.sh
