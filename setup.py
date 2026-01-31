from setuptools import setup, find_packages

setup(
    name="strategy_spec",
    version="0.1.0",
    description="Wealthai 量化策略规范",
    packages=find_packages(),
    python_requires=">=3.7",
    install_requires=[
        "pandas>=1.0.0",
        "numpy>=1.18.0",
        "pyyaml>=5.1",
    ],
)
