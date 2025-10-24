"""
AgentGuard Python SDK Setup
Enterprise-grade Python client library for AI agent safety validation.
"""

from setuptools import setup, find_packages
import os

# Read README for long description
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "AgentGuard Python SDK - Enterprise AI Agent Safety Validation"

# Read requirements
def read_requirements():
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    if os.path.exists(requirements_path):
        with open(requirements_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return [
        'httpx>=0.25.0',
        'websockets>=11.0',
        'pydantic>=2.0.0',
        'asyncio-mqtt>=0.13.0'
    ]

setup(
    name="agentguard-sdk",
    version="1.0.0",
    author="AgentGuard Team",
    author_email="support@agentguard.com",
    description="Enterprise-grade Python SDK for AI agent safety validation and management",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/agentguard/python-sdk",
    project_urls={
        "Documentation": "https://docs.agentguard.com/sdk/python",
        "Source": "https://github.com/agentguard/python-sdk",
        "Tracker": "https://github.com/agentguard/python-sdk/issues",
        "Homepage": "https://agentguard.com"
    },
    packages=find_packages(include=['agentguard_sdk', 'agentguard_sdk.*']),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Security",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "pre-commit>=3.0.0"
        ],
        "docs": [
            "sphinx>=6.0.0",
            "sphinx-rtd-theme>=1.2.0",
            "sphinx-autodoc-typehints>=1.22.0"
        ],
        "all": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "pre-commit>=3.0.0",
            "sphinx>=6.0.0",
            "sphinx-rtd-theme>=1.2.0",
            "sphinx-autodoc-typehints>=1.22.0"
        ]
    },
    entry_points={
        "console_scripts": [
            "agentguard=agentguard_sdk.cli:main",
        ],
    },
    keywords=[
        "ai", "artificial-intelligence", "agent", "safety", "validation", 
        "hallucination", "detection", "enterprise", "security", "compliance",
        "claude", "gpt", "llm", "monitoring", "deployment"
    ],
    include_package_data=True,
    zip_safe=False,
    platforms=["any"],
    license="MIT",
    
    # Metadata for PyPI
    maintainer="AgentGuard Team",
    maintainer_email="support@agentguard.com",
    
    # Security and quality badges
    # These would be displayed on PyPI
    download_url="https://pypi.org/project/agentguard-sdk/",
)
