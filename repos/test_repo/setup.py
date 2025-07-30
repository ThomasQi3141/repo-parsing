from setuptools import setup, find_packages

setup(
    name="sample_project",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pytest>=7.4.3",
    ],
    author="Sample Author",
    author_email="sample@example.com",
    description="A demonstration of a well-structured Python package",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/example/sample_project",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
) 