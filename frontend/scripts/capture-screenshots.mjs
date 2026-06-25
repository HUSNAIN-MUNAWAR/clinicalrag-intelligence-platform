import path from 'node:path';
import { fileURLToPath } from 'node:url';
import puppeteer from 'puppeteer-core';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(__dirname, '..', '..');
const screenshotDir = path.join(root, 'docs', 'screenshots');
const chromePath = process.env.CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const baseUrl = process.env.APP_URL || 'http://127.0.0.1:3000';

const browser = await puppeteer.launch({
  executablePath: chromePath,
  headless: true,
  defaultViewport: { width: 1440, height: 1100, deviceScaleFactor: 1 },
  args: ['--no-sandbox', '--disable-setuid-sandbox'],
});

async function capture(page, route, fileName) {
  await page.goto(`${baseUrl}${route}`, { waitUntil: 'networkidle0', timeout: 60000 });
  await page.screenshot({ path: path.join(screenshotDir, fileName), fullPage: true });
}

try {
  const page = await browser.newPage();
  await capture(page, '/', 'overview.png');

  await page.goto(`${baseUrl}/playground`, { waitUntil: 'networkidle0', timeout: 60000 });
  await page.click('textarea');
  await page.keyboard.down('Control');
  await page.keyboard.press('KeyA');
  await page.keyboard.up('Control');
  await page.keyboard.type('What warning signs are mentioned for asthma?');
  await page.click('button');
  await page.waitForFunction(() => document.body.innerText.includes('Citations'), { timeout: 60000 });
  await page.screenshot({ path: path.join(screenshotDir, 'rag-playground.png'), fullPage: true });

  await page.goto(`${baseUrl}/comparison`, { waitUntil: 'networkidle0', timeout: 60000 });
  await page.click('button');
  await page.waitForFunction(() => document.body.innerText.includes('risk'), { timeout: 60000 });
  await page.screenshot({ path: path.join(screenshotDir, 'comparison-lab.png'), fullPage: true });

  await capture(page, '/evaluation', 'evaluation-lab.png');
  await capture(page, '/safety', 'safety-center.png');
} finally {
  await browser.close();
}
