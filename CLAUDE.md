General guidelines:

* use uv and python 3.11 
* all url endpoints of APIs and services need to be hosted with a prefix like /appname/ so that they can be hosted behind an nginx proxy.
* all urls for endpoints need to end with a / to make them easier for my reverse proxy to handle
* projects should create a virtual environment in ~/dev/.venvs/{project-name} and a symbolic link .venv so that uv will use that virtual environment
* worktree folders can then create their own symbolic link to avoid folder path troubles getting to the .venv 
* use a Makefile to manage devops tasks like init start stop docker-start docker-stop docker-build docker-redeploy
* the README.md should be our project documentation, the CLAUDE.md file should stay basic