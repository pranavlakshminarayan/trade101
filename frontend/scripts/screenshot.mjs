// Drive the real Trade101 frontend and screenshot the curtain, closed and open.
// Drive the running app and capture the screens. Requires both servers up:
//   backend:  .venv/Scripts/python.exe tools/stub_server.py     (from backend/)
//   frontend: npm run dev                                        (from frontend/)
// Then:       node scripts/screenshot.mjs
// Shots land in frontend/screenshots/ (override with SHOT_DIR).
import { mkdirSync } from 'node:fs'
import { chromium } from 'playwright'

const OUT = process.env.SHOT_DIR || 'screenshots'
const errors = []

mkdirSync(OUT, { recursive: true })

// executablePath is only needed where Chromium is pre-installed outside the
// npm cache (this container); locally, `npx playwright install chromium` first
// and Playwright finds it itself.
const browser = await chromium.launch({
  ...(process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {}),
  args: ['--no-sandbox'],
})
const page = await (await browser.newContext({ viewport: { width: 1440, height: 1000 } })).newPage()
page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()) })
page.on('pageerror', (e) => errors.push('PAGEERROR: ' + e.message))

const shot = async (name, opts = {}) => {
  await page.screenshot({ path: `${OUT}/${name}.png`, ...opts })
  console.log('shot:', name)
}

// 1. Welcome
await page.goto('http://127.0.0.1:5173', { waitUntil: 'networkidle' })
await page.waitForSelector('text=Which stock shall we study')
await shot('01-welcome')

// 2. Research page — the curtain should be CLOSED
await page.fill('input[placeholder="Search a company or ticker…"]', 'NVDA')
await page.press('input[placeholder="Search a company or ticker…"]', 'Enter')
await page.waitForSelector('text=AI momentum read', { timeout: 30000 })
await page.waitForSelector('text=hidden for now', { timeout: 30000 })
await page.waitForTimeout(2500) // let the chart + lenses + fundamentals settle

// Prove the leaks are closed, in the live DOM.
const closed = await page.evaluate(() => {
  const strip = document.querySelector('.strip')
  const body = document.body.innerText
  return {
    leanChipInStrip: !!strip?.querySelector('.chip.up, .chip.down'),
    summaryVisible: body.includes('holding above both moving averages'),
    curtainVisible: body.includes('nothing is being withheld from you'),
    newsTabOnFeed: document.querySelector('.ntab.on')?.innerText?.trim(),
    asOfVisible: body.includes('as of'),
    coverageVisible: body.includes('Sourced'),
  }
})
console.log('CURTAIN CLOSED →', JSON.stringify(closed, null, 2))
await shot('02-curtain-closed', { fullPage: true })
await page.locator('.card', { hasText: 'AI momentum read' }).first().screenshot({
  path: `${OUT}/03-curtain-panel.png`,
})

// 3. Reveal
await page.click('button:has-text("Reveal Trade101\'s read")')
await page.waitForSelector('text=it is not advice', { timeout: 15000 })
await page.waitForTimeout(1200)
const revealed = await page.evaluate(() => {
  const strip = document.querySelector('.strip')
  const body = document.body.innerText
  return {
    leanChipInStrip: !!strip?.querySelector('.chip.up, .chip.down'),
    summaryVisible: body.includes('holding above both moving averages'),
    withheldVisible: body.includes('withheld'),
    citationChips: document.querySelectorAll('.cite').length,
  }
})
console.log('REVEALED →', JSON.stringify(revealed, null, 2))
await shot('04-revealed', { fullPage: true })
await page.locator('.card', { hasText: 'AI momentum read' }).first().screenshot({
  path: `${OUT}/05-revealed-panel.png`,
})

// 4. The news panel's inference tab (the second leak)
await page.click('button.ntab:has-text("What it means")')
await page.waitForTimeout(600)
await page.locator('.card', { hasText: 'News & financial signals' }).first().screenshot({
  path: `${OUT}/06-news-inference.png`,
})

// 5. Style lenses — expand mean-reversion, which argues against itself
await page.locator('button.lens-head:has-text("Mean reversion")').click()
await page.waitForTimeout(500)
await page.locator('.card', { hasText: 'Style lenses' }).first().screenshot({
  path: `${OUT}/07-lenses.png`,
})

// 6. Guided Study
await page.click('button:has-text("Study this chart")')
await page.waitForSelector('text=Guided study')
await page.waitForTimeout(600)
await shot('08-study-observe')

// 7. Light mode, back on the research page
await page.keyboard.press('Escape')
await page.click('.modal-bg', { position: { x: 5, y: 5 } }).catch(() => {})
await page.waitForTimeout(400)
await page.click('button.themebtn')
await page.waitForTimeout(700)
await shot('09-light-mode', { fullPage: true })

console.log('\nCONSOLE ERRORS:', errors.length ? errors : 'none')
await browser.close()
