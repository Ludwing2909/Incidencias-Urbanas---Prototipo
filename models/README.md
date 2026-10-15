# Artefactos confiables

`active.json` y `<version>.joblib` son salidas locales de `ml.cli activate`, excluyendo joblib de Git. Cargarlos requiere dependencias exactas e integridad SHA-256; solo artefactos propios. No hay subida de modelo por HTTP ni reentrenamiento al iniciar.

La demo activa está identificada `demonstration=true`, umbral null y sin evaluación local. Su presencia no habilita competencias. Reiniciar API tras activar/rollback. Historial en archive; scripts administrativos preservan versión anterior. Consulte docs/model_card y docs/operacion.
