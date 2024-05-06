OUTPUT_DIR=output

all: install run

install: venv
	. venv/bin/activate && ( \
			pip install -r requirements.txt; \
			pre-commit install; \
			nvm use 20; \
			npm run build \
		)

venv:
	test -d venv || python3 -m venv venv

run:
	. venv/bin/activate && ( \
		python main.py --output-dir ${OUTPUT_DIR} \
	)

fetch-latest:
	. venv/bin/activate && ( \
		python main.py --year 2024 --fetch --output-dir ${OUTPUT_DIR}; \
		python main.py --output-dir ${OUTPUT_DIR} \
	)

fetch-all:
	. venv/bin/activate && ( \
		python main.py --year 2016 --fetch --output-dir ${OUTPUT_DIR}; \
		python main.py --year 2017 --fetch --output-dir ${OUTPUT_DIR}; \
		python main.py --year 2018 --fetch --output-dir ${OUTPUT_DIR}; \
		python main.py --year 2019 --fetch --output-dir ${OUTPUT_DIR}; \
		python main.py --year 2020 --fetch --output-dir ${OUTPUT_DIR}; \
		python main.py --year 2021 --fetch --output-dir ${OUTPUT_DIR}; \
		python main.py --year 2022 --fetch --output-dir ${OUTPUT_DIR}; \
		python main.py --year 2023 --fetch --output-dir ${OUTPUT_DIR}; \
		python main.py --year 2024 --fetch --output-dir ${OUTPUT_DIR}; \
		python main.py --output-dir ${OUTPUT_DIR} \
	)

serve:
	. venv/bin/activate && python -m http.server

test:
	. venv/bin/activate && python tests.py

clean:
	rm -rfv venv
	rm -rfv ${OUTPUT_DIR}
