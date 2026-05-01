import os
import sys
from pathlib import Path

from setuptools import find_packages, setup

PROJECT_ROOT = Path(__file__).parent.resolve()
APP_PATH = PROJECT_ROOT / "app.py"


def get_version():
    return "0.1.0.dev0"


def get_readme():
    readme_path = PROJECT_ROOT / "README.md"
    if readme_path.exists():
        return readme_path.read_text(encoding="utf-8")
    return ""


def get_requirements():
    req_path = PROJECT_ROOT / "requirements.txt"
    if req_path.exists():
        lines = req_path.read_text(encoding="utf-8").strip().split("\n")
        return [line.strip() for line in lines if line.strip() and not line.startswith("#")]
    return []


setup(
    name="wgui4vasp",
    version=get_version(),
    description="A Web-based GUI (WGUI) for VASP simulation workflows",
    long_description=get_readme(),
    long_description_content_type="text/markdown",
    author="Longlong Li",
    author_email="longlongli@outlook.com",
    url="https://github.com/llliphys/WGUI4VASP",
    project_urls={
        "Source": "https://github.com/llliphys/WGUI4VASP",
        "Documentation": "https://github.com/llliphys/WGUI4VASP#readme",
    },
    license="MIT",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Chemistry",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    packages=find_packages(exclude=["calctest", ".*", "__pycache__"]),
    py_modules=["app", "run_app"],
    python_requires=">=3.8",
    install_requires=get_requirements(),
    entry_points={
        "console_scripts": [
            "wgui4vasp=run_app:main",

        ],
    },
)