install:
	poetry install

search: search.py
	poetry run python ./search.py

organize: organize.py
	poetry run python ./organize.py --all
