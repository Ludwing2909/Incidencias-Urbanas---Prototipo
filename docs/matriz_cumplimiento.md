# Matriz requisito → componente → evidencia

Los estados de evidencia distinguen implementación de verificación empírica/institucional. La demostración no certifica rendimiento en Juliaca.

| Requisito del encargo | Archivo / componente | Evidencia y dependencia |
|---|---|---|
| 1 Alcance académico y adaptación | README, docs/arquitectura, Home | UI explica límites; no chatbot ni envío externo. Documento metodológico adicional no recibido. |
| 2 Ocho categorías/R9/fronteras | config/categories.json, backend/schemas, services, docs/anotacion | Tests de C1/C5, C2/C3, C2/C8 y R9 fuera del enum; campos separados. |
| 3 Tecnologías/separación/bloqueos | frontend/package*.json, requirements*, backend/registration, ml/* | React/TS/Vite/Router/Tailwind y FastAPI/SQLAlchemy/Alembic; build y pytest. PostgreSQL Compose implementado, motor no disponible para ejecución. |
| 4 Fuentes y adquisición | config/sources, scripts/inspect_sources, ml/source_import, reports/source_inspection | Avilés inspeccionado, 2020 filas. Valladolid inspeccionado, 202 296 filas estructuradas sin descripción, excluido de entrenamiento y usado en cuatro tablas/vista agregada. Ninguna etiqueta administrativa convertida en texto real. Corpus local autorizado pendiente. |
| 5 CSV/etiquetado/acuerdo | ml/data, plantilla CSV, docs/anotacion/diccionario | Validación y acuerdo/kappa verificados con fixtures; no doble anotación humana real completada. |
| 6 Limpieza/privacidad | ml/text, ml.data.prepare, docs/datos_y_privacidad | Preservación de tildes/negaciones; redacción preliminar probada; anonimización humana y política institucional pendientes. |
| 7 Particiones y fuga | ml.data.split_data/folds, demo_particionado.manifest | Control de IDs/grupos/duplicados; semilla y pliegues explícitos; prueba real pendiente, elaborados nunca validation/test. |
| 8 Cinco modelos/búsqueda/notebooks | ml/experiment, notebooks, reports/runs/demo-v3 | Cinco referencias entrenadas realmente; tablas CV/tiempos/parámetros; notebooks válidos sin salidas inventadas. Comparación real/híbrido depende de corpus real. |
| 9 Calibración y abstención | ml/experiment.choose_threshold, inference, backend/services | Sigmoide sobre pliegues de entrenamiento; margen no porcentaje; umbral null sin validación real; C7/C8 bloqueadas. Tests de puntuación/margen/reglas/modelo. |
| 10 Evaluación y reportes | ml.experiment.evaluate, reports/runs, model_card | Resultados funcionales/desafíos elaborados separados, matrices, curvas e incertidumbre; n/denominadores/null explícitos. Evaluación real local/externa y destino institucional pendientes. |
| 11 Reglas/estados/correcciones | Rule/Review/StateHistory/Audit, rutas admin, Rules/Detail | Nuevas versiones preservan reglas anteriores; originales/correcciones separados; permisos/evidencia/transiciones probados. Competencias aún no validadas. |
| 12 DB/API/códigos/health | backend/db, migrations, registration/main, docs/openapi | Migración upgrade/downgrade, registro sin modelo, código con UPSERT y unicidad, concurrencia/idempotencia/contratos probados en SQLite. |
| 13 Frontend conectado | frontend/src/*, integration.spec | Formularios, confirmación, seguimiento, sesión, resumen, bandeja, detalle, reglas y modelo; dos pruebas de navegador contra FastAPI real pasadas. |
| 14 Seguridad/seguimiento | backend/security/settings, frontend/api, nginx | Argon2id, sesiones revocables, CSRF, CORS, roles, secreto con hash, límites persistentes y respuestas mínimas; pruebas negativas pasadas. |
| 15 Operación/versionado | compose, manage, scripts/rollback_model/sqlite_backup, docs/operacion | Modelo activo propio/manifiesto, activación y archivo previo; copia SQLite probada. PostgreSQL/restore y Compose en ejecución pendientes por motor detenido. |
| 16 Pruebas de aceptación | tests/*, frontend/tests, reports/pytest.xml/playwright.json | Evidencia real de pruebas, build, OpenAPI y auditoría npm; cifras finales en docs/verificacion. No valida lingüística ni rendimiento local. |
| 17 Documentación/entrega | README y docs/* | Arquitectura, diccionario, protocolos, model/dataset card, manual, operación, fuentes, guion y matriz. |
| 18 Fases y pendientes | comentarios de ejecución y docs/verificacion | Inspección, contratos, datos/configuración, persistencia, ML, frontend e integración realizadas; pendientes externos explicitados. |

## Pendientes externos concretos

Ampliación Proceso de PLN: matriz detallada de los nuevos requisitos, componentes, comprobaciones y estados en [matriz_pln.md](matriz_pln.md). Las capacidades técnicas implementadas no completan los siguientes requisitos externos.

1. Obtener autorización y corpus local urbano español; reservar evaluación real independiente antes de desarrollo.
2. Revisar privacidad, lengua local, grupos/paráfrasis, doble anotación ≥20 % y test/desafíos; calcular acuerdo antes de adjudicar.
3. Aclarar licencias/compatibilidad de fuentes externas, excluir catálogos/reclamaciones fuera de alcance y registrar mapeos/exclusiones.
4. Entrenar real e híbrido con selección independiente y evaluar sin reutilización del test para alcanzar metas; calibración/umbral real con n e incertidumbre.
5. Revisar ROF/competencias y vigencia institucional con responsable y fuente documental; proporcionar referencia administrativa de destino. C7/C8 siguen en revisión.
6. Aprobar finalidad, base legal, conservación, derechos/acceso y seguridad del piloto. No se enviaron datos a entidades.
7. Iniciar un motor PostgreSQL/Docker operativo, ejecutar Compose, respaldo/restauración y pruebas de concurrencia sobre ese motor antes del piloto.
