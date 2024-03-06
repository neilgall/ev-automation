requirements: requirements.txt
	pip-sync requirements.txt

requirements.txt: requirements.in
	pip-compile --upgrade $<

start:
	python main.py

docker:
	docker build -t ev-automation .
