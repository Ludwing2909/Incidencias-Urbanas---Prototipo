# Proceso de PLN · ampliación del 14 de octubre de 2026

## Uso y permisos

Abra `/pln` desde **Proceso de PLN**. Escriba un ejemplo sin identidades y pulse **Analizar**. La petición no registra una incidencia, no obtiene un código y no modifica estados. Las operaciones ausentes se indican explícitamente. **Situación y mejoras** contiene las doce líneas A–L, con prioridad, problema, dependencia y criterio de cumplimiento. Sus estados técnicos no equivalen a validación local.

**Datos y entrenamiento** requiere iniciar sesión en Personal. Se consulta el modelo activo o un experimento local con artefacto íntegro; seleccionar un candidato no lo activa. El corpus se identifica por SHA-256 y los reportes por hash del artefacto. Ausencia de datos, evaluaciones o curvas se muestra como No evaluado/no disponible; no como una métrica cero. Los ocho funcionales y catorce desafíos permanecen separados de entrenamiento, validación y test. Los seis desafíos con tema conocido tienen un denominador distinto del total de catorce.

En el detalle del personal, **Analizar este caso y guardar versión** inicia un historial separado. Responda preguntas pendientes, corrija valores extraídos o continúe a revisión. Las respuestas se redactan preliminarmente y se conservan con el original y el usuario en versiones; un conflicto devuelve 409. Una corrección de extracción puede dejar null y declara origen humano. No cambia la clasificación, mientras una aclaración crea una nueva inferencia contextual. Ninguna de las dos reemplaza la predicción original ni cambia el estado operativo. No existe análisis de casos almacenados mediante código público.

## Cómo se obtiene la traza

`Predictor.execute` es la ejecución común. La observación usa copias superficiales por petición del contenedor calibrado y de sus Pipelines; comparte los mismos objetos ajustados de TF-IDF, clasificación y calibración. Un delegado observa cada llamada real a transform y devuelve el vector intacto. No se modifica el Pipeline global ni se ejecutan fit/fit_transform desde HTTP.

El modelo activo demo-v3 es **CalibratedClassifierCV(sigmoid) con cinco Pipelines TF-IDF + LinearSVC**. `svc` es un identificador histórico del experimento, no el nombre concreto de SVC de kernel. Cada miembro se ajustó con su subconjunto de entrenamiento y puede tener vocabulario e IDF diferentes. La traza los distingue y muestra hasta 80 características únicas y 30 pesos por miembro; informa totales y truncamiento. La puntuación pública final proviene de predict_proba; los estimadores base usan decision_function. Un margen no se presenta como probabilidad.

El analizador observado determina palabras, bigramas o caracteres según el artefacto. No hay corrección ortográfica, lematización, stemming, extracción por entidades, resumen ni multilabel. Stopwords se muestra omitida cuando la configuración es None. NFC, espacios y redacción por regex sí se ejecutan. El preprocesador callable `anonymize` sustituye el preprocesado predeterminado de scikit-learn: el parámetro lowercase=True por sí solo no acredita conversión efectiva a minúsculas. Se muestran las características realmente producidas; modificar esa preparación requiere otro entrenamiento y versión.

La frecuencia mostrada es el conteo del analizador; el IDF es idf_ persistido; el peso es el valor final de transform con la configuración de frecuencia binaria/sublinear y normalización del miembro. No se reajusta IDF sobre el mensaje. Los mayores pesos no son contribuciones causales de palabras a la decisión. Un vector vacío conserva la salida real del estimador, si la hay, y explica la falta de características representadas. La ausencia o fallo del modelo devuelve tema y puntuación nulos, con revisión.

Todos los tiempos usan perf_counter. El tiempo de inferencia incluye transform y calibración; etapas anidadas no se suman para obtener la latencia total. Las operaciones no implementadas solo miden el procesamiento de su estado, no un algoritmo inexistente. La comparación de preparación oculta segmentos sustituidos antes de responder: no devuelve el texto sensible eliminado. Esa protección sigue siendo preliminar y no acredita anonimización perfecta.

Los motivos distinguen umbral ausente/no validado, puntuación no probabilística o sin calibración y puntuación realmente inferior al umbral. Una puntuación alta ya no se etiqueta baja por falta de validación. La política de revisión de la demo permanece bloqueada y los motivos de predicciones históricas no se reescriben.

El destino se consulta en las reglas de la base, con validación, vigencia y versión. Cuando falta competencia confirmada, aparece **Área responsable pendiente de confirmación**. C7/C8 permanecen en revisión. No existe envío ni derivación oficial automática.

## Extracción y relacionados

La extracción inicial usa fragmentos literales para problema, barrio/sector/parque y referencia temporal; los campos no encontrados son null. La ubicación puede provenir del campo general. Las preguntas se generan sobre faltantes o pistas de varios temas y no repiten IDs ya respondidos. Es una referencia de reglas con errores posibles; necesita referencias anotadas y evaluación local.

El índice de relacionados es diferente del clasificador y se construye explícitamente fuera de HTTP:

```powershell
& .\.venv\Scripts\python.exe -m scripts.build_related_index
```

