
convert: get
	python -c "import csv,json; print('\n'.join(json.dumps(r) for r in csv.DictReader(open('ld80-metadata.csv'))))" > ld80-metadata.jsonl

get:
	ghead -n -9 ~/git/LakeDistrictCorpus/LD80_metadata/LD80_metadata.csv > ld80-metadata.csv


