#!/bin/bash
# AgentGuard Kubernetes Deployment Script
# October 2025 Enhancement: Production-ready deployment automation

set -e

# Configuration
NAMESPACE="agentguard"
ENVIRONMENT="${ENVIRONMENT:-production}"
VERSION="${VERSION:-2025.10}"
REGISTRY="${REGISTRY:-agentguard}"
IMAGE_TAG="${IMAGE_TAG:-${VERSION}}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed or not in PATH"
        exit 1
    fi
    
    # Check cluster connection
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    # Check Docker (for building images)
    if ! command -v docker &> /dev/null; then
        log_warning "Docker is not installed - skipping image build"
        SKIP_BUILD=true
    fi
    
    log_success "Prerequisites check passed"
}

# Build Docker image
build_image() {
    if [ "$SKIP_BUILD" = true ]; then
        log_warning "Skipping image build"
        return
    fi
    
    log_info "Building Docker image..."
    
    # Build with build args
    docker build \
        -f Dockerfile.k8s \
        --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
        --build-arg VCS_REF="$(git rev-parse --short HEAD)" \
        --build-arg VERSION="${VERSION}" \
        -t "${REGISTRY}/api:${IMAGE_TAG}" \
        -t "${REGISTRY}/api:latest" \
        .
    
    log_success "Docker image built successfully"
}

# Push Docker image
push_image() {
    if [ "$SKIP_BUILD" = true ]; then
        log_warning "Skipping image push"
        return
    fi
    
    log_info "Pushing Docker image..."
    
    docker push "${REGISTRY}/api:${IMAGE_TAG}"
    docker push "${REGISTRY}/api:latest"
    
    log_success "Docker image pushed successfully"
}

# Create namespace
create_namespace() {
    log_info "Creating namespace..."
    
    if kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_warning "Namespace $NAMESPACE already exists"
    else
        kubectl apply -f k8s/namespace.yaml
        log_success "Namespace created"
    fi
}

# Deploy secrets
deploy_secrets() {
    log_info "Deploying secrets..."
    
    # Check if secrets file exists and has been customized
    if [ ! -f "k8s/secrets.yaml" ]; then
        log_error "Secrets file not found. Please create k8s/secrets.yaml"
        exit 1
    fi
    
    # Check if secrets contain placeholder values
    if grep -q "your_.*_here" k8s/secrets.yaml; then
        log_error "Secrets file contains placeholder values. Please update with actual secrets."
        log_error "Use: kubectl create secret generic agentguard-secrets --from-literal=CLAUDE_API_KEY=your_key"
        exit 1
    fi
    
    kubectl apply -f k8s/secrets.yaml
    log_success "Secrets deployed"
}

# Deploy configuration
deploy_config() {
    log_info "Deploying configuration..."
    
    kubectl apply -f k8s/configmap.yaml
    log_success "Configuration deployed"
}

# Deploy RBAC
deploy_rbac() {
    log_info "Deploying RBAC..."
    
    kubectl apply -f k8s/rbac.yaml
    log_success "RBAC deployed"
}

# Deploy storage
deploy_storage() {
    log_info "Deploying storage..."
    
    kubectl apply -f k8s/pvc.yaml
    log_success "Storage deployed"
}

# Deploy StatefulSets
deploy_statefulsets() {
    log_info "Deploying StatefulSets..."
    
    kubectl apply -f k8s/statefulset.yaml
    log_success "StatefulSets deployed"
}

# Deploy services
deploy_services() {
    log_info "Deploying services..."
    
    kubectl apply -f k8s/service.yaml
    log_success "Services deployed"
}

# Deploy applications
deploy_apps() {
    log_info "Deploying applications..."
    
    # Update image tag in deployment
    sed -i.bak "s|image: agentguard/api:.*|image: ${REGISTRY}/api:${IMAGE_TAG}|g" k8s/deployment.yaml
    
    kubectl apply -f k8s/deployment.yaml
    log_success "Applications deployed"
    
    # Restore original file
    mv k8s/deployment.yaml.bak k8s/deployment.yaml
}

