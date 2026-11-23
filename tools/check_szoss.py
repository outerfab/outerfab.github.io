"""Local browser regression checks; all form requests are intercepted.

Install Playwright in a temporary environment, serve website/dist on port 8767,
and build with SZOSS_FORMSPARK_FORM_ID=szoss-local-test before running.
Rebuild without that override after testing. No real registrations are sent.
"""
import asyncio,json
from pathlib import Path
from playwright.async_api import async_playwright
URL='http://127.0.0.1:8767/events/szoss/'
async def main():
 async with async_playwright() as p:
  browser=await p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
  page=await browser.new_page(viewport={'width':1280,'height':900})
  errors=[]; page.on('pageerror',lambda e:errors.append(str(e)))
  async def fill():
   await page.locator('[name=name]').fill('Local browser test')
   await page.locator('[name=email]').fill('local-test@example.invalid')
   await page.locator('[name=project]').fill('Synthetic browser verification, intercepted locally.')
  for width in [360,390,768,1280]:
   await page.set_viewport_size({'width':width,'height':900});await page.goto(URL);await page.evaluate('document.fonts.ready')
   assert await page.evaluate('document.documentElement.scrollWidth <= innerWidth'),f'overflow {width}'
   for img in await page.locator('img').all():
    await img.scroll_into_view_if_needed();await img.evaluate('(i)=>i.loading="eager"')
   await page.wait_for_function('Array.from(document.images).every(i => i.complete && i.naturalWidth > 0)')
   await page.evaluate('scrollTo(0,0)');await page.screenshot(path=f'/tmp/szoss-{width}-full.png',full_page=True)
  await page.goto(URL)
  assert not await page.locator('form').evaluate('(f)=>f.checkValidity()')
  requests=[]
  async def success(route):
   data=route.request.post_data_json; requests.append(data)
   assert '_redirect' not in data and '_error' not in data
   await asyncio.sleep(.15)
   await route.fulfill(status=200,content_type='application/json',body=json.dumps(data))
  await page.route('https://submit-form.com/**',success)
  await fill();await page.locator('button[type=submit]').click();await page.locator('form').evaluate('(f)=>f.requestSubmit()');await page.wait_for_selector('#registration-status h3')
  assert await page.locator('form').is_hidden()
  assert 'directions and further details' in await page.locator('#registration-status').inner_text()
  assert len(requests)==1 and requests[0]['event_id']=='szoss-2026-11-11'
  await page.unroute('https://submit-form.com/**')
  await page.goto(URL);await fill()
  async def fail(route):await route.fulfill(status=402,body='Out of submissions')
  await page.route('https://submit-form.com/**',fail)
  await page.locator('button[type=submit]').click();await page.wait_for_function('document.querySelector("#registration-status").textContent.includes("could not confirm")')
  assert await page.locator('[name=project]').input_value()=='Synthetic browser verification, intercepted locally.'
  assert await page.locator('button[type=submit]').is_enabled()
  await page.unroute('https://submit-form.com/**')
  await page.goto(URL);await fill()
  async def malformed(route):await route.fulfill(status=200,content_type='application/json',body='{}')
  await page.route('https://submit-form.com/**',malformed)
  await page.locator('button[type=submit]').click();await page.wait_for_function('document.querySelector("#registration-status").textContent.includes("could not confirm")')
  assert await page.locator('form').is_visible()
  assert not errors,errors
  await browser.close()
 print('PASS: 360/390/768/1280 widths, all portraits loaded, validation, accepted receipt, rejected response, malformed response, retained answers; zero live submissions.')
asyncio.run(main())
