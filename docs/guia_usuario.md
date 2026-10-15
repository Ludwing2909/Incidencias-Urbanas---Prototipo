# Guía de usuario

Nuevo apartado **Proceso de PLN**: `/pln` permite analizar un ejemplo editable sin registrar. Muestra preparación protegida, características conocidas/desconocidas, pesos TF-IDF, estimador, revisión y reglas de destino. `/pln/mejoras` presenta las capacidades A–L. **Datos y entrenamiento** está dentro del panel del personal y permite consultar el modelo activo o candidatos sin activarlos. En el detalle del caso puede guardar análisis, responder preguntas pendientes, corregir campos extraídos y consultar relacionados; cada actuación conserva historial y original. El índice de relaciones se construye offline y puede estar ausente/desactualizado. Ninguna relación fusiona casos. Manual ampliado y guion docente: `proceso_pln.md`.

Inicio explica ocho temas y el alcance académico. En Registrar describa un problema principal en español, hasta 3000 caracteres, sin datos personales. Se permite ubicación general de hasta 180 caracteres. Vacíos/espacios o tamaños excesivos se rechazan; textos breves se registran para revisión, sin inventar certeza.

Confirmación muestra código, secreto y clasificación orientativa. Guarde el secreto ahora en lugar privado; si se pierde no existe recuperación pública. Nunca coloque secreto en URL. Tema sugerido y destino orientativo aparecen separados; una puntuación calibrada no verifica competencia. Un margen del estimador se etiqueta como margen, sin porcentaje de confianza. Modelo ausente muestra tema/puntuación no disponibles. Demo se identifica explícitamente.

Seguimiento solicita código y secreto por POST y solo devuelve estado/fechas. No expone descripción, destino interno, observaciones, usuario ni evidencia. Ante error se responde igual para caso inexistente o secreto incorrecto. Después de demasiados intentos espere diez minutos.

Personal inicia sesión con usuarios creados explícitamente. Roles: revisor consulta/revisa casos; administrador además versiona reglas y confirma actuaciones Derivado/Resuelto. Los permisos se verifican en backend. Resumen usa conteos reales y no rellena vacíos. Bandeja ofrece código, tema, estado y paginación. En Detalle se muestra texto autorizado, predicción original, revisión, prioridad y versiones.

Si abre una ruta del panel sin sesión o con sesión expirada, se muestra automáticamente Acceso del personal y se conserva la página solicitada. Tras autenticarse vuelve a ella, por ejemplo Fuentes de datos. Un fallo de conexión/servicio se muestra con Reintentar en la página original; no se confunde con falta de sesión. En la demo local el usuario `admin-demo` usa la contraseña aleatoria guardada en `.env` como `DEMO_ADMIN_PASSWORD` (consúltela localmente; no se publica en la interfaz).

Confirmar/corregir tema y destino requiere motivo de al menos 8 caracteres significativos y la versión del caso. Si otro revisor actuó, el sistema informa conflicto; recargue y considere su actuación. La predicción no se pierde. El caso pasa a Revisado. Para reabrir, registrar transición a Pendiente de revisión con motivo. Una clasificación no produce Derivado ni Resuelto: esos estados requieren administrador, confirmación humana y evidencia. Solo se permite Revisado→Derivado→Resuelto; no saltar etapas.

Reglas muestran validación, fechas y versiones; el administrador edita creando una versión nueva. Texto de condiciones admitido automáticamente: `incidencia urbana`; otras condiciones quedan en revisión hasta implementar una evaluación documentalmente contrastada. Ámbito aplicable: `Juliaca urbana` o ubicación general exacta normalizada; reglas múltiples ambiguas no se eligen. C7/C8 requieren revisión aun con regla validada.

Modelo/experimentos muestran disponibilidad, carácter demo, manifiesto, parámetros y métricas reales de CV. Entrenamiento/activación no están expuestos en el panel. Consulte los reportes de test/desafíos y las limitaciones antes de interpretar métricas. Cierre sesión al terminar; expira después de ocho horas y se revoca en logout.


## Prioridad alta, media o baja

Los nuevos análisis y registros incluyen prioridad sugerida, motivo y fragmentos de evidencia. Reglas priority-rules-v1: alta ante riesgo explícito para personas o interrupción esencial; media ante fallos de servicio/problemas persistentes; baja ante mantenimiento/mejoras sin riesgo descrito. Falta de evidencia suficiente: media provisional, requiere revisión. Se consideran negaciones próximas a las señales; la heurística tiene límites y no constituye detección de emergencias validada. Es independiente de TF-IDF y de la probabilidad temática. Los registros anteriores conservan su evaluación histórica y muestran prioridad no clasificada si no tenían los tres niveles. Se eliminó la franja superior y la referencia Laboratorio PLN del logotipo; el pie queda simplificado.
