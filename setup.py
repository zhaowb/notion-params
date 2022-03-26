import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="notion-params",
    version="0.0.2",
    author="Wenbo Zhao",
    author_email="zhaowb@gmail.com",
    description="Helper to build Notion API params, parse markdown text into Notion API blocks",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/zhaowb/notion-params.git",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
        'marko==1.2.0',
        'pydash',
        'requests',
        'backoff',
    ],
    py_modules=['notion_params']
)
