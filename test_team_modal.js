const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  await page.goto('file:///Users/ksmoon/Downloads/대시보드 인센티브 테스트12_1_9월 25일 _맥북용/HR/output_files/HR_Dashboard_Complete_2025_10.html');
  await page.waitForTimeout(1000);
  
  // Click total employees KPI
  await page.click('.kpi-card:has-text("총 재직자 수")');
  await page.waitForTimeout(1000);
  
  // Click ASSEMBLY team
  await page.click('a:has-text("ASSEMBLY")');
  await page.waitForTimeout(2000);
  
  // Check if table has rows
  const rowCount = await page.locator('#teamDetailMembersTable tbody tr').count();
  console.log(`✅ Table has ${rowCount} rows`);
  
  // Take screenshot
  await page.screenshot({ path: '.playwright-mcp/team_modal_final.png', fullPage: true });
  
  await browser.close();
})();
