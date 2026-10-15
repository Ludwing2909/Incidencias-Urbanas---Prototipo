import {test,expect} from '@playwright/test'

test('prioridad alta/media/baja y encabezado sin textos retirados',async({page})=>{
  await page.goto('/pln')
  await expect(page.locator('.academic')).toHaveCount(0)
  await expect(page.locator('.brand')).not.toContainText('Laboratorio PLN')
  for(const [message,level] of [['Hay un incendio junto al mercado.','alta'],['La luminaria del barrio no enciende desde ayer.','media'],['Sugiero pintar las bancas del parque.','baja']]){
    await page.getByLabel('Ejemplo editable y anonimizado').fill(message)
    await page.getByRole('button',{name:'Analizar',exact:true}).click()
    await expect(page.getByText(`Prioridad ${level}`,{exact:true})).toBeVisible()
  }
})

async function login(page:import('@playwright/test').Page){await page.goto('/personal');await page.getByLabel('Usuario',{exact:true}).fill('test-admin');await page.getByLabel('Contraseña',{exact:true}).fill('Test-password-123!');await page.getByRole('button',{name:'Iniciar sesión'}).click();await expect(page.getByRole('heading',{name:'Resumen de incidencias'})).toBeVisible()}

test('traza real y simulación pública sin registro, con diseño móvil',async({page})=>{
  await page.goto('/pln')
  await expect(page.getByRole('heading',{name:'Proceso de PLN',exact:true})).toBeVisible()
  await page.getByLabel('Ejemplo editable y anonimizado').fill('La luminaria del barrio no enciende desde ayer.')
  const analysis=page.waitForResponse(r=>r.url().endsWith('/pln/analizar')&&r.request().method()==='POST')
  await page.getByRole('button',{name:'Analizar',exact:true}).click()
  const response=await (await analysis).json()
  await expect(page.getByRole('status')).toContainText('No se ha creado una incidencia')
  await expect(page.locator('[data-stage="clasificacion"]')).toContainText('LinearSVC')
  await expect(page.locator('[data-stage="tfidf"] table').first()).toBeVisible()
  const member=response.etapas.find((s:{id:string})=>s.id==='tfidf').salida.miembros[0]
  await expect(page.locator('[data-stage="tfidf"] table').first()).toContainText(member.pesos[0].peso.toFixed(4))
  await expect(page.getByText('Área responsable pendiente de confirmación',{exact:true}).first()).toBeVisible()
  await expect(page.locator('[data-stage="lematizacion"]')).toContainText('no implementada')
  await page.setViewportSize({width:390,height:844})
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBeTruthy()
  await page.getByLabel('Ejemplo editable y anonimizado').fill('xyzzy qqqq zzzzzz')
  await page.getByRole('button',{name:'Analizar',exact:true}).click()
  await expect(page.locator('[data-stage="tfidf"]').getByText(/El vector está vacío/).first()).toBeVisible()
})

test('auditoría protegida, cohortes separadas y tablero A–L',async({page})=>{
  await page.goto('/admin/pln/datos')
  await expect(page).toHaveURL(/\/personal$/)
  await page.getByLabel('Usuario',{exact:true}).fill('test-admin')
  await page.getByLabel('Contraseña',{exact:true}).fill('Test-password-123!')
  await page.getByRole('button',{name:'Iniciar sesión'}).click()
  await expect(page.getByRole('heading',{name:'Datos y entrenamiento',exact:true})).toBeVisible()
  await expect(page.getByRole('heading',{name:'test · No evaluado'})).toBeVisible()
  await expect(page.getByRole('heading',{name:'functional · Evaluado'})).toBeVisible()
  await expect(page.getByRole('heading',{name:'challenge · Evaluado'})).toBeVisible()
  await page.goto('/pln/mejoras')
  await expect(page.locator('.improvement-grid .card')).toHaveCount(12)
  await expect(page.getByRole('heading',{name:'A. Corpus local'})).toBeVisible()
  await expect(page.getByRole('heading',{name:'L. Operación PostgreSQL'})).toBeVisible()
})

test('aclaraciones versionadas del personal conservan original y revisión',async({page})=>{
  await login(page)
  const response=await page.request.post('/api/v1/incidencias',{data:{descripcion:'Hay basura acumulada en la vía pública.'},headers:{'Idempotency-Key':crypto.randomUUID()}})
  expect(response.status()).toBe(201)
  const incident=await response.json()
  await page.goto(`/admin/incidencias/${incident.id}`)
  await page.getByRole('button',{name:'Analizar este caso y guardar versión'}).click()
  await expect(page.getByText(/Versión de análisis 1/)).toBeVisible()
  await page.getByLabel('¿En qué barrio o sector ocurre, sin dirección exacta?').fill('barrio Central')
  await page.getByLabel('¿Desde cuándo ocurre o cuándo lo observaste?').fill('desde ayer')
  await page.getByRole('button',{name:'Guardar aclaraciones y nueva versión'}).click()
  await expect(page.getByText(/Versión de análisis 2/)).toBeVisible()
  await expect(page.getByText('Aclaraciones pendientes',{exact:true})).toHaveCount(0)
  await page.getByText('Historial de análisis (2 versiones mostradas)',{exact:true}).click()
  await expect(page.getByText('Original conservado: Hay basura acumulada en la vía pública.').first()).toBeVisible()
  await page.getByRole('button',{name:'Buscar relacionados',exact:true}).click()
  await expect(page.getByText(/Índice ausente|Índice desactualizado/)).toBeVisible()
  const detail=await (await page.request.get(`/api/v1/admin/incidencias/${incident.id}`)).json()
  expect(detail.revision).toBe(1)
  expect(detail.state).toBe(incident.clasificacion.estado)
})
