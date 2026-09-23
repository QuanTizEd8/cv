.PHONY: all academic industry targeted visual visual-even visual-kendall clean

# Build all standard variants (Typst pipeline + HTML themes)
all: academic industry targeted visual

academic:
	python scripts/build.py academic-cv

industry:
	python scripts/build.py industry-resume

targeted:
	python scripts/build.py targeted-example

# Add a new target for each targeted application, e.g.:
#   targeted-acme:
#	    python scripts/build.py targeted-acme-corp

# HTML theme pipeline — resumed + npm JSON Resume themes
# To add a new theme: npm install --save-dev jsonresume-theme-<name>
# then add a target below and register it in visual:
visual: visual-even visual-kendall

visual-even:
	mkdir -p output
	npx resumed render content/resume.json --theme jsonresume-theme-even --output output/visual-even.html
	@echo "  HTML: output/visual-even.html"
	node scripts/html-to-pdf.js output/visual-even.html output/visual-even.pdf A4

visual-kendall:
	mkdir -p output
	npx resumed render content/resume.json --theme jsonresume-theme-kendall --output output/visual-kendall.html
	@echo "  HTML: output/visual-kendall.html"
	node scripts/html-to-pdf.js output/visual-kendall.html output/visual-kendall.pdf A4

clean:
	rm -rf output/
