import {chromium} from 'playwright'
import {mkdir} from 'node:fs/promises'
const browser=await chromium.launch({headless:true})
const page=await browser.newPage({viewport:{width:1440,height:1080}})
await page.goto('http://127.0.0.1:5173/',{waitUntil:'networkidle'})
await mkdir('../reports',{recursive:true})
await page.screenshot({path:'../reports/ui_desktop.png',fullPage:true})
await page.setViewportSize({width:390,height:844})
await page.screenshot({path:'../reports/ui_mobile.png',fullPage:true})
console.log('Capturas del prototipo local guardadas')
await browser.close()
