# LD80 metadata, derived from a LakeDistrictCorpus checkout sitting
# alongside this repo. Override if yours lives elsewhere:
#   make get CORPUS=/path/to/LakeDistrictCorpus
CORPUS ?= ../../../../LakeDistrictCorpus
SOURCE := $(CORPUS)/LD80_metadata/LD80_metadata.csv

convert: get
	python -c "import csv,json; print('\n'.join(json.dumps(r) for r in csv.DictReader(open('ld80-metadata.csv'))))" > ld80-metadata.jsonl

get:
	ghead -n -9 $(SOURCE) > ld80-metadata.csv
