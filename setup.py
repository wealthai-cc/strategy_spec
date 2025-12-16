"""
Setup script for WealthAI Strategy Execution Engine.
"""

from setuptools import setup, find_packages

setup(
    name="wealthai-strategy-engine",
    version="0.1.0",
    description="Strategy execution engine for WealthAI (JoinQuant-style)",
    author="WealthAI",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "protobuf>=4.21.0",
        "grpcio>=1.50.0",
        "grpcio-tools>=1.50.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.2.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "mypy>=1.0.0",
        ],
    },
)

