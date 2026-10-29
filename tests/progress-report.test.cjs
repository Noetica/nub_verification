// Local report only: all HTTP(S) requests are blocked; no tenant or Azure calls.
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const { execFileSync } = require('node:child_process');
const { pathToFileURL } = require('node:url');

const root = path.resolve(__dirname, '..');
const packageFlag = process.argv.indexOf('--playwright-package');
const packageName = packageFlag < 0 ? 'playwright' : path.resolve(process.argv[packageFlag + 1]);
const { chromium } = require(packageName);
const output = path.join(root, 'results', 'pr2-feedback-16072ed');
const evidenceFile = path.join(output, 'validation.json');
const relative = value => path.relative(root, value).split(path.sep).join('/');
const digest = value => crypto.createHash('sha256').update(fs.readFileSync(value)).digest('hex');
const result = {
  scope: 'Standalone report validation; no live tenant tests',
  base_commit: execFileSync('git', ['rev-parse', 'HEAD'], { cwd: root, encoding: 'utf8' }).trim(),
  working_tree_modified: Boolean(execFileSync('git', ['status', '--porcelain'], { cwd: root, encoding: 'utf8' }).trim()),
  node_version: process.version,
  status: 'RUNNING',
  checks: [],
  screenshots: [],
};
fs.mkdirSync(output, { recursive: true });
const save = () => fs.writeFileSync(evidenceFile, JSON.stringify(result, null, 2) + '\n');
save();

(async () => {
  let browser;
  try {
    const data = JSON.parse(fs.readFileSync(path.join(root, 'consolidation-status.json'), 'utf8'));
    browser = await chromium.launch({ headless: true });
    result.browser_version = browser.version();
    const page = await browser.newPage({ viewport: { width: 1280, height: 920 } });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.route(/^https?:\/\//, route => route.abort());
    await page.goto(pathToFileURL(path.join(root, 'progress-summary.html')).href);
    for (const status of ['all', 'done', 'in_progress', 'todo', 'blocked', 'deferred']) {
      await page.selectOption('#status-filter', status);
      const expected = status === 'all' ? data.planned_points.length : data.planned_points.filter(p => p.status === status).length;
      assert.equal(await page.locator('#points .point:visible').count(), expected, status);
    }
    result.checks.push('All six status filters match the JSON planned-point counts');
    await page.selectOption('#status-filter', 'all');
    const agent = JSON.parse(await page.locator('#agent-state').textContent());
    assert.deepEqual(agent.planned_points, data.planned_points);
    assert.deepEqual(agent.resume, data.agent_handover);
    await page.locator('#copy-handover').evaluate(element => { element.closest('details').open = true; });
    await page.evaluate(() => Object.defineProperty(navigator, 'clipboard', {
      configurable: true, value: { writeText: async text => { window.copiedReportText = text; } },
    }));
    await page.click('#copy-handover');
    assert.deepEqual(JSON.parse(await page.evaluate(() => window.copiedReportText)), agent);
    assert.match(await page.locator('#copy-status').textContent(), /copied/);
    await page.evaluate(() => Object.defineProperty(navigator, 'clipboard', {
      configurable: true, value: { writeText: async () => { throw new Error('mock clipboard denial'); } },
    }));
    await page.click('#copy-handover');
    assert.match(await page.locator('#copy-status').textContent(), /Clipboard unavailable/);
    result.checks.push('Handover JSON fidelity and clipboard success/denial paths');

    for (const viewport of [{ width: 1280, height: 920, name: 'desktop' }, { width: 390, height: 844, name: 'mobile' }]) {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      await page.evaluate(() => window.scrollTo(0, 0));
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false, viewport.name + ' overflow');
      const file = path.join(output, 'report-' + viewport.name + '.png');
      await page.screenshot({ path: file });
      result.screenshots.push({ path: relative(file), width: viewport.width, height: viewport.height });
    }
    result.checks.push('Desktop/mobile viewport layout without horizontal overflow');
    for (const target of await page.locator('a[href]').evaluateAll(links => links.map(a => a.getAttribute('href')))) {
      if (/^https?:\/\//.test(target)) continue;
      if (target.startsWith('#')) assert(await page.locator(target).count(), 'missing anchor ' + target);
      else assert(fs.existsSync(path.resolve(root, target.split('#')[0])), 'missing local file ' + target);
    }
    assert.deepEqual(errors, []);
    result.checks.push('Local evidence links/anchors exist; no browser script errors');
    result.source_sha256 = {};
    for (const name of ['consolidation-status.json', 'progress-summary.html', 'scripts/render-progress.py', 'tests/progress-report.test.cjs', 'tests/test_render_progress.py']) {
      result.source_sha256[name] = digest(path.join(root, name));
    }
    result.status = 'PASS';
    console.log('PASS: report filters, handover/clipboard, local links, desktop/mobile layout and no script errors');
  } catch (error) {
    result.status = 'FAIL';
    result.error = error.message;
    process.exitCode = 1;
    console.error(error.message);
  } finally {
    if (browser) await browser.close();
    result.completed_at_utc = new Date().toISOString();
    save();
  }
})();
