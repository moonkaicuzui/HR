const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  // Capture console messages
  const consoleMessages = [];
  page.on('console', msg => {
    const text = msg.text();
    consoleMessages.push(`[${msg.type()}] ${text}`);
    console.log(`🖥️  Console [${msg.type()}]:`, text);
  });

  // Navigate to the latest dashboard
  await page.goto('file:///Users/ksmoon/Coding/HR/output_files/HR_Dashboard_Complete_2025_10.html', { timeout: 60000 });
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(2000);

  // Call showModal1() function directly
  await page.evaluate(() => showModal1());
  await page.waitForTimeout(2000);

  // Check if modal is visible
  const modalVisible = await page.isVisible('#modal1');
  console.log(`✅ Modal visible: ${modalVisible}`);

  // Check if both canvases exist
  const monthlyCanvasExists = await page.isVisible('#modalChart1_monthly');
  const weeklyCanvasExists = await page.isVisible('#modalChart1_weekly');
  console.log(`✅ Monthly canvas exists: ${monthlyCanvasExists}`);
  console.log(`✅ Weekly canvas exists: ${weeklyCanvasExists}`);

  // Check canvas sizes
  const canvasSizes = await page.evaluate(() => {
    const monthlyCanvas = document.getElementById('modalChart1_monthly');
    const weeklyCanvas = document.getElementById('modalChart1_weekly');
    return {
      monthly: monthlyCanvas ? { width: monthlyCanvas.width, height: monthlyCanvas.height } : null,
      weekly: weeklyCanvas ? { width: weeklyCanvas.width, height: weeklyCanvas.height } : null
    };
  });
  console.log(`✅ Monthly canvas size:`, canvasSizes.monthly);
  console.log(`✅ Weekly canvas size:`, canvasSizes.weekly);

  // Get console logs to check for errors
  const consoleLogs = await page.evaluate(() => {
    return window.consoleMessages || [];
  });
  console.log('📋 Console logs:', consoleLogs);

  // Check if Chart.js charts exist
  const chartsExist = await page.evaluate(() => {
    const monthlyCanvas = document.getElementById('modalChart1_monthly');
    const weeklyCanvas = document.getElementById('modalChart1_weekly');
    return {
      monthly: monthlyCanvas && window.Chart && window.Chart.getChart(monthlyCanvas) !== undefined,
      weekly: weeklyCanvas && window.Chart && window.Chart.getChart(weeklyCanvas) !== undefined
    };
  });
  console.log(`✅ Monthly chart exists: ${chartsExist.monthly}`);
  console.log(`✅ Weekly chart exists: ${chartsExist.weekly}`);

  // Get chart data
  const chartsData = await page.evaluate(() => {
    const monthlyCanvas = document.getElementById('modalChart1_monthly');
    const weeklyCanvas = document.getElementById('modalChart1_weekly');

    const monthlyChart = window.Chart && window.Chart.getChart(monthlyCanvas);
    const weeklyChart = window.Chart && window.Chart.getChart(weeklyCanvas);

    return {
      monthly: monthlyChart ? {
        labels: monthlyChart.data.labels,
        datasetLength: monthlyChart.data.datasets.length,
        firstDataset: monthlyChart.data.datasets[0] ? {
          label: monthlyChart.data.datasets[0].label,
          dataLength: monthlyChart.data.datasets[0].data.length
        } : null
      } : null,
      weekly: weeklyChart ? {
        labels: weeklyChart.data.labels,
        datasetLength: weeklyChart.data.datasets.length,
        firstDataset: weeklyChart.data.datasets[0] ? {
          label: weeklyChart.data.datasets[0].label,
          dataLength: weeklyChart.data.datasets[0].data.length
        } : null
      } : null
    };
  });
  console.log(`✅ Monthly chart data:`, JSON.stringify(chartsData.monthly, null, 2));
  console.log(`✅ Weekly chart data:`, JSON.stringify(chartsData.weekly, null, 2));

  // Take screenshot
  await page.screenshot({ path: '/Users/ksmoon/Coding/HR/modal_chart_test.png', fullPage: true });
  console.log('✅ Screenshot saved: modal_chart_test.png');

  // Wait before closing
  await page.waitForTimeout(3000);

  await browser.close();
})();
