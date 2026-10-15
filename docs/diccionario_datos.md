# Contrato CSV UTF-8

Plantilla: `data/plantilla.csv`. Una fila por texto independiente o variante documentada. Las transformaciones no convierten elaborado en real. No incluir contacto operativo ni ubicación identificable.

| Campo | Tipo y regla |
|---|---|
| id | Texto único, estable, sin identificador ciudadano |
| texto_reclamo | Español redactado/anonimizado, no vacío; único tras normalizar |
| categoria | C1–C8; vacío solo en challenge/functional sin tema asignable |
| fuente | Identificador del registro de fuentes/protocolo autorizado |
| tipo_dato | `real` o `elaborado` |
| validado | `true`/`false`; revisión temática/privacidad según protocolo; demo distingue su verificación funcional |
| grupo_origen | Original/plantilla común; todas las paráfrasis y subcasos comparten valor |
| particion | Vacío antes de particionar o train/validation/test/challenge/functional |
| motivo_revision | Razones esperadas separadas por punto y coma; desafío puede tener categoría conocida |
| transformacion | Identificador de proceso y versión; detalles en manifiesto de transformación |
| licencia_autorizacion | Referencia real al permiso/licencia, no una autorización inventada |

Validador: columnas, IDs, categorías, procedencia mínima, nulos, tipos, validación, particiones, grupos y duplicados. La similitud cercana usa SequenceMatcher≥0.92 y falla si pares similares tienen grupos distintos. Es conservadora, O(n²), adecuada a la meta de ~900; no garantiza ausencia de equivalencia semántica. Revise paráfrasis manualmente y agrúpelas antes de partir. No elimine negaciones/tildes para forzar deduplicación.

`split` genera CSV y `.manifest.json` con semilla 42, hashes de entrada/salida, IDs, grupos y conteos por cohorte. `prepare` conserva originales, elimina vacíos, normaliza/redacta y marca toda salida `validado=false` hasta revisión humana; `.privacy.json` guarda conteos/hashes. No declara anonimización perfecta. Fuentes completas/restringidas no se versionan.

Anotaciones independientes: CSV `id,anotador_a,anotador_b`, valores C1–C8 o SIN_TEMA. `agreement` calcula acuerdo y kappa antes de adjudicar; kappa indefinible se informa null. Adjudicación en archivo separado `id,etiqueta_final,adjudicador,fecha,motivo,version_guia` dentro de espacio autorizado, sin usar predicciones como verdad.
