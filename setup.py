from setuptools import setup, find_packages

setup(
    name="ecommerce-scraper",
    version="1.0.0",
    description="A comprehensive e-commerce web scraper with GUI",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    install_requires=[
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.2",
        "pandas>=2.0.0",
        "openpyxl>=3.1.0",
        "selenium>=4.15.0",
        "webdriver-manager>=4.0.0",
        "lxml>=4.9.0",
    ],
    entry_points={
        "console_scripts": [
            "ecommerce-scraper=main:main",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
) 