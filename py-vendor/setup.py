from setuptools import setup, find_namespace_packages


setup(
    name='deep-serverless',
    version='1.0.4',
    description='Sharable modules from Deep serverlss',
    long_description_content_type='text/markdown',
    long_description=open('./README.md').read(),
    license="MIT",

    author='TC Dev',
    author_email='dev@togglecorp.com',
    url='https://github.com/the-deep/serverless',

    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Topic :: Utilities",
        "Operating System :: OS Independent",
    ],

    packages=find_namespace_packages(),
    # packages=find_packages(exclude=("tests", "tests.*")),
    install_requires=[
        'boto3==1.9.88',
        'pynamodb==4.3.2',
        'requests==2.21.0',
    ],
    zip_safe=False,
)
