"""
Setup configuration for AgentGuard Statistical Judge
"""

from setuptools import setup, find_packages
import os

# Read README for long description
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="agentguard-statistical",
    version="1.0.0",
    author="Mothership AI",
    author_email="opensource@mothership-ai.com",
    description="Open-source statistical hallucination detection for AI systems",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/mothership-ai/agentguard-statistical",
    project_urls={
        "Bug Tracker": "https://github.com/mothership-ai/agentguard-statistical/issues",
        "Documentation": "https://docs.agentguard.ai",
        "Homepage": "https://watcher.mothership-ai.com",
        "Source": "https://github.com/mothership-ai/agentguard-statistical",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Linguistic",
    ],
    python_requires=">=3.9",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "isort>=5.10.0",
            "flake8>=5.0.0",
            "mypy>=0.991",
            "pre-commit>=2.20.0",
        ],
        "gpu": [
            "torch[cuda]>=1.12.0",
        ],
        "docs": [
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.0.0",
            "myst-parser>=0.18.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "agentguard-statistical=agentguard_statistical.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "agentguard_statistical": ["*.json", "*.yaml", "*.txt"],
    },
    keywords=[
        "hallucination detection",
        "ai safety",
        "nlp",
        "machine learning",
        "transformers",
        "statistical analysis",
        "uncertainty quantification",
    ],
    zip_safe=False,
)
