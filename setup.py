#!/usr/bin/env python3
"""
Setup script for Eyeguard Eye Strain Detection System.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    with open(requirements_file) as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="eyeguard",
    version="1.0.0",
    author="Gaurav Kumar Mehta",
    author_email="gaurav@example.com",
    description="Eye Strain Detection System using Computer Vision and Machine Learning",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/Eye-Guard",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Image Recognition",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'eyeguard=src.main:main',
            'eyeguard-train=src.ml.model_trainer:main',
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
