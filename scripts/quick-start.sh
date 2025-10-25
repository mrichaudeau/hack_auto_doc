#!/bin/bash
# Quick Start Script for Technology Watch Platform (Docker)
# This script sets up and starts the entire Docker development environment

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored message
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Print section header
print_header() {
    echo ""
    print_message "$BLUE" "=============================================="
    print_message "$BLUE" "$1"
    print_message "$BLUE" "=============================================="
    echo ""
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Main script starts here
print_header "Technology Watch Platform - Quick Start"

# Step 1: Check prerequisites
print_header "Step 1: Checking Prerequisites"

if ! command_exists docker; then
    print_message "$RED" "✗ Docker is not installed!"
    print_message "$YELLOW" "Please install Docker Desktop from: https://www.docker.com/products/docker-desktop"
    exit 1
fi
print_message "$GREEN" "✓ Docker is installed"

if ! command_exists docker-compose; then
    print_message "$RED" "✗ Docker Compose is not installed!"
    print_message "$YELLOW" "Please install Docker Compose"
    exit 1
fi
print_message "$GREEN" "✓ Docker Compose is installed"

# Step 2: Check if .env file exists
print_header "Step 2: Environment Configuration"

if [ ! -f .env ]; then
    print_message "$YELLOW" "⚠ .env file not found. Creating from template..."

    if [ -f .env.example ]; then
        cp .env.example .env
        print_message "$GREEN" "✓ .env file created from .env.example"
        print_message "$YELLOW" "⚠ IMPORTANT: Please edit .env file and configure your settings!"
        print_message "$YELLOW" "   - Set a secure DJANGO_SECRET_KEY"
        print_message "$YELLOW" "   - Set a secure POSTGRES_PASSWORD"
        print_message "$YELLOW" "   - Configure email settings if needed"
        print_message "$YELLOW" "   - Add AI API keys when ready"
        echo ""
        read -p "Press Enter after you've configured .env (or press Ctrl+C to exit)..."
    else
        print_message "$RED" "✗ .env.example not found!"
        exit 1
    fi
else
    print_message "$GREEN" "✓ .env file exists"
fi

# Step 3: Stop any existing containers
print_header "Step 3: Cleaning Up Existing Containers"

if [ "$(docker-compose ps -q)" ]; then
    print_message "$YELLOW" "Stopping existing containers..."
    docker-compose down
    print_message "$GREEN" "✓ Existing containers stopped"
else
    print_message "$GREEN" "✓ No existing containers to stop"
fi

# Step 4: Build Docker images
print_header "Step 4: Building Docker Images"

print_message "$YELLOW" "This may take several minutes on first run..."
docker-compose build
print_message "$GREEN" "✓ Docker images built successfully"

# Step 5: Start services
print_header "Step 5: Starting Services"

print_message "$YELLOW" "Starting all services in background..."
docker-compose up -d
print_message "$GREEN" "✓ All services started"

# Step 6: Wait for services to be healthy
print_header "Step 6: Waiting for Services to be Ready"

print_message "$YELLOW" "Waiting for database..."
timeout=60
elapsed=0
while ! docker-compose exec -T db pg_isready -U postgres >/dev/null 2>&1; do
    if [ $elapsed -ge $timeout ]; then
        print_message "$RED" "✗ Database failed to start after ${timeout}s"
        docker-compose logs db
        exit 1
    fi
    echo -n "."
    sleep 2
    elapsed=$((elapsed + 2))
done
print_message "$GREEN" "✓ Database is ready"

print_message "$YELLOW" "Waiting for Redis..."
elapsed=0
while ! docker-compose exec -T redis redis-cli ping >/dev/null 2>&1; do
    if [ $elapsed -ge $timeout ]; then
        print_message "$RED" "✗ Redis failed to start after ${timeout}s"
        docker-compose logs redis
        exit 1
    fi
    echo -n "."
    sleep 2
    elapsed=$((elapsed + 2))
done
print_message "$GREEN" "✓ Redis is ready"

# Step 7: Run database migrations
print_header "Step 7: Running Database Migrations"

print_message "$YELLOW" "Applying database migrations..."
docker-compose exec -T backend python manage.py migrate
print_message "$GREEN" "✓ Migrations applied successfully"

# Step 8: Create superuser (optional)
print_header "Step 8: Create Superuser (Optional)"

print_message "$YELLOW" "Do you want to create a Django superuser? (y/n)"
read -r create_superuser

if [ "$create_superuser" = "y" ]; then
    docker-compose exec backend python manage.py createsuperuser
    print_message "$GREEN" "✓ Superuser created"
else
    print_message "$YELLOW" "Skipping superuser creation"
fi

# Step 9: Display service status
print_header "Step 9: Service Status"

docker-compose ps

# Step 10: Display access information
print_header "🎉 Setup Complete! 🎉"

print_message "$GREEN" "All services are running successfully!"
echo ""
print_message "$BLUE" "Access the application at:"
echo "  • Frontend:     http://localhost:3000"
echo "  • Backend API:  http://localhost:8000/api/"
echo "  • Admin Panel:  http://localhost:8000/admin/"
echo ""
print_message "$BLUE" "Useful commands:"
echo "  • View logs:           docker-compose logs -f"
echo "  • View backend logs:   docker-compose logs -f backend"
echo "  • View frontend logs:  docker-compose logs -f frontend"
echo "  • Stop services:       docker-compose stop"
echo "  • Restart services:    docker-compose restart"
echo "  • Shutdown:            docker-compose down"
echo "  • Rebuild:             docker-compose up -d --build"
echo ""
print_message "$YELLOW" "Note: Frontend may take a few moments to compile on first start"
print_message "$YELLOW" "Check logs with: docker-compose logs -f frontend"
echo ""

# Optional: Open browser
print_message "$YELLOW" "Open frontend in browser? (y/n)"
read -r open_browser

if [ "$open_browser" = "y" ]; then
    if command_exists xdg-open; then
        xdg-open http://localhost:3000
    elif command_exists open; then
        open http://localhost:3000
    elif command_exists start; then
        start http://localhost:3000
    else
        print_message "$YELLOW" "Could not detect browser command. Please open http://localhost:3000 manually"
    fi
fi

print_message "$GREEN" "Happy coding! 🚀"
