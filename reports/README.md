# Evidencias y resultados

`source_inspection.json`: descargas/inspección reales con enlaces, fechas, columnas, conteos, hashes y fallos. No contiene textos personales.

`sources/valladolid_2020.json` y `sources/valladolid_2020/*.csv`: análisis agregado del archivo proporcionado por el usuario. 202 296 registros administrativos sin descripciones; cuatro tablas, mapeo orientativo y exclusión de entrenamiento. `pytest_dataset.xml` contiene la verificación de ingestión/ML realizada después de esa integración.

`pytest.xml`: resultados reales de tests API/ML/operación. `playwright.json`: flujo navegador contra FastAPI real. `ui_desktop.png`/`ui_mobile.png`, si existen, son capturas propias del prototipo.

`runs/demo-v3/`: comparación ejecutada, manifiesto, artefactos, tablas CV, umbral nulo, métricas funcionales y de desafío, matrices y curvas. No hay prueba/validación reales. Directories demo-v1/v2 corresponden a intentos fallidos previos al ajuste del scorer y no tienen `experiment.json` de ejecución completada; no se presentan como resultados.

Los modelos/resultados grandes de runs son artefactos locales excluidos de Git. `docs/model_card.md` registra el resultado principal y sus límites. Reproducir en un directorio nuevo siguiendo README; no modificar experimentos ya congelados.
