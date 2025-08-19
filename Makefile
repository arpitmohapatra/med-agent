.PHONY: help setup install-backend install-frontend start-backend start-frontend start-dev stop clean test lint format

# Default target
help:
	@echo "MedQuery MVP - Available Commands:"
	@echo ""
	@echo "Setup:"
	@echo "  setup              - Complete project setup"
	@echo "  install-backend    - Install backend dependencies"
	@echo "  install-frontend   - Install frontend dependencies"
	@echo ""
	@echo "Development:"
	@echo "  start-dev          - Start both backend and frontend in development mode"
	@echo "  start-backend      - Start backend server"
	@echo "  start-frontend     - Start frontend development server"
	@echo ""
	@echo "Docker:"
	@echo "  docker-dev         - Start development environment with Docker"
	@echo "  docker-full        - Start full stack with Docker"
	@echo "  docker-stop        - Stop all Docker containers"
	@echo "  docker-clean       - Clean up Docker containers and volumes"
	@echo ""
	@echo "Data:"
	@echo "  ingest-sample      - Ingest sample medicine data"
	@echo "  ingest-dataset     - Ingest full medicine dataset (248k records)"
	@echo "  ingest-dataset-test- Ingest subset for testing (1k records)"
	@echo "  ingest-kaggle      - Ingest Kaggle dataset"
	@echo "  evaluate           - Run evaluation suite"
	@echo ""
	@echo "Maintenance:"
	@echo "  test               - Run tests"
	@echo "  lint               - Run linters"
	@echo "  format             - Format code"
	@echo "  clean              - Clean build artifacts"

# Setup
setup:
	@echo "🏥 Setting up MedQuery MVP..."
	@python setup.py

install-backend:
	@echo "🐍 Installing backend dependencies..."
	cd backend && python -m venv venv
	cd backend && (source venv/bin/activate || venv/Scripts/activate) && pip install -r requirements.txt

install-frontend:
	@echo "⚛️  Installing frontend dependencies..."
	cd frontend && npm install

# Development
start-dev:
	@echo "🚀 Starting development environment..."
	@make -j2 start-backend start-frontend

start-backend:
	@echo "🐍 Starting backend server..."
	cd backend && (source venv/bin/activate || venv/Scripts/activate) && python main.py

start-frontend:
	@echo "⚛️  Starting frontend development server..."
	cd frontend && npm start

# Docker
docker-dev:
	@echo "🐳 Starting development environment with Docker..."
	docker-compose up elasticsearch kibana

docker-full:
	@echo "🐳 Starting full stack with Docker..."
	docker-compose --profile full-stack --profile kibana up --build

docker-stop:
	@echo "🛑 Stopping Docker containers..."
	docker-compose down

docker-clean:
	@echo "🧹 Cleaning up Docker environment..."
	docker-compose down -v --remove-orphans
	docker system prune -f

# Data
ingest-sample:
	@echo "📥 Ingesting sample data..."
	cd backend && (source venv/bin/activate || venv/Scripts/activate) && python scripts/ingest_data.py --sample

ingest-dataset:
	@echo "📥 Ingesting full medicine dataset..."
	cd backend && (source venv/bin/activate || venv/Scripts/activate) && python scripts/ingest_medicine_dataset.py --verify

ingest-dataset-test:
	@echo "📥 Ingesting medicine dataset (1000 records for testing)..."
	cd backend && (source venv/bin/activate || venv/Scripts/activate) && python scripts/ingest_medicine_dataset.py --max-records 1000 --verify

ingest-kaggle:
	@echo "📥 Ingesting Kaggle dataset..."
	cd backend && (source venv/bin/activate || venv/Scripts/activate) && python scripts/ingest_data.py

evaluate:
	@echo "📊 Running evaluation suite..."
	cd backend && (source venv/bin/activate || venv/Scripts/activate) && python scripts/evaluate.py

# Maintenance
test:
	@echo "🧪 Running tests..."
	cd backend && (source venv/bin/activate || venv/Scripts/activate) && python -m pytest tests/ -v
	cd frontend && npm test -- --coverage --watchAll=false

lint:
	@echo "🔍 Running linters..."
	cd backend && (source venv/bin/activate || venv/Scripts/activate) && flake8 app/ scripts/
	cd frontend && npm run lint

format:
	@echo "✨ Formatting code..."
	cd backend && (source venv/bin/activate || venv/Scripts/activate) && black app/ scripts/
	cd frontend && npm run format

clean:
	@echo "🧹 Cleaning build artifacts..."
	rm -rf backend/venv/
	rm -rf backend/__pycache__/
	rm -rf backend/app/__pycache__/
	rm -rf backend/.pytest_cache/
	rm -rf frontend/node_modules/
	rm -rf frontend/build/
	rm -rf frontend/.eslintcache
