# Contratos del apartado Proceso de PLN

Versión de contrato: pln-v1. No se entrena ni registra una incidencia al analizar.

| Ruta | Permiso | Contrato |
|---|---|---|
| POST /api/v1/pln/analizar | Público, entrada limitada y control de frecuencia | descripcion (1–3000 caracteres), ubicacion_general opcional (180). Devuelve AnalysisResult; nunca código ni secreto. |
| GET /api/v1/pln/metadatos | Público | Versión y estructura del modelo cargado, sin vocabulario completo, textos, IDs de entrenamiento ni rutas locales. |
| GET /api/v1/admin/pln/datos | Personal | Auditoría agregada del modelo activo o ?version de una ejecución local con artefacto íntegro; la consulta no activa el candidato. Reportes ausentes/null significan No evaluado. |
| GET /api/v1/pln/capacidades | Público | Capacidades, prioridades, dependencias y evidencias para completar A–L. |
| POST /api/v1/admin/incidencias/{id}/analisis | Personal + CSRF | Análisis del texto autorizado; guarda una versión independiente, sin modificar estado ni predicción original. |
| POST /api/v1/admin/incidencias/{id}/aclaraciones | Personal + CSRF | Respuestas a preguntas pendientes y versión observada; conserva original y todas las versiones. Conflicto 409. |
| POST /api/v1/admin/incidencias/{id}/extraccion | Personal + CSRF | version y campos corregidos (problema_principal, lugar_general, referencia_temporal), string o null. Nueva versión; conserva salida del clasificador y declara origen humano. |
| GET /api/v1/admin/incidencias/{id}/analisis | Personal | Historial de análisis y aclaraciones, sin credenciales. |
| GET /api/v1/admin/incidencias/{id}/relacionados | Personal | top_k 1–10, umbral 0–1; índice TF-IDF separado creado fuera de HTTP, exclusión propia y de futuros. |
| POST /api/v1/admin/incidencias/{id}/relaciones | Personal + CSRF | relacionado_id, confirmar/descartar, motivo. Registra decisión; nunca fusiona casos. |

Cada etapa: id, nombre, estado (aplicada/omitida/no implementada/no disponible), motivo, entrada/salida permitida, transformaciones, version, tiempo_ms y limitacion. Los tiempos son medidos, no animados artificialmente. La comparación de preparación oculta los segmentos detectados como sensibles antes de enviarlos. La redacción es preliminar y no garantiza eliminación de identidades.

La traza observa transform de cada Pipeline ajustado dentro del ensemble calibrado mediante copias superficiales por petición. Los vectorizadores, clasificadores y calibradores son los mismos objetos ajustados; no se modifica el artefacto ni se ejecuta fit. Cada miembro puede tener vocabulario/IDF diferentes. Se limita a 30 pesos y 80 características por miembro, con totales y truncamiento explícitos.

Datos experimentales: únicamente agregados y referencias de reportes locales asociados al modelo; no textos o identificadores del corpus. Consultas públicas nunca aceptan IDs o códigos de casos almacenados. Las respuestas llevan Cache-Control no-store. No se registran cuerpos en logs. El limitador existente puede actualizar sus contadores, pero analizar no escribe incidencias, predicciones, estados ni auditorías de casos.
