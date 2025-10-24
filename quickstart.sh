#!/bin/bash
# AgentGuard Quick Start Script

echo "=========================================="
echo " AgentGuard Core Detection Engine"
echo " Quick Start Setup"
echo "=========================================="

# Check Python version
echo ""
echo "Checking Python version..."
python_version=$(python3.12 --version 2>&1)
if [ $? -eq 0 ]; then
    echo "✓ $python_version"
else
    echo "✗ Python 3.12 not found. Please install Python 3.12+"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    python3.12 -m venv venv
    echo "✓ Virtual environment created"
else
    echo ""
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --quiet --upgrade pip
echo "✓ pip upgraded"

# Install dependencies
echo ""
echo "Installing dependencies (this may take 5-10 minutes)..."
pip install --quiet -r requirements.txt
if [ $? -eq 0 ]; then
    echo "✓ Dependencies installed successfully"
else
    echo "✗ Failed to install dependencies"
    exit 1
fi

# Check for .env file
echo ""
if [ ! -f ".env" ]; then
    echo "⚠ .env file not found"
    echo ""
    echo "Please create .env file with your Claude API key:"
    echo ""
    echo "  CLAUDE_API_KEY=your_api_key_here"
    echo "  MLFLOW_TRACKING_URI=./mlruns"
    echo "  MLFLOW_EXPERIMENT_NAME=agentguard_prototype"
    echo "  API_HOST=0.0.0.0"
    echo "  API_PORT=8000"
    echo "  LOG_LEVEL=INFO"
    echo ""
    read -p "Enter your Claude API key (or press Enter to skip): " api_key
    if [ ! -z "$api_key" ]; then
        cat > .env << EOF
CLAUDE_API_KEY=$api_key
MLFLOW_TRACKING_URI=./mlruns
MLFLOW_EXPERIMENT_NAME=agentguard_prototype
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
MAX_CONCURRENT_REQUESTS=10
EOF
        echo "✓ .env file created"
    else
        echo "⚠ Skipped .env creation. You'll need to create it manually."
    fi
else
    echo "✓ .env file exists"
fi

# Create necessary directories
echo ""
echo "Creating directories..."
mkdir -p mlruns logs data config
echo "✓ Directories created"

# Test imports
echo ""
echo "Testing imports..."
python -c "import fastapi, anthropic, torch, transformers" 2>&1
if [ $? -eq 0 ]; then
    echo "✓ All dependencies imported successfully"
else
    echo "✗ Import test failed"
    exit 1
fi

# Check CUDA availability
echo ""
echo "Checking GPU availability..."
cuda_available=$(python -c "import torch; print('Yes' if torch.cuda.is_available() else 'No')" 2>&1)
echo "  CUDA available: $cuda_available"

# Print next steps
echo ""
echo "=========================================="
echo " Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Ensure .env file has your Claude API key"
echo "   $ cat .env"
echo ""
echo "2. Start the API server:"
echo "   $ python -m src.api.main"
echo "   # Or with uvicorn:"
echo "   $ uvicorn src.api.main:app --reload"
echo ""
echo "3. Test the health endpoint:"
echo "   $ curl http://localhost:8000/health"
echo ""
echo "4. Run batch tests with CLI:"
echo "   $ python agentguard_cli.py --input data/sample_scenarios.json --output results.json"
echo ""
echo "5. View API documentation:"
echo "   http://localhost:8000/docs"
echo ""
echo "=========================================="

