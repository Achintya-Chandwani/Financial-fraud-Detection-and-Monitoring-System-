# FraudShield AI — editable install
# This allows running `uvicorn backend.main:app` from the project root
# by making the root a proper Python package root.
from setuptools import setup, find_packages

setup(
    name="fraudshield-ai",
    version="1.0.0",
    packages=find_packages(),
    python_requires=">=3.10",
)
