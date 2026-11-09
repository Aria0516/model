// Render a generated figure HTML to PNG (2x) and PDF with Playwright.
// Usage: node render_fig.js fig_model_evolution 1940 1190
//        node render_fig.js fig_model_mechanism 1940 1200
const path = require('path');
const { chromium } = require('playwright');
const [name, w, h] = process.argv.slice(2);
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: +w, height: +h }, deviceScaleFactor: 2 });
  const base = path.join(__dirname, name);
  await p.goto('file://' + base + '.html');
  await p.screenshot({ path: base + '.png' });
  await p.pdf({ path: base + '.pdf', width: w + 'px', height: h + 'px', printBackground: true });
  await b.close();
})();
