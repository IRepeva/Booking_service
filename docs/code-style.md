<h1>Code agreement</h1>
To ensure code consistency in the project, we use pre-commit, which includes several code analyzers:

- autopep8
- black
- isort
- flake8, 
as well as several checks, such as a ban on committing to the main branch, etc.

On every commit, the checks will be run, as well as code reformatting.

<h3>Working specifics</h3>
1. When formatting, the commit is not executed. Updated files are added to the git index, after which a commit needs to be made again.
2. flake8 does not format files on its own, but only provides a report on inconsistencies. The inconsistencies need to be fixed manually.

<h3>Installing pre-commit</h3>
To start working with pre-commit, you need to install them first:
```shell
pip install pre-commit 
```
Alternatively, you can install all project dependencies:
```shell
pip install -r deploy/requirements.txt
```
Then, run the following command:
```shell
pre-commit install
```