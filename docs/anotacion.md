# Guía de anotación v1

Lea el texto sin predicciones, destino anterior ni estado. Asigne el problema dominante, no el lugar donde ocurre. Si no hay tema dominante, conserve el desafío sin tema y motive revisión. No decida veracidad, competencia ni urgencia a partir de la categoría.

| Tema | Incluye | Excluye / frontera |
|---|---|---|
| C1 Limpieza pública y residuos sólidos | Recojo, acumulación de basura, barrido, contenedores | Basura en parque es C1 si dominante; mantenimiento vegetal es C5 |
| C2 Infraestructura urbana y drenaje pluvial | Baches, veredas, pavimento, canales/sumideros de lluvia | Semáforos/señalización C3; fuga de agua/red sanitaria C8 |
| C3 Transporte, tránsito y seguridad vial | Señales, semáforos, circulación, paraderos y cruces | Deterioro físico de pista/vereda C2 |
| C4 Seguridad ciudadana y Serenazgo | Vigilancia, robos, amenazas, agresión | No confirma delito ni urgencia; la prioridad se anota aparte |
| C5 Parques, áreas verdes y ornato | Poda, riego vegetal, jardines, bancas y juegos | Residuos como problema principal C1; iluminación C7 |
| C6 Comercio y fiscalización municipal | Puestos, ocupación comercial, higiene del comercio | Trámite de licencia/reclamo administrativo fuera del alcance |
| C7 Alumbrado público | Luminarias/farolas/postes de iluminación pública | Electricidad privada o facturación fuera de alcance; competencia siempre revisión |
| C8 Agua y alcantarillado | Fugas, servicio de agua, tuberías/red de desagüe sanitario | Drenaje de lluvia C2; reclamo formal de facturación fuera del alcance; competencia siempre revisión |

R9 no es etiqueta de entrenamiento ni oficina. Un desafío puede tener C8 y requerir aclaración/competencia. Ejemplo: fuga de agua que dañó una vereda puede ser C8 si la fuga domina; dos problemas sin prioridad requieren revisión. Las heurísticas de producción no determinan la etiqueta de referencia.

Dos personas etiquetan independientemente al menos 20 % del corpus; seleccione esa muestra por clases/fuentes/grupos antes de anotar. Todos los test y desafíos se doble anotan cuando sea viable; registre omisiones y razón. Con ~800 clasificables y ~100 desafíos la meta es de planificación, no suficiencia estadística. No duplicar textos para equilibrar cuotas.

Procedimiento: capacitación con ejemplos ajenos a test; versión de guía congelada; anotaciones separadas; ejecutar acuerdo porcentual y kappa; revisar desacuerdos con tercera persona/adjudicación consensuada, registrando motivo. No sustituir referencias por predicciones. Si el acuerdo es bajo, revisar límites en desarrollo y nueva anotación, conservando registro de versiones. No inspeccionar test para cambiar palabras clave o parámetros del modelo.

Los 86 ejemplos entregados se elaboraron de forma asistida y sus etiquetas se comprobaron contra esta guía dentro del desarrollo; no fueron etiquetados por dos personas ni revisados lingüísticamente en Juliaca. Esa limitación aparece en dataset card y manifiesto. Evite convertir palabras estereotipadas en evaluación real; recupere expresiones locales autorizadas y revise su diversidad con hablantes competentes.
