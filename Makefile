requirements: requirements.txt
	pip-sync requirements.txt

requirements.txt: requirements.in
	pip-compile --upgrade $<

.PHONY: start
start:
	python main.py

.PHONY: docker
docker:
	docker build -t ev-automation .

.PHONY: lambda
lambda:
	(cd lambda && make)
