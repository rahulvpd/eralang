from setuptools import setup, find_packages

setup(
    name="eralang",
    version="2.0.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "era=eralang.cli:main",
        ],
    },
    python_requires=">=3.8",
)
