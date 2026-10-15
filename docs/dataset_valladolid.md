# Valladolid 2009–2020: fuente estructurada y extracción

Se inspeccionó el archivo local `682291-D0072-2020.csv` proporcionado por el usuario, sin modificar el original. SHA-256 `25f7ae0176acaadb6de0c85f23eafc9185ab3f4ac463fff4c912b461733558fe`, tamaño 24 873 907 bytes, UTF-8 con BOM y separador `;`. Procedencia contrastada con el [catálogo oficial del Ayuntamiento de Valladolid](https://www.valladolid.es/es/temas/hacemos/open-data-datos-abiertos/catalogo-datos/ficheros-datos-elaborados-clasificados-sectores/sector-publico): recurso de incidencias, quejas, sugerencias y reclamaciones actualizado a 31/12/2020.

Resultado de inspección: **202 296 filas**, 12 columnas, 202 296 identificadores únicos y exclusivamente numéricos en `peticion`; 156 etiquetas administrativas no vacías en `tema` (157 valores si se cuenta el vacío). Fechas observadas de petición 31/07/2009–30/12/2020, sin fechas inválidas. No contiene un campo de descripción libre. Columnas: `peticion, canal_entrada, fecha_peticion, tipo, estado, tema, fecha_cierre, canal_respuesta, x, y, LON, LAT`.

## Uso incorporado al proyecto

`python -m ml.source_import <archivo>` produce el informe agregado `reports/sources/valladolid_2020.json` y cuatro tablas: temas con frecuencia/criterio, años, tipos y correspondencias C1–C8. El registro de fuentes guarda hash, columnas, permiso publicado y exclusión de entrenamiento. El endpoint protegido `GET /api/v1/admin/fuentes` entrega estos resúmenes; Personal → Fuentes de datos los muestra con búsqueda y filtros, separado de la bandeja de incidencias.

No se cargó el original en la base de incidencias; no se exportaron filas individuales, IDs ni coordenadas. Los conteos externos no alteran estadísticas operativas, reglas de competencia, prioridades ni el modelo activo. No se hicieron llamadas de entrenamiento ni activación para esta fuente.

| Correspondencia orientativa | Registros de origen |
|---|---:|
| C1 | 40 312 |
| C2 | 15 853 |
| C3 | 16 886 |
| C4 | 13 489 |
| C5 | 24 464 |
| C6 | 0 |
| C7 | 12 768 |
| C8 | 3 703 |
| Total de correspondencias orientativas | 127 475 |

Restantes: 28 639 fuera de alcance; 28 354 ambiguos; 17 826 sin correspondencia documentada; 2 sin tema. Estas cantidades suman las 202 296 filas. Los tipos originales se conservan separados: quejas, información, sugerencias, reclamaciones y vacíos. No toda fila con tema compatible es una incidencia urbana clasificable.

El mapeo `config/valladolid_mapping.json` está versionado y **no validado independientemente por personas**. Usa etiquetas administrativas únicamente para comparar cobertura de la taxonomía. No asigna verdades temáticas a descripciones ausentes. C6 queda en cero: «Innovación y Comercio» es demasiado amplia para atribuir una incidencia de fiscalización. «Jardines. Limpieza» queda ambiguo C1/C5; «Tapas de registro» no distingue C2/C8; «Tasa de basuras» se excluye porque es un asunto tributario. Policía/vigilancia es comparable al tema C4, sin atribuir competencias de Serenazgo ni de una entidad de Juliaca.

## Por qué no se entrena con este archivo

`peticion` es el número del caso, no el mensaje. `tema` es una etiqueta. Renombrar esa etiqueta como `texto_reclamo` filtraría la respuesta: el clasificador aprendería los nombres administrativos y su frecuencia, sin aprender lenguaje ciudadano. Duplicar una etiqueta miles de veces tampoco genera ejemplos independientes. El validador rechaza el formato bruto y también un supuesto corpus real que declare esta fuente sin texto libre.

No se generaron descripciones sintéticas presentadas como reales. Los ejemplos elaborados existentes siguen identificados como elaborados y no reemplazan validación/test. Para mejorar rendimiento se necesita una fuente que incluya descripciones redactadas y referencias anotadas con grupos independientes. Avilés contiene `Descripcion`, pero requiere el protocolo de privacidad y etiquetado; un corpus local autorizado sigue siendo indispensable para evaluar Juliaca.

## Reproducción

Desde la raíz, PowerShell:

```powershell
& .\.venv\Scripts\python.exe -m ml.source_import 'C:\Users\Usuario\Downloads\682291-D0072-2020.csv'
& .\.venv\Scripts\python.exe -m pytest tests/test_source_import.py
```

Otro equipo debe pasar la ruta de su copia autorizada. No necesita copiarla a Git. El archivo original permanece bajo su custodia. Los reportes guardan hash y cambios; el mapeo puede revisarse sin reentrenar ni alterar el artefacto del modelo.

## Atribución y límites

El [portal Open Data del Ayuntamiento](https://www.valladolid.es/es/temas/hacemos/open-data-datos-abiertos) publica como condición general **CC BY 3.0 ES salvo indicación contraria**. Se conserva atribución, enlace y declaración de las transformaciones; no se asume respaldo municipal. Revisar condiciones específicas antes de redistribuir originales. Las frecuencias son de Valladolid y de su sistema de registro entre 2009 y 2020: no representan demanda, prioridad, balance de clases ni desempeño en Juliaca.
