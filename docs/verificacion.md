# Verificación ejecutada · 13 de octubre de 2026

Entorno: Windows, PowerShell 7.6.5, Node 24.11.0, Python 3.12.14 incluido en el runtime de Codex; `.venv` local. El alias `python` de Windows no arrancó y el venv incluido no tenía pip, por lo que se instalaron dependencias con el pip del runtime y `--python .venv/Scripts/python.exe`. README para otra instalación exige Python 3.12 de python.org. Versiones congeladas en requirements.lock.txt y package-lock.json.

| Comprobación | Resultado real |
|---|---|
| pytest API/ML/migración/operación | **58 pasadas**, 0 fallidas, 0 omitidas; última ejecución 66.96 s. Evidencia `reports/pytest.xml`. |
| Playwright contra Vite/FastAPI reales | **2 pasadas**, 0 fallidas; última ejecución 10.0 s. Evidencia `reports/playwright.json`. |
| TypeScript y build Vite 6.4.4 | Pasado; JS 254.58 kB / gzip 80.79 kB y CSS 11.83 kB; archivos dist locales. |
| Contratos Pydantic/OpenAPI | Exportados en docs/openapi.json; registro, seguimiento, auth, listados/detalle, reglas, estadísticas y modelo usan contratos; prueba de enum de 8 clases y respuesta de registro. |
| Entrenamiento demo | Ejecutado: 64 textos elaborados, 5 pliegues por grupos, cinco referencias, búsqueda y calibración sigmoide. Selección aprendida SVC, CV macro-F1 0.540; no superó palabras clave (0.973). |
| Umbral demo | Ejecutado; cero validación real, umbral null, todas las sugerencias en revisión. |
| Evaluación funcional y desafíos | Ejecutada y separada: 8 y 14 textos elaborados. Funcional accuracy 0.875 / macro-F1 0.833, soporte 1 por clase; no prueba real. |
| CSV/particiones/fugas | 86 filas validadas; manifiestos con hashes/IDs/grupos/semilla. Tests negativos para R9, duplicados, grupos, elaborados en test y falta de soporte. |
| Persistencia/concurrencia | SQLite probado: reinicio, 12 registros concurrentes, reintentos concurrentes con misma clave, unicidad, revisión con conflicto. No extrapolar a PostgreSQL. |
| Migración | Upgrade → downgrade → upgrade sobre base temporal pasado; demo migrada y reglas sembradas. |
| Respaldo SQLite | Backup real probado sobre fixture temporal, integridad y rechazo de destino existente. |
| Notebooks | Dos archivos nbformat válidos, todas las celdas Python compilan; no ejecutados completos en Colab ni se inventaron outputs. |
| Fuente Avilés | Descarga/inspección real: 2020 filas, 12 columnas, 2000 descripciones distintas; fuera del entrenamiento. |
| Otras fuentes | La Carlota: timeout; Valladolid: límite inicial/timeout SSL al ampliar; SENACE: HTML inspeccionado, CSV generado en navegador pendiente de descarga/permiso. |
| Auditoría npm | Primera instalación: 4 vulnerabilidades altas. Actualizadas versiones corregidas; resolución final reportó **0 vulnerabilidades**. |
| Compose | `docker compose config --quiet` pasado. No se ejecutaron contenedores ni pruebas PostgreSQL: motor Linux no disponible aun tras iniciar Docker Desktop en segundo plano. |
| Demo local y diseño final | FastAPI en 127.0.0.1:8000 y Vite en 127.0.0.1:5173 iniciados; health ready devolvió `modelo_disponible=true`. Capturas de escritorio/móvil inspeccionadas visualmente en reports/ui_desktop.png y ui_mobile.png. |

Los tests verifican: taxonomía/fronteras, revisión/urgencia y límites de heurísticas, tamaños/vacíos, score/margen, C7/C8 y reglas ausentes/no validadas, ausencia/incompatibilidad y fallo de inferencia, corrección conservando predicción, permisos/CSRF/logout, transiciones/evidencia, secreto/código incorrectos, límites, concurrencia/idempotencia, reinicio, migraciones, grupos/duplicados, predicción script/API, política de evaluación y denominadores nulos, respaldo y notebooks. Navegador comprueba formulario→registro→seguimiento→revisión→historial y errores/diseño móvil. No son prueba de eficacia municipal ni validación lingüística/local.

Incidencias de ejecución corregidas: build aislado bloqueó realpath (se ejecutó autorizado fuera de aislamiento); pytest aislado se detuvo sin resultados (cancelado y repetido con acceso local normal); scorer de etiquetas textuales requirió pos_label=None; selectores de Playwright tenían errores de sintaxis corregidos antes del pase final. Intentos demo-v1/v2 no son experimentos completados. No se fabricaron resultados de esas ejecuciones.

Advertencias conocidas: deprecaciones de AnyIO/Starlette y Pyparsing/Matplotlib (15 avisos en la última corrida), sin fallos de pruebas. Actualizar con nueva resolución/pruebas antes de piloto. Sesiones, reglas y modelo sirven la demo local; credenciales aleatorias solo en `.env`.

No ejecutado/no validado: rendimiento real de Juliaca; anotación independiente humana; competencias y destino institucional; anonimización perfecta; copia/restauración PostgreSQL; despliegue institucional; evaluación de lenguas quechua/aimara; medición de tiempos/impacto municipal. Procedimientos y dependencias en docs/matriz_cumplimiento.md.

## Integración posterior del archivo de Valladolid

La copia proporcionada por el usuario se inspeccionó y extrajo con `ml.source_import`: 202 296 filas, 156 temas no vacíos y cero descripciones libres. Hash del archivo original comprobado sin modificación; conteos por decisión reconcilian exactamente el total. Cuatro tablas agregadas, mapeo versionado y endpoint/vista de fuentes incorporados. No se importaron IDs/coordenadas ni casos operativos y el modelo activo sigue `demo-v3`.

