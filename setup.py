"""
Translation Evaluator - 共享评估库
用于翻译质量评估的统一库
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="translation-evaluator",
    version="1.0.0",
    author="Translator Team",
    description="统一翻译质量评估库，支持BLEU, COMET, BLEURT, BERTScore, MQM, ChrF",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.20.0",
        "dataclasses; python_version<'3.7'",
    ],
    extras_require={
        "bertscore": ["bert-score>=0.3.13"],
        "comet": ["unbabel-comet>=2.0.0"],
        "bleurt": ["bleurt>=0.0.1"],
        "chrf": ["sacrebleu>=2.0.0"],
        "all": [
            "bert-score>=0.3.13",
            "unbabel-comet>=2.0.0",
            "bleurt>=0.0.1",
            "sacrebleu>=2.0.0",
        ],
    },
)