# Deploy HPA
deploy_hpa() {
    log_info "Deploying HPA..."
    
    # Check if metrics server is available
    if kubectl get apiservice v1beta1.metrics.k8s.io &> /dev/null; then
        kubectl apply -f k8s/hpa.yaml
        log_success "HPA deployed"
    else
        log_warning "Metrics server not available - skipping HPA deployment"
    fi
}

# Deploy ingress
deploy_ingress() {
    log_info "Deploying ingress..."
    
    # Check if ingress controller is available
    if kubectl get ingressclass nginx &> /dev/null; then
        kubectl apply -f k8s/ingress.yaml
        log_success "Ingress deployed"
    else
        log_warning "NGINX ingress controller not available - skipping ingress deployment"
    fi
}

# Wait for deployments
wait_for_deployments() {
    log_info "Waiting for deployments to be ready..."
    
    # Wait for StatefulSets
    kubectl wait --for=condition=ready pod -l app=agentguard,component=postgres -n "$NAMESPACE" --timeout=300s
    kubectl wait --for=condition=ready pod -l app=agentguard,component=redis -n "$NAMESPACE" --timeout=300s
    
    # Wait for Deployments
    kubectl wait --for=condition=available deployment/agentguard-api -n "$NAMESPACE" --timeout=300s
    kubectl wait --for=condition=available deployment/agentguard-nginx -n "$NAMESPACE" --timeout=300s
    
    log_success "All deployments are ready"
}

# Verify deployment
verify_deployment() {
    log_info "Verifying deployment..."
    
    # Check pod status
    kubectl get pods -n "$NAMESPACE"
    
    # Check service endpoints
    kubectl get endpoints -n "$NAMESPACE"
    
    # Test health endpoint
    if kubectl get service agentguard-nginx -n "$NAMESPACE" &> /dev/null; then
        log_info "Testing health endpoint..."
        kubectl port-forward service/agentguard-nginx 8080:80 -n "$NAMESPACE" &
        PORT_FORWARD_PID=$!
        sleep 5
        
        if curl -f http://localhost:8080/health &> /dev/null; then
            log_success "Health check passed"
        else
            log_warning "Health check failed"
        fi
        
        kill $PORT_FORWARD_PID 2>/dev/null || true
    fi
    
    log_success "Deployment verification complete"
}

# Cleanup function
cleanup() {
    log_info "Cleaning up..."
    kill $PORT_FORWARD_PID 2>/dev/null || true
}

# Set trap for cleanup
trap cleanup EXIT

# Main deployment function
main() {
    log_info "Starting AgentGuard deployment to Kubernetes"
    log_info "Environment: $ENVIRONMENT"
    log_info "Version: $VERSION"
    log_info "Namespace: $NAMESPACE"
    log_info "Registry: $REGISTRY"
    log_info "Image Tag: $IMAGE_TAG"
    
    check_prerequisites
    
    if [ "$1" != "--skip-build" ]; then
        build_image
        push_image
    fi
    
    create_namespace
    deploy_secrets
    deploy_config
    deploy_rbac
    deploy_storage
    deploy_statefulsets
    deploy_services
    deploy_apps
    deploy_hpa
    deploy_ingress
    
    wait_for_deployments
    verify_deployment
    
    log_success "AgentGuard deployment completed successfully!"
    log_info "Access the application at: https://watcher.mothership-ai.com"
    log_info "API documentation: https://api.agentguard.mothership-ai.com/docs"
}

# Handle command line arguments
case "$1" in
    --help|-h)
        echo "Usage: $0 [--skip-build] [--help]"
        echo ""
        echo "Options:"
        echo "  --skip-build    Skip Docker image build and push"
        echo "  --help, -h      Show this help message"
        echo ""
        echo "Environment variables:"
        echo "  ENVIRONMENT     Deployment environment (default: production)"
        echo "  VERSION         Application version (default: 2025.10)"
        echo "  REGISTRY        Docker registry (default: agentguard)"
        echo "  IMAGE_TAG       Docker image tag (default: VERSION)"
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac
