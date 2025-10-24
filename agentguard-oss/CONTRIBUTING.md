# Contributing to AgentGuard Statistical Judge

Thank you for your interest in contributing to AgentGuard Statistical Judge! This document provides guidelines and information for contributors.

## 🤝 How to Contribute

### Reporting Issues

1. **Search existing issues** first to avoid duplicates
2. **Use issue templates** when available
3. **Provide detailed information**:
   - Python version and OS
   - AgentGuard version
   - Minimal code example
   - Expected vs actual behavior
   - Full error traceback

### Suggesting Features

1. **Check the roadmap** in README.md first
2. **Open a feature request** with:
   - Clear use case description
   - Proposed API design
   - Implementation considerations
   - Potential alternatives

### Code Contributions

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** following our coding standards
4. **Add tests** for new functionality
5. **Update documentation** as needed
6. **Submit a pull request**

## 🛠️ Development Setup

### Prerequisites

- Python 3.9+
- Git
- Virtual environment tool (venv, conda, etc.)

### Setup Steps

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/agentguard-statistical.git
cd agentguard-statistical

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=agentguard_statistical

# Run specific test file
pytest tests/test_statistical_judge.py

# Run with verbose output
pytest -v
```

### Code Quality

We use several tools to maintain code quality:

```bash
# Format code
black agentguard_statistical/
isort agentguard_statistical/

# Lint code
flake8 agentguard_statistical/

# Type checking
mypy agentguard_statistical/

# Run all checks
pre-commit run --all-files
```

## 📝 Coding Standards

### Python Style

- Follow **PEP 8** style guide
- Use **Black** for code formatting
- Use **isort** for import sorting
- Maximum line length: **88 characters**
- Use **type hints** for all public functions

### Documentation

- **Docstrings** for all public functions and classes
- Use **Google style** docstrings
- Include **examples** in docstrings when helpful
- Update **README.md** for significant changes

### Example Function Documentation

```python
def evaluate(self, agent_output: str, context: Optional[str] = None) -> Tuple[float, List[float]]:
    """
    Evaluate text for hallucination indicators.
    
    Args:
        agent_output: Text to evaluate for hallucination indicators
        context: Optional context for comparison
        
    Returns:
        Tuple of (hallucination_score, confidence_interval)
        
    Example:
        >>> judge = StatisticalJudge()
        >>> score, confidence = judge.evaluate("The sky is green")
        >>> print(f"Score: {score:.3f}")
    """
```

### Testing Standards

- **Unit tests** for all public methods
- **Integration tests** for complex workflows
- **Minimum 80% code coverage**
- Use **pytest** framework
- Mock external dependencies

### Example Test

```python
def test_evaluate_basic():
    """Test basic evaluation functionality."""
    judge = StatisticalJudge()
    score, confidence = judge.evaluate("Test text")
    
    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0
    assert isinstance(confidence, list)
    assert len(confidence) == 2
```

## 🏗️ Project Structure

```
agentguard-statistical/
├── agentguard_statistical/
│   ├── __init__.py          # Package initialization
│   ├── statistical_judge.py # Main judge implementation
│   ├── utils.py            # Utility functions
│   ├── metrics.py          # Evaluation metrics
│   └── cli.py              # Command-line interface
├── tests/
│   ├── test_statistical_judge.py
│   ├── test_utils.py
│   └── test_metrics.py
├── docs/                   # Documentation
├── examples/               # Usage examples
├── README.md
├── CONTRIBUTING.md
├── LICENSE
├── setup.py
└── requirements.txt
```

## 🎯 Contribution Areas

### High Priority

- 🐛 **Bug fixes** and stability improvements
- 📊 **Performance optimizations** for faster inference
- 🧪 **Test coverage** improvements
- 📚 **Documentation** enhancements

### Medium Priority

- 🌍 **Multilingual support** for non-English text
- 📈 **New statistical methods** for detection
- 🔌 **Framework integrations** (LangChain, etc.)
- 📊 **Benchmarking** on new datasets

### Future Features

- 🖼️ **Multimodal support** (images, video)
- ⚡ **Model quantization** for edge deployment
- 🔄 **Streaming evaluation** for real-time use
- 🎛️ **Configuration management** improvements

## 📋 Pull Request Process

### Before Submitting

1. **Ensure tests pass**: `pytest`
2. **Check code quality**: `pre-commit run --all-files`
3. **Update documentation** if needed
4. **Add changelog entry** for significant changes

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] Added tests for new functionality
- [ ] Updated documentation

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
```

### Review Process

1. **Automated checks** must pass
2. **Code review** by maintainers
3. **Testing** on multiple environments
4. **Documentation review** if applicable
5. **Merge** after approval

## 🏷️ Release Process

### Version Numbering

We follow **Semantic Versioning** (semver):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

1. Update version in `setup.py` and `__init__.py`
2. Update `CHANGELOG.md`
3. Create release PR
4. Tag release: `git tag v1.0.0`
5. Push tags: `git push --tags`
6. GitHub Actions handles PyPI deployment

## 🤔 Questions?

### Getting Help

- 💬 **Discord**: [Join our community](https://discord.gg/agentguard)
- 📧 **Email**: opensource@mothership-ai.com
- 🐛 **Issues**: [GitHub Issues](https://github.com/mothership-ai/agentguard-statistical/issues)
- 📖 **Docs**: [Documentation](https://docs.agentguard.ai)

### Maintainers

- **Sean McDonnell** - [@seanebones-lang](https://github.com/seanebones-lang)
- **Mothership AI Team** - [@mothership-ai](https://github.com/mothership-ai)

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## 🙏 Recognition

Contributors are recognized in:
- **README.md** contributors section
- **Release notes** for significant contributions
- **Hall of Fame** for major contributors

Thank you for helping make AgentGuard better! 🚀
