#!/bin/bash

# ML CI/CD Pipeline Demo Script
# This script demonstrates the complete MLOps pipeline

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "\n${PURPLE}$1${NC}"
    echo -e "${PURPLE}$(printf '=%.0s' {1..50})${NC}\n"
}

# Function to wait for user input
wait_for_user() {
    echo -e "\n${CYAN}Press Enter to continue...${NC}"
    read -r
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check requirements
check_requirements() {
    print_header "🔍 Checking Requirements"
    
    local missing_tools=()
    
    if ! command_exists docker; then
        missing_tools+=("docker")
    fi
    
    if ! command_exists docker-compose; then
        missing_tools+=("docker-compose")
    fi
    
    if ! command_exists python; then
        missing_tools+=("python")
    fi
    
    if ! command_exists pip; then
        missing_tools+=("pip")
    fi
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        print_error "Missing required tools: ${missing_tools[*]}"
        echo "Please install these tools before running the demo."
        exit 1
    fi
    
    print_success "All required tools are available!"
}

# Function to setup environment
setup_environment() {
    print_header "🛠️ Setting Up Environment"
    
    print_status "Creating virtual environment..."
    if [ ! -d "venv" ]; then
        python -m venv venv
    fi
    
    print_status "Activating virtual environment..."
    source venv/bin/activate
    
    print_status "Installing Python dependencies..."
    pip install -q -r requirements.txt
    
    print_status "Setting up MLflow..."
    make setup-mlflow > /dev/null 2>&1
    
    print_success "Environment setup completed!"
}

# Function to start services
start_services() {
    print_header "🚀 Starting Services"
    
    print_status "Building Docker images..."
    make docker-build > /dev/null 2>&1
    
    print_status "Starting development environment..."
    make dev > /dev/null 2>&1
    
    print_status "Waiting for services to be ready..."
    sleep 10
    
    # Check if MLflow is running
    if curl -s http://localhost:5000 > /dev/null; then
        print_success "MLflow UI is running at http://localhost:5000"
    else
        print_warning "MLflow UI might still be starting up"
    fi
    
    print_success "Services started successfully!"
    
    echo -e "\n${CYAN}🔗 Available Services:${NC}"
    echo "  • MLflow UI: http://localhost:5000"
    echo "  • Prometheus: http://localhost:9090"
    echo "  • Grafana: http://localhost:3000 (admin/admin)"
}

# Function to run training
run_training() {
    print_header "🎯 Running Model Training"
    
    print_status "Starting model training with MLflow tracking..."
    
    # Run training in background and capture output
    export MLFLOW_TRACKING_URI=http://localhost:5000
    
    # Use quick training for demo
    make train-quick > training.log 2>&1 &
    local train_pid=$!
    
    print_status "Training started (PID: $train_pid)"
    print_status "You can monitor progress at http://localhost:5000"
    
    # Wait for training to complete with progress indicator
    local spin='-\|/'
    local i=0
    while kill -0 $train_pid 2>/dev/null; do
        i=$(( (i+1) %4 ))
        printf "\r${YELLOW}Training in progress... ${spin:$i:1}${NC}"
        sleep 1
    done
    
    wait $train_pid
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        print_success "Training completed successfully!"
        echo -e "\n${CYAN}Check the MLflow UI to see the experiment results:${NC}"
        echo "  http://localhost:5000"
    else
        print_error "Training failed with exit code $exit_code"
        echo "Check training.log for details"
    fi
}

# Function to demonstrate model comparison
compare_models() {
    print_header "📊 Model Comparison & Promotion"
    
    print_status "Comparing model runs..."
    make compare-models
    
    wait_for_user
    
    print_status "Promoting best model to staging..."
    make promote-model
    
    print_success "Model promoted to staging!"
    echo -e "\n${CYAN}You can see the model in the MLflow Model Registry:${NC}"
    echo "  http://localhost:5000/#/models"
}

# Function to demonstrate model serving
demonstrate_serving() {
    print_header "🌐 Model Serving Demo"
    
    print_status "Starting model serving..."
    
    # Start serving in background
    make serve-model > serving.log 2>&1 &
    local serve_pid=$!
    
    print_status "Waiting for model server to start..."
    sleep 15
    
    # Test health endpoint
    if curl -s http://localhost:8080/health > /dev/null; then
        print_success "Model server is healthy!"
        
        print_status "Testing model prediction..."
        
        # Make a sample prediction
        local response=$(curl -s -X POST http://localhost:8080/predict \
            -H "Content-Type: application/json" \
            -d '{"instances": [{"input": "def hello_world():\n    print(\"Hello, World!\")"}]}')
        
        if [ $? -eq 0 ]; then
            print_success "Prediction successful!"
            echo -e "\n${CYAN}Sample prediction response:${NC}"
            echo "$response" | python -m json.tool 2>/dev/null || echo "$response"
        else
            print_warning "Prediction test failed"
        fi
        
        # Stop serving
        kill $serve_pid 2>/dev/null || true
    else
        print_warning "Model server health check failed"
        kill $serve_pid 2>/dev/null || true
    fi
}

# Function to demonstrate CI/CD pipeline
demonstrate_cicd() {
    print_header "🔄 CI/CD Pipeline Demo"
    
    print_status "Running quality gates (linting, formatting, security)..."
    make format-check lint security > /dev/null 2>&1
    
    print_status "Running tests..."
    make test > /dev/null 2>&1
    
    print_success "All quality gates passed!"
    
    print_status "This is what happens in GitHub Actions:"
    echo "  1. ✅ Code formatting check"
    echo "  2. ✅ Linting and type checking"
    echo "  3. ✅ Security scanning"
    echo "  4. ✅ Unit tests with coverage"
    echo "  5. ✅ Integration tests"
    echo "  6. 🚀 Docker image build and push"
    echo "  7. 🌐 Deployment to AWS ECS"
}

# Function to show infrastructure
show_infrastructure() {
    print_header "☁️ Infrastructure Overview"
    
    print_status "Infrastructure components:"
    echo "  • AWS ECS Fargate - Container orchestration"
    echo "  • AWS RDS PostgreSQL - MLflow backend store"
    echo "  • AWS S3 - Model artifacts and data storage"
    echo "  • AWS ECR - Docker image registry"
    echo "  • AWS ALB - Load balancing and SSL termination"
    echo "  • Terraform - Infrastructure as Code"
    
    if [ -d "infra" ]; then
        print_status "Terraform configuration available in ./infra/"
        echo "  Run 'make infra-plan' to see deployment plan"
        echo "  Run 'make infra-apply' to deploy to AWS"
    fi
}

# Function to cleanup
cleanup() {
    print_header "🧹 Cleanup"
    
    print_status "Stopping services..."
    make down > /dev/null 2>&1 || true
    
    print_status "Cleaning up artifacts..."
    rm -f training.log serving.log
    
    print_success "Cleanup completed!"
}

# Function to show final summary
show_summary() {
    print_header "🎉 Demo Summary"
    
    echo -e "${GREEN}✅ Environment Setup${NC}"
    echo -e "${GREEN}✅ Service Orchestration${NC}"
    echo -e "${GREEN}✅ Model Training with MLflow${NC}"
    echo -e "${GREEN}✅ Model Comparison & Promotion${NC}"
    echo -e "${GREEN}✅ Model Serving${NC}"
    echo -e "${GREEN}✅ CI/CD Pipeline${NC}"
    
    echo -e "\n${CYAN}📚 Next Steps:${NC}"
    echo "  • Explore the documentation: make docs-serve"
    echo "  • Deploy to AWS: make infra-apply"
    echo "  • Customize for your use case"
    echo "  • Add more models and experiments"
    
    echo -e "\n${PURPLE}🔗 Useful Links:${NC}"
    echo "  • GitHub Repository: https://github.com/your-username/ml_ci_cd"
    echo "  • Documentation: https://your-username.github.io/ml_ci_cd"
    echo "  • MLflow: https://mlflow.org/"
    echo "  • AWS ECS: https://aws.amazon.com/ecs/"
}

# Main demo function
main() {
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                   🚀 ML CI/CD Pipeline Demo                 ║"
    echo "║                                                              ║"
    echo "║  This demo will showcase a complete MLOps pipeline with:     ║"
    echo "║  • MLflow experiment tracking                                ║"
    echo "║  • Docker containerization                                   ║"
    echo "║  • Model serving with FastAPI                               ║"
    echo "║  • CI/CD with GitHub Actions                                ║"
    echo "║  • AWS deployment with Terraform                            ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}\n"
    
    wait_for_user
    
    # Check if we're in the right directory
    if [ ! -f "README.md" ] || [ ! -f "Makefile" ]; then
        print_error "Please run this script from the project root directory"
        exit 1
    fi
    
    # Run demo steps
    check_requirements
    wait_for_user
    
    setup_environment
    wait_for_user
    
    start_services
    wait_for_user
    
    run_training
    wait_for_user
    
    compare_models
    wait_for_user
    
    demonstrate_serving
    wait_for_user
    
    demonstrate_cicd
    wait_for_user
    
    show_infrastructure
    wait_for_user
    
    cleanup
    
    show_summary
    
    print_success "Demo completed! 🎉"
}

# Handle script interruption
trap cleanup EXIT

# Run main function
main "$@"
