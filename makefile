.PHONY: help

help: ## Show this help.
    # From: https://gist.github.com/prwhite/8168133
	@grep -E '^[a-z.A-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-35s\033[0m %s\n", $$1, $$2}'

VERSION="1.0.0"

docker_destroy: docker_stop_containers docker_rm_stopped_containers docker_destroy_image ## Destroy Docker Container and Image
reset_docker_and_pipfile_libraries: docker_destroy reset_pipenv_dependencies docker_build_image_nocache ## Destroy Docker Image, Rebuild requirement.txt based on Pipenv Pipfile, Create Docker Image no cache

docker_build_image_nocache: ## Build Image and ensure to account for requirements.txt changes
	docker build --no-cache -t langchain-streamlit-agent:latest .

docker_list_images:
	docker image ls

docker_list_containers:
	docker ps -a

local_build_streamlit_webapp:## build local no docker
	streamlit run app_landing.py --server.port 9000

docker_run: docker_rm_container
	docker run -d --name langchain-streamlit-agent -p 8051:8051 langchain-streamlit-agent:latest

docker_build_streamlit_webapp: docker_rm_container ## Build Webapp Container
	docker run \
		-p 8051:8051 \
		-v $(shell pwd):/root/app/ \
		-w="/root/app/" \
		--name langchain-streamlit-agent-container \
		langchain-streamlit-agent:latest

local_app_test:## build local no docker
	streamlit run app_test.py --server.port 8888

fetch_snowflake_key:## Get RSA token for snowflake connection. Key is GitIgnored
	aws secretsmanager get-secret-value --secret-id prod-snowflake-prod-service-account | jq --raw-output '.SecretString' > .streamlit/rsa_key.p8

docker_destroy_image:
	-docker rmi langchain-streamlit-agent:latest

docker_rm_container: docker_stop_containers docker_rm_stopped_containers

docker_stop_containers:
	-docker stop $(shell docker ps -a --filter ancestor=langchain-streamlit-agent:latest --format="{{.ID}}")

docker_rm_stopped_containers:
	-docker rm $(shell docker ps -a -f status=exited -q)

docker_container_interactive_bash: ## Interactive Bash inside running container
	docker exec -it langchain-streamlit-agent-container /bin/bash

docker_container_inspect: ## Inspect Container
	docker container inspect langchain-streamlit-agent-container

docker_stats: ## Live stats for CPU and Memory Utilization
	docker stats

docker_running_logs: ## Live Logs from Container
	docker logs -f langchain-streamlit-agent-container

docker_full_prune: ## Purge all containers and images. WARNING: will apply to non-webapp docker resources
	-docker stop $(shell docker ps -a -q)
	-docker rm $(shell docker ps -a -q)
	-docker container prune -f
	-docker image prune -f

pipenv_install:
	-pipenv --rm; # Remove pipenv for this directory if exists
	-[ -e Pipfile.lock ] && rm Pipfile.lock; # Remove pipenv LockFiles for this directory if exists
	pipenv install;

pipenv_update_requirements_txt:
	pipenv --version;
	pipenv requirements > requirements.txt;

reset_pipenv_dependencies: pipenv_install pipenv_update_requirements_txt