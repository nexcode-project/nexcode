from setuptools import setup, find_packages

setup(
    name='nexcode',
    version='0.1.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'click',
        'openai',
        'pyyaml',
    ],
    entry_points={
        'console_scripts': [
            'nexcode = nexcode.cli:cli',
        ],
    },
    author='Your Name',
    author_email='your.email@example.com',
    description='A CLI tool to generate git commits using AI',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/YOUR_USERNAME/nexcode',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.7',
) 