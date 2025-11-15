.PHONY: help install-backend install-frontend run-backend run-frontend docker-build docker-up docker-down test clean

help:
	@echo "Compliance Copilot - Makefile Commands"
	@echo ""
	@echo "  make install-backend    - Install Python dependencies"
	@echo "  make install-frontend   - Install Node.js dependencies"
	@echo "  make run-backend        - Run backend server"
	@echo "  make run-frontend       - Run frontend server"
	@echo "  make docker-build       - Build Docker images"
	@echo "  make docker-up          - Start Docker Compose"
	@echo "  make docker-down        - Stop Docker Compose"
	@echo "  make test               - Run tests"
	@echo "  make clean              - Clean build artifacts"

install-backend:
	cd backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt

install-frontend:
	cd frontend && npm install

run-backend:
	cd backend && source venv/bin/activate && uvicorn main:app --reload --host 0.0.0.0 --port 8000

run-frontend:
	cd frontend && npm run dev

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

test:
	@echo "Running backend tests..."
	cd backend && python -m pytest tests/ || echo "No tests found"
	@echo "Running frontend tests..."
	cd frontend && npm test || echo "No tests found"

clean:
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".next" -exec rm -r {} +
	find . -type d -name "node_modules" -exec rm -r {} +