Usa TF-IDF de palabras/bigramas y similitud coseno, hasta 1000 casos. Se guarda bajo data/private/related_index, excluido de Git. Un hash del snapshot detecta cambios: después de nuevos registros o cambios de texto/ubicación/fecha se reconstruye offline. La consulta limita top-k a 10, permite umbral 0–1, excluye propio caso y fechas posteriores, y muestra coincidencia de ubicación y distancia temporal como contexto. No mezcla estos valores con probabilidades del clasificador. El valor predeterminado 0.25 es configurable, no un umbral validado localmente.

La referencia actual no mide relaciones históricas: para ese experimento se debe construir otro índice con corte temporal, agrupación y casos futuros excluidos también del ajuste del vectorizador. Las decisiones confirmar/descartar exigen sesión, CSRF y motivo; quedan auditadas y no fusionan, borran o cambian estados. Índice ausente/desactualizado no impide registrar ni revisar incidencias.

## Experimento adicional y límites

`--expanded` habilita una búsqueda offline acotada: word(1,2), char_wb(3,5), logística, LinearSVC, MultinomialNB y SVC RBF; C 0.1/1, pesos None/balanced o alpha 0.1/1 según corresponda. Conserva Dummy mayoritario y palabras clave en los mismos pliegues. Los reportes nuevos registran el nombre concreto del estimador y la fecha de entrenamiento/evaluación. No se inventaron fechas para evaluaciones antiguas.

```powershell
& .\.venv\Scripts\python.exe -m ml.cli train data/demo_particionado.csv reports/runs/nueva-comparacion --demo --expanded
& .\.venv\Scripts\python.exe -m ml.cli threshold data/demo_particionado.csv reports/runs/nueva-comparacion
& .\.venv\Scripts\python.exe -m ml.cli evaluate data/demo_particionado.csv reports/runs/nueva-comparacion --partition functional
```

La ejecución `pln-expanded-demo-20261014` utilizó los 64 textos elaborados y cinco pliegues por grupos. CV macro-F1: Dummy 0.0181; palabras clave 0.9733; logística 0.7675; LinearSVC 0.7542; NB 0.7342; SVC RBF 0.6163. Seleccionó logística con caracteres entre modelos aprendidos. No superó la referencia de palabras clave. Funcionales: 8/8 y macro-F1 1.0; desafíos con tema conocido: 6/6 y macro-F1 de clases presentes 1.0. Estos conjuntos diminutos y elaborados no son prueba real ni evidencia de eficacia local. No se calculó una curva de aprendizaje. El umbral quedó null, cobertura operativa cero. El candidato no se activó: registro y traza siguen en demo-v3.

Las correcciones operativas no alimentan automáticamente el entrenamiento. Adjudicar una nueva versión de datos, evaluar candidatos y revisar resultados antes de activar; conservar rollback y no reutilizar indefinidamente el mismo test para selección.

## Corpus y operación pendientes

`data/templates/` contiene formatos vacíos de autorización, anotación independiente, adjudicación, extracción, relaciones y reserva del test local. No son datos reales ni permisos otorgados. Completar dos anotaciones sin mostrar predicciones, medir acuerdo antes del consenso y conservar grupos, fuentes y cortes de prueba independientes. Valladolid continúa solo como agregado externo sin descripción libre; no se incorporaron otros CSV de terceros a entrenamiento.

Migración 0002 agrega analysis_versions y relation_decisions. Antes de arrancar:

```powershell
& .\.venv\Scripts\python.exe -m alembic upgrade head
& .\.venv\Scripts\python.exe -m scripts.export_contract
& .\.venv\Scripts\python.exe -m scripts.verify_postgres
```

El verificador PostgreSQL usa un proyecto Docker aleatorio, base y puerto aislados, prueba migración/concurrencia/idempotencia y pg_dump/restore sobre una segunda base vacía. En esta entrega quedó **bloqueado** porque falta el motor Docker Linux. Las configuraciones Compose pasaron, pero no se ejecutaron contenedores ni restauración PostgreSQL. No acredita ejecución del stack institucional completo.

Resumen, multilabel, detección robusta de urgencia, catálogo local de ubicaciones y validación de competencias siguen pendientes. La matriz de requisitos y las evidencias están en matriz_pln.md. El informe Word anterior corresponde al estado documentado del 13 de octubre; esta ampliación y sus resultados se documentan aquí.

## Guía breve para el docente

1. PLN transforma lenguaje escrito para que el sistema pueda identificar patrones; no verifica la verdad del reclamo.
2. Mostrar un mensaje y su preparación real; conservar tildes y negaciones, y señalar límites de redacción.
3. TF-IDF convierte características en números: combina frecuencia del mensaje con IDF aprendido en entrenamiento; nunca aprende del ejemplo analizado.
4. Mostrar LinearSVC calibrado, su probabilidad final y los motivos de revisión; explicar que no existe un umbral real validado.
5. Abrir Datos y entrenamiento: separar entrenamiento/CV de funcionales/desafíos y de una prueba real ausente. Comparar referencias sin afirmar rendimiento de Juliaca.
6. Mostrar el destino: depende de reglas administrativas, no de TF-IDF. Finalmente abrir A–L y explicar qué evidencia externa falta.
