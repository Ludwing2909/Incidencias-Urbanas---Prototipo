# Dataset card · demostración v1

La ampliación del 14/10/2026 conserva este corpus y su hash. La comparación adicional `pln-expanded-demo-20261014` sigue utilizando únicamente los mismos textos elaborados; no añade prueba real. El apartado Datos y entrenamiento calcula tipos, particiones, distribución y grupos desde el CSV cuyo hash coincide con el artefacto seleccionado. Las anotaciones independientes no están documentadas para esta demostración. `data/templates/` entrega solo encabezados vacíos para permisos, anotación/adjudicación, extracción, relaciones y reserva de test local. `reports/pln_csv_inspection.json` registra esquema/conteos de los CSV existentes sin copiar sus textos; Avilés continúa fuera del entrenamiento.

Origen: elaboración asistida propia mediante `scripts/build_demo.py` v1, publicada para reproducir el ejercicio bajo CC0-1.0. No contiene registros reales copiados, acceso municipal ni identidades operativas. 86 filas: 64 train, 8 functional y 14 challenge; ningún validation/test real. Grupo por original independiente, variantes futuras deben compartir ese grupo. Hash, método, versión y conteos: `data/demo_manifest.json` y `data/demo_particionado.manifest.json`.

Categorías exactamente C1–C8; desafíos sin tema llevan vacío. `validado=true` verifica coherencia funcional de las etiquetas elaboradas con la guía, no validación de dos personas. No existe kappa real calculado para este corpus. Es necesario recolectar y anotar independientemente datos reales antes de sostener rendimiento académico local.

Sesgos: textos limpios, problemas expresados con palabras evidentes y balance artificial de ocho clases. El predominio de la referencia por palabras clave en CV demuestra que el ejercicio facilita coincidencia léxica. No representa distribución, faltas ortográficas, bilingüismo ni prácticas de Juliaca. Los ejemplos en otras lenguas son pruebas del bloqueo heurístico, no validación lingüística.

Privacidad: ejemplos elaborados sin datos personales; corpus real pendiente de aprobación y revisión humana. CSV UTF-8 estable; conserva tildes y negaciones. Filas sin texto, IDs duplicados y grupos cruzados son inválidos. Duplicación cercana se detecta lexicalmente y requiere inspección humana de relaciones semánticas.

La fuente externa Avilés fue inspeccionada y quedó fuera del corpus. Otros recursos siguen pendientes/excluidos según `docs/datos_y_privacidad.md`. No presentar las metas ~800+100 como cantidades obtenidas. Recopilar test independiente local antes de ampliar entrenamiento; separar claramente resultados reales externos/locales de los elaborados.

Actualización: Valladolid fue inspeccionado desde la copia aportada por el usuario. Sus 202 296 filas no contienen textos libres, por lo que también quedó fuera del corpus. Se utiliza solo en análisis agregado y vista de fuentes; no se modificó el entrenamiento ni se generaron textos reales ficticios para completar clases.
