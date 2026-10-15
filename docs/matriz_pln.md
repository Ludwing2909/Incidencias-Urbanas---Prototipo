# Matriz requisito → componente → comprobación → estado

Ampliación del 14 de octubre de 2026. Verificado significa comprobación técnica del prototipo; no validación local ni institucional.

| Requisito | Componente | Comprobación/evidencia | Estado |
|---|---|---|---|
| Inspeccionar proyecto y otros CSV | Servicios, Predictor, reportes, pln_csv_inspection.json | Hash del corpus activo; CSV existentes revisados por esquema/conteos; Avilés excluido | Verificado |
| 1A Entrada, longitud e idioma real | AnalysisInput, backend/pln.analyze | Vacíos/límites; heurística de idioma declarada | Verificado; detección lingüística local pendiente |
| 1B Preparación real y cambios | normalize/anonymize, safe_diff, Stage | Redacción de correo/teléfono/DNI; comparación sin segmentos sensibles | Verificado técnicamente; anonimización perfecta no acreditada |
| 1C Analizador y vocabulario | ObservedVectorizer | Palabras/bigramas y caracteres según artefacto; desconocidos/vector vacío | Verificado |
| 1D TF-IDF persistido sin fit | ml/trace.py | Pesos/IDF iguales a transform del artefacto; fit/fit_transform bloqueados durante prueba | Verificado |
| 1E Estimador/puntuación/calibración | model_description, Predictor.execute | LinearSVC base y CalibratedClassifierCV; margen/probabilidad distintos | Verificado |
| 1F Revisión y R9 | classification_result común | Toda demo en revisión; mismos resultados de registro y traza | Verificado |
| 1G Destino/vigencia | destination_info, DestinationCard | Consulta reglas; pendiente de confirmación; C7/C8 sin derivación automática | Verificado; competencias institucionales pendientes |
| 1H Resultado sin seguimiento ficticio | PLNAnalysis/AnalysisView | Analizar no escribe casos/predicciones/estados/auditoría de casos | Verificado |
| 2 Procedencia/particiones/grupos | pln_metadata.dataset_summary, PLNData | Hash, tipos/distribución, grupos compartidos y duplicados exactos | Verificado; controles semánticos/locales pendientes |
| 2 Comparación, pliegues, parámetros | experiment.json, --expanded | Referencias y cuatro modelos en pliegues equivalentes; nombres concretos | Ejecutado solo sobre corpus elaborado |
| 2 Métricas/matrices/soporte/fechas | experimental_audit, MetricsTable | Funcionales/desafíos separados; n conocido; métricas null sin soporte; fechas antiguas no inventadas | Verificado |
| 2 Curvas de aprendizaje | Lectura learning_curve.json | Ausencia mostrada como No evaluado | No calculadas |
| 3A Corpus local | data/templates; guía de anotación | Formatos vacíos de permiso, dos anotadores, acuerdo y adjudicación/test | Preparado; bloqueado por acceso/revisión externos |
| 3B Fuga/grupos/fuentes | ml.data, pipeline por pliegue | Tests negativos de duplicados, grupos, elaborados en test; evaluación real ausente | Parcialmente verificado |
| 3C Modelado ampliado | ml.experiment.train --expanded | pln-expanded-demo-20261014; palabras/caracteres, LR/LinearSVC/SVC RBF/NB | Ejecutado demo; candidato no activado |
| 3D Extracción | extraction + ruta extraccion + historial | Fragmentos literales, null y corrección humana versionada | Verificado técnicamente; precisión local pendiente |
| 3E Aclaraciones | AnalysisVersion, rutas/IncidentPLN | Original intacto, respuestas, versiones, preguntas no repetidas, 409/CSRF | Verificado |
| 3F Relacionados | related.py, build_related_index, RelationDecision | Coseno sin fit HTTP; top-k/umbral; excluir propio/futuros; hash snapshot; audit sin fusión | Verificado técnicamente; umbral/evaluación histórica pendientes |
| 3G Tarjeta tras persistir | Confirmation + DestinationCard | Código/secreto solo en registro; origen administrativo de destino | Verificado |
| 3H Formulario/revisión/correcciones | Register, Inbox, StatsResult | Flujos vigentes y conteos por tema original; filtros | Verificado; ubicación estructurada/catálogo local pendiente |
| 3I Resumen | Tablero de capacidades | Ausencia declarada | Pendiente por datos/evaluación |
| 3J Multitema/prioridad | hints/review_reasons/urgency | Negaciones y varias pistas; monoclase no presentado como multilabel | Parcialmente verificado; multilabel pendiente |
| 3K Retroalimentación/versionado | Review, manifiestos, activate/rollback | Predicción original intacta; activación explícita; no reentrenamiento por corrección | Parcialmente verificado; ciclo local pendiente |
| 3L PostgreSQL/Docker | verify_postgres, compose.verificacion.yaml | Config Compose válida; postgres_verificacion.json | Bloqueado: motor Linux no disponible; operación no ejecutada |
| 4 Contratos/permisos/privacidad | contratos_pln.md, OpenAPI, staff/CSRF/limit | Público solo texto nuevo; casos/reportes protegidos; respuestas acotadas | Verificado |
| 4 Responsive/accesibilidad | PLNProcess/IncidentPLN/CSS | Tablas con caption, etiquetas, estado real y prueba sin overflow móvil | Verificado; auditoría exhaustiva de accesibilidad pendiente |
| 4 Fallos de artefactos/reportes | Predictor, metadata, índice | Modelo ausente, vector vacío, reporte/índice ausente no impiden registro | Verificado |
| 5 Regresiones | pytest_pln_full.xml, playwright.json | Suite Python y ocho flujos de navegador; build TypeScript/Vite | Verificado; cifras en verificacion.md |
| Entrega técnica | 0002, contratos, servicios, UI, tests y documentos | Upgrade/downgrade/upgrade SQLite; demo migrada a 0002 | Verificado SQLite; no extrapolar a PostgreSQL |
| Explicación al docente | proceso_pln.md, sección final | Guion de PLN, TF-IDF, entrenamiento, evaluación y reglas | Entregado |

## Pendientes que no se marcaron como completados

Corpus local autorizado, anotación/acuerdo independientes, revisión lingüística y de privacidad, test real reservado, calibración/umbral real, evaluación de extracción/relaciones, competencias institucionales y piloto. También catálogo de barrios, resumen fiel, multilabel y criterios robustos de prioridad. El verificador PostgreSQL está preparado, pero no pudo ejecutarse con el motor Linux ausente.

## Incidencias de verificación

El primer build de Vite falló por EPERM dentro del aislamiento; el build normal autorizado pasó. Un renderizado trataba el número de miembros calibrados como una lista de trazas; se corrigió y las pruebas de navegador pasaron. Una repetición agotó el limitador de login de la base persistente de pruebas; el servidor e2e ahora limpia solo los contadores de tests/e2e.db al arrancar. No se relajaron límites de la demo ni permisos del backend. Los reportes finales sustituyen las corridas fallidas; esas incidencias no se presentan como fallos pendientes de producto.
