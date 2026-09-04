const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { createRequire } = require("node:module");
const runtimeRequire = process.env.PLAYWRIGHT_MODULE_ROOT
  ? createRequire(path.join(process.env.PLAYWRIGHT_MODULE_ROOT, "package.json"))
  : require;
const { chromium } = runtimeRequire("playwright");

const recurring = {
  id: "recurring", title: "SUP-тур на Азатское водохранилище",
  recurring_schedule: "ЕЖЕДНЕВНО:\n1 ГРУППА: 09:00 – 15:00\n2 ГРУППА: 16:00 – 22:00",
  display_until: "2026-09-06", venue_name: "ЖД вокзал", category: "tourism",
  price_text: "Будни — 14 000 AMD; выходные — 18 000 AMD",
  date_start: null, date_end: null,
};
const fixtures = [
  recurring,
  { id: "concert", title: "Джазовый концерт", date_start: "2026-09-07", venue_name: "Клуб", category: "concert" },
  { ...recurring, id: "expired", title: "Старый анонс", display_until: "2026-08-30" },
  { id: "unknown", title: "Без даты", venue_name: "Клуб" },
];

(async () => {
  const browser = await chromium.launch({ headless: true, channel: process.env.PLAYWRIGHT_CHANNEL || "chrome" });
  try {
    for (const viewport of [{ width: 375, height: 812 }, { width: 1280, height: 900 }]) {
      const page = await browser.newPage({ viewport, timezoneId: "America/Los_Angeles" });
      await page.clock.install({ time: new Date("2026-09-06T19:59:00Z") });
      const errors = [];
      page.on("pageerror", (error) => errors.push(error.message));
      const html = fs.readFileSync(path.join(__dirname, "index.html"), "utf8")
        .replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, "")
        .replace(/<link\b[^>]*>/gi, "");
      await page.setContent(html);
      await page.addStyleTag({ path: path.join(__dirname, "styles.css") });
      await page.evaluate((events) => {
        window.YEREVAN_EVENTS_CONFIG = { supabaseUrl: "", supabaseAnonKey: "" };
        window.supabase = { createClient: () => ({ from: () => ({ select: () => ({
          order: async () => ({ data: events, error: null }),
        }) }) }) };
      }, fixtures);
      await page.addScriptTag({ path: path.join(__dirname, "app.js") });
      await page.locator(".event-card").first().waitFor();
      assert.equal(await page.locator(".event-card").count(), 2);
      assert.equal(await page.getByText("На этой неделе", { exact: true }).count(), 1);
      assert.equal(await page.locator(".event-card").filter({ hasText: "SUP-тур" }).count(), 1);
      assert.match(await page.locator("#events-list").innerText(), /16:00/);
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
      const filename = path.join(os.tmpdir(), `yerevan-recurring-${viewport.width}.png`);
      await page.screenshot({ path: filename, fullPage: true });
      console.log(filename);
      await page.locator("#date-input").fill("2026-09-07");
      assert.equal(await page.locator(".event-card").count(), 1);
      assert.match(await page.locator("#events-list").innerText(), /Джазовый/);
      await page.locator("#reset-button").click();
      assert.equal(await page.locator(".event-card").count(), 2);
      await page.clock.fastForward(120000);
      assert.equal(await page.locator(".event-card").count(), 1);
      assert.doesNotMatch(await page.locator("#events-list").innerText(), /SUP-тур/);
      assert.deepEqual(errors, []);
      await page.close();
    }
    console.log("Recurring cards, date filters, midnight expiry and mobile layout: OK");
  } finally {
    await browser.close();
  }
})().catch((error) => { console.error(error); process.exitCode = 1; });
