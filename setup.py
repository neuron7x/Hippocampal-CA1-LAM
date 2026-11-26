from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="Hippocampal-CA1-LAM",
    version="2.0.0",
    author="neuron7x",
    description="Research model of hippocampal CA1 laminar architecture and AI memory",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/neuron7x/Hippocampal-CA1-LAM",
    packages=find_packages(exclude=["tests", "examples", "docs"]),
    py_modules=["test_golden_standalone"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
    python_requires=">=3.11",
    install_requires=[
        "numpy>=1.24.0",
        "scipy>=1.10.0",
        "scikit-learn>=1.2.0",
        "PyYAML>=6.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "flake8>=6.0.0",
            "black>=23.0.0",
            "mypy>=1.5.0",
            "matplotlib>=3.7.0",
            "Pillow>=13.0",
        ],
        "viz": [
            "matplotlib>=3.7.0",
            "Pillow>=13.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "ca1-test=test_golden_standalone:main",
        ],
    },
)
