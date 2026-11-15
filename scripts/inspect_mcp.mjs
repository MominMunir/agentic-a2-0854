// Drive the actual local MCP Inspector for repeatable contract screenshots.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
process.env.PLAYWRIGHT_BROWSERS_PATH=path.join(root,'.cache/playwright');
const {chromium}=await import('../apps/web/node_modules/playwright/index.mjs');
const log=fs.readFileSync(path.join(root,'.private/inspector.log'),'utf8').replace(/\x1b\[[0-9;]*m/g,'');
const address=log.match(/http:\/\/127\.0\.0\.1:6274[^\s]*/)?.[0];
if(!address) throw new Error('Start the official Inspector first; its private local URL is missing.');
const browser=await chromium.launch({headless:true});
const context=await browser.newContext({viewport:{width:1440,height:1050},storageState:fs.existsSync(path.join(root,'.private/inspector-state.json'))?path.join(root,'.private/inspector-state.json'):undefined});
const page=await context.newPage();
await page.goto(address,{waitUntil:'domcontentloaded'});
await page.waitForTimeout(1500);
if(process.argv[2]==='add' || process.argv[2]==='configure') {
  await page.getByRole('button',{name:'Add Servers',exact:true}).click();
  await page.getByText('+ Add manually',{exact:true}).click();
  if(process.argv[2]==='configure') {
    await page.getByPlaceholder('my-server').fill('gigbid-portfolio');
    await page.getByPlaceholder('npx').fill(path.join(root,'.venv/Scripts/python.exe'));
    await page.locator('textarea').nth(0).fill('-m\nmcp_servers.portfolio.server');
    const tenant=JSON.parse(fs.readFileSync(path.join(root,'.private/inspector-tenant.json'),'utf8')).tenant;
    await page.locator('textarea').nth(1).fill('MCP_STDIO_TENANT='+tenant);
    await page.getByPlaceholder('(inherit)').fill(root);
    await page.getByRole('button',{name:'Add',exact:true}).click();
    await page.getByLabel('Connect or disconnect "gigbid-portfolio"',{exact:true}).check();
    await page.waitForTimeout(2500);
  }
}
if(process.argv[2]==='connect') {
  await page.getByRole('switch',{name:'Connect or disconnect "gigbid-portfolio"',exact:true}).focus();
  await page.getByRole('switch',{name:'Connect or disconnect "gigbid-portfolio"',exact:true}).press('Space');
  await page.waitForTimeout(3000);
  await page.getByText('gigbid-portfolio',{exact:true}).first().click();
  await page.waitForTimeout(1500);
}
if(['tools','search','resources','prompts'].includes(process.argv[2])) {
  const toggle=page.getByRole('switch',{name:'Connect or disconnect "gigbid-portfolio"',exact:true});
  if(!await toggle.isChecked()) { await toggle.focus(); await toggle.press('Space'); await page.waitForTimeout(4500); }
  await page.getByText('gigbid-portfolio',{exact:true}).first().click();
  await page.getByText(process.argv[2]==='resources'?'Resources':process.argv[2]==='prompts'?'Prompts':'Tools',{exact:true}).first().click();
  await page.waitForTimeout(1000);
  if(process.argv[2]==='search') {
    await page.getByText('search_evidence',{exact:true}).first().click();
    if(process.argv.includes('--execute')) {
      await page.getByLabel(/^Requirement/).fill('Python classification');
      await page.getByLabel('K',{exact:true}).fill('5');
      await page.getByRole('button',{name:'Execute Tool',exact:true}).click();
      await page.waitForFunction(()=>document.body.innerText.includes('ml-project-'),{timeout:45000});
      await page.screenshot({path:path.join(root,'docs/images/mcp-inspector-search.png'),fullPage:true});
    }
  }
  if(process.argv[2]==='tools') await page.screenshot({path:path.join(root,'docs/images/mcp-inspector-tools.png'),fullPage:true});
  if(['resources','prompts'].includes(process.argv[2])) await page.screenshot({path:path.join(root,'docs/images/mcp-inspector-'+process.argv[2]+'.png'),fullPage:true});
}
console.log((await page.locator('body').innerText()).replace(/[A-Za-z0-9_-]{40,}/g,'[redacted]').slice(0,13000));
console.log(await page.locator('input').evaluateAll(nodes=>nodes.map(n=>({placeholder:n.placeholder,type:n.type,aria:n.getAttribute('aria-label')}))));
await context.storageState({path:path.join(root,'.private/inspector-state.json')});
await browser.close();
