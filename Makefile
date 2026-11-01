.PHONY: data analysis charts test all
data:
	python src/generate_data.py --out data/raw
analysis:
	python src/run_analysis.py
charts:
	python src/make_charts.py
test:
	pytest -q
all: data analysis charts test
