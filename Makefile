all: build

build: .build

.build:
	pip install -r requirements.txt
	touch .build
