all: build

.PHONY: test

build: .build

.build: requirements.txt
	pip install -r requirements.txt
	touch .build

test: alphabot
	nosetests alphabot
	pyflakes alphabot
	pep8 --max-line-length=100 alphabot
