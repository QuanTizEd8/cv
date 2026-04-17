.PHONY: all academic industry targeted clean

# Build all standard variants
all: academic industry targeted

academic:
	python scripts/build.py academic-cv

industry:
	python scripts/build.py industry-resume

targeted:
	python scripts/build.py targeted-example

# Add a new target for each targeted application, e.g.:
#   targeted-acme:
#	    python scripts/build.py targeted-acme-corp

clean:
	rm -rf output/
