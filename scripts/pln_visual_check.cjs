// QA de lectura: no crea casos ni guarda aclaraciones/relaciones.
const {chromium}=require('../frontend/node_modules/playwright');
const fs=require('fs');
const path=require('path');
(async()=>{
 const root=path.resolve(__dirname,'..');
 const browser=await chromium.launch({headless:true});
 const context=await browser.newContext({baseURL:'http://127.0.0.1:5173',viewport:{width:1360,height:900}});
 const page=await context.newPage();
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 try{
  await page.goto('/pln');
  await page.getByRole('button',{name:'Analizar',exact:true}).click();
  await page.locator('[data-stage="tfidf"]').waitFor();
  await page.screenshot({path:path.join(root,'reports/pln_desktop.png')});
  await page.locator('[data-stage="tfidf"]').scrollIntoViewIfNeeded();
  await page.screenshot({path:path.join(root,'reports/pln_tfidf.png')});
  await page.setViewportSize({width:390,height:844});
  await page.screenshot({path:path.join(root,'reports/pln_mobile.png')});
  if(await page.evaluate(()=>document.documentElement.scrollWidth>window.innerWidth))throw new Error('Overflow móvil');
  const env=fs.readFileSync(path.join(root,'.env'),'utf8');
  const secret=(env.match(/^DEMO_ADMIN_PASSWORD=(.*)$/m)||[])[1]?.trim().replace(/^"|"$/g,'');
  if(!secret)throw new Error('Credencial de demo ausente');
  const login=await context.request.post('/api/v1/auth/login',{data:{usuario:'admin-demo',password:secret}});
  if(!login.ok())throw new Error('Login de QA no disponible');
  await page.setViewportSize({width:1360,height:900});
  await page.goto('/admin/pln/datos');
  await page.getByText('Procedencia y particiones',{exact:true}).waitFor();
  await page.screenshot({path:path.join(root,'reports/pln_datos.png')});
  await page.getByLabel('Experimento a consultar').selectOption('pln-expanded-demo-20261014');
  await page.getByText('Modelo: pln-expanded-demo-20261014. Corpus: disponible.',{exact:true}).waitFor();
  await page.getByText('Entrenamiento y comparación de desarrollo',{exact:true}).scrollIntoViewIfNeeded();
  await page.screenshot({path:path.join(root,'reports/pln_candidato.png')});
  await page.goto('/pln/mejoras');
  await page.getByRole('heading',{name:'A. Corpus local'}).waitFor();
  await page.screenshot({path:path.join(root,'reports/pln_mejoras.png')});
  if(errors.length)throw new Error(errors.join('; '));
  console.log('QA visual: seis capturas, sin errores JS ni overflow móvil; candidato consultado sin activación.');
 }finally{await browser.close()}
})().catch(e=>{console.error(e.message);process.exit(1)});
