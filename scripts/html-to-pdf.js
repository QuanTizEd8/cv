#!/usr/bin/env node
// Convert a local HTML file to PDF using headless Chromium via Puppeteer.
// Usage: node scripts/html-to-pdf.js <input.html> <output.pdf> [a4|letter]

const puppeteer = require('puppeteer');
const path = require('path');

const [, , htmlFile, pdfFile, pageFormat = 'A4'] = process.argv;

if (!htmlFile || !pdfFile) {
  console.error('Usage: node scripts/html-to-pdf.js <input.html> <output.pdf> [A4|Letter]');
  process.exit(1);
}

(async () => {
  const browser = await puppeteer.launch({
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });
  const page = await browser.newPage();

  // Match viewport width to the page format so layout doesn't reflow.
  // A4: 210mm = 794px at 96dpi. Letter: 8.5in = 816px at 96dpi.
  const viewportWidth = pageFormat.toLowerCase() === 'letter' ? 816 : 794;
  await page.setViewport({ width: viewportWidth, height: 1123, deviceScaleFactor: 1 });

  await page.goto(`file://${path.resolve(htmlFile)}`, { waitUntil: 'networkidle0' });
  await page.pdf({
    path: pdfFile,
    format: pageFormat,
    printBackground: true,
    preferCSSPageSize: true,  // honour @page rules declared by the theme
  });
  await browser.close();
  console.log(`  PDF:  ${pdfFile}`);
})();
