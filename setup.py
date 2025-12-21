"""
Setup script for python-rate-limiter package.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="python-rate-limiter",
    version="1.0.0",
    author="Sudhanshu Shekhar",
    author_email="shekhar349@gmail.com",
    description="A Python rate limiter library for FastAPI, Flask, and Django applications",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/shekhar349/python-rate-limiter",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[],
    extras_require={
        "fastapi": ["fastapi>=0.68.0"],
        "flask": ["flask>=2.0.0"],
        "django": ["django>=3.2.0"],
        "all": ["fastapi>=0.68.0", "flask>=2.0.0", "django>=3.2.0"],
    },
)

