from setuptools import setup, find_packages

setup(
    name="hippocampal_ca1_lam",
    version="0.1.0",
    description="Neuromathematical framework for 4-layer laminar CA1 organization",
    author="Neuron7x",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.21.0",
        "scipy>=1.7.0",
        "matplotlib>=3.4.0",
    ],
    extras_require={
        "test": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
        ],
    },
)