Verificación de este cambio: **45 tests pasados** (`tests/test_source_import.py` y `tests/test_ml.py`, 40.22 s, evidencia `reports/pytest_dataset.xml`), incluyendo seis nuevos tests de ingestión, exclusión, privacidad del resumen y permisos. **3 pruebas de navegador pasadas** (9.9 s, `reports/playwright.json`) verifican además conteos y filtros de la nueva vista. TypeScript/build pasados: 39 módulos, JS 260.71 kB / gzip 82.27 kB. No se repitió toda la suite anterior de 58 tests porque el cambio se verificó con su cobertura de datos/ML y flujos de integración afectados.

Una carrera en la prueba de bandeja quedó corregida: con registros de ejecuciones previas podía encontrar varios enlaces «Revisar» antes de actualizarse el filtro; ahora identifica el caso mediante el código único. La repetición completa de las tres pruebas pasó. La API y Vite locales fueron reiniciados con la ruta de fuentes disponible. Véase `docs/dataset_valladolid.md` para límites y procedencia.

## Acceso directo al panel sin sesión

Se corrigió la navegación del frontend: HTTP 401 en la comprobación de sesión redirige a Personal, conserva la ruta solicitada y vuelve a ella tras autenticación. Se conserva el código HTTP en ApiError; errores de servicio siguen mostrando Reintentar y no producen una redirección incorrecta. La ruta de retorno se restringe al panel local. No se retiraron permisos del backend ni se publicaron contraseñas en la interfaz.

TypeScript/build pasados y **5 pruebas de navegador pasadas** en 10.3 s (`reports/playwright.json`), incluidas dos nuevas pruebas: acceso directo a fuentes sin sesión y retorno después de login; error de servicio 503 con reintento en la ruta original. Backend e interfaz de demostración reiniciados después de la verificación.


## Proceso de PLN · 14 de octubre de 2026

| Comprobación final | Resultado |
|---|---|
| Suite completa Python | 78 pasadas, 0 fallidas, 0 errores, 0 omitidas; 90.03 s. reports/pytest_pln_full.xml. |
| Navegador | 8 pasadas, 0 fallidas, 0 omitidas; 21.49 s. reports/playwright.json. |
| TypeScript y Vite | Pasado: 41 módulos, JS 287.53 kB / gzip 89.11 kB. |
| Traza real | Salida igual a predicción normal; pesos e IDF iguales al vectorizador; sin fit/fit_transform, sin escritura de casos. Concurrencia, vocabulario vacío y fallo del estimador comprobados. |
| Historial/privacidad | Aclaraciones, corrección nullable de extracción, original/estado conservados, CSRF/roles/conflicto y relaciones sin fusión comprobados. |
| Modelo y corpus | demo-v3 sigue activo; 86 textos elaborados; Valladolid/Avilés fuera del entrenamiento. CSV revisados en reports/pln_csv_inspection.json. |
| Experimento adicional | Palabras/caracteres y cuatro modelos ejecutados offline; logística CV 0.7675, keywords 0.9733; 8 funcionales y 6 desafíos conocidos perfectos, insuficientes para conclusión local. Candidato no activado, umbral null. |
| SQLite | Backup previo íntegro; migración 0002 aplicada; upgrade/downgrade/upgrade sobre base temporal pasado. Índice separado inicial construido con un caso; no hay otro candidato que sugerir. |
| QA visual | Seis capturas escritorio/móvil/reportes/candidato/tablero inspeccionadas; sin errores JS u overflow. |
| Compose/PostgreSQL | Ambas configuraciones válidas. Verificador bloqueado: motor Docker Linux no disponible. Contenedores, PostgreSQL y pg_restore NO ejecutados. |

Las cifras de la suite específica PLN se solapan con la suite completa: no se suman. Las incidencias de build aislado, renderizado y límites de la base de pruebas se corrigieron; se documentan en matriz_pln.md. Persisten avisos de deprecación AnyIO/Pyparsing sin fallos. El control de frecuencia operativo conserva sus límites; solo tests/e2e.db limpia contadores al iniciar cada suite. Los motivos nuevos separan umbral no validado, puntuación no probabilística/sin calibración y puntuación baja. No se reescribieron predicciones históricas.

No ejecutado/validado: test real local, doble anotación independiente, competencias institucionales, precisión local de extracción/relaciones, calibración/umbral real, curva de aprendizaje, resumen, multilabel, piloto ni operación PostgreSQL. Matriz completa en matriz_pln.md; guía docente/uso en proceso_pln.md.


## Prioridad y limpieza de interfaz

priority-rules-v1 añade alta/media/baja con motivo y evidencia, sin entrenar otro modelo. Casos insuficientes: media provisional. Negaciones, precedencia de riesgo y coherencia registro/traza comprobadas. Los valores antiguos ordinaria/posible urgencia se admiten para consultar historial, sin reinterpretarlos como prioridad nueva. Sin migración: evaluación conservada en JSON de predicción.

Pruebas focalizadas prioridad/API/PLN: 38 pasadas, 0 fallidas/omitidas (9.333 s), reports/pytest_priority.xml. Navegador: 9 pasadas, 0 fallidas/omitidas (16.6 s), reports/playwright.json. Build TypeScript/Vite pasado: 41 módulos, JS 287.78 kB/gzip 89.14 kB. No se repitió la suite completa anterior, dado que se comprobaron las áreas afectadas y los flujos de registro/seguimiento/revisión. Se retiraron la franja superior, Laboratorio PLN del logo y textos del pie; se simplificaron textos de formulario/confirmación. La prioridad es orientativa y aún no está validada con anotaciones locales.
