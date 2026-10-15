# Operación y seguridad

Credenciales creadas con `backend.manage create-user`; contraseñas Argon2id, nunca en argumentos ni repositorio. Roles revisor/administrador comprobados en cada ruta. Sesión aleatoria 256 bits, hash en DB, ocho horas, revocable, cookie HttpOnly/SameSite=Strict, Secure activable para HTTPS. Mutaciones del personal exigen token CSRF asociado a la sesión. CORS permite solo orígenes configurados. Los secretos `.env` quedan externos al repositorio. Conservar APP_SECRET estable; rotarlo invalida sesiones, consulta e idempotencia existentes, por lo que exige plan de migración y no debe hacerse accidentalmente.

Consulta y login: 15 y 10 intentos por ventana de diez minutos e IP del socket; registro 40. El contador está en la base y es compartido entre procesos. No se confía en cabeceras de IP suministradas por usuario. En Compose el proxy comparte IP y, por tanto, ese límite es conservador para todas las personas; antes de un piloto configurar identidad de proxy verificada y estrategia de límites, sin abrir confianza en X-Forwarded-For arbitrario. `purge-sessions-and-limits` limpia sesiones expiradas y reinicia límites durante mantenimiento. No es protección completa contra abuso distribuido.

El código REC es público; secreto de seguimiento deriva de clave aleatoria de idempotencia y APP_SECRET, se guarda solo hash, se envía por POST y no en logs. Respuesta indistinguible ante credenciales de consulta incorrectas. API no guarda descripción original sin redacción preliminar, pero nombres/domicilios residuales pueden existir. Minimización y revisión humana siguen pendientes para datos reales. Logs de acceso están desactivados en instrucciones/Compose; no habilitar logging de cuerpos o secretos. React escapa texto y Nginx define política de contenido. Consultas parametrizadas y tamaños Pydantic controlados; ninguna carga web de modelos.

## Copia y restauración PostgreSQL

Use un directorio local autorizado excluido de Git. El formato custom evita alteración de binarios por redirección de PowerShell. El rol/destino proceden de `.env` dentro del contenedor, sin imprimir secretos:

```powershell
New-Item -ItemType Directory -Path backups -Force
docker compose exec db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc -f /tmp/incidencias.dump'
$dbContainer = docker compose ps -q db
docker cp "${dbContainer}:/tmp/incidencias.dump" .\backups\incidencias.dump
```

Restauración sobre una base **vacía de prueba** o un entorno recuperado; no ejecutar sobre datos que necesite conservar:

```powershell
$dbContainer = docker compose ps -q db
docker cp .\backups\incidencias.dump "${dbContainer}:/tmp/incidencias.restore"
docker compose exec db sh -c 'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner /tmp/incidencias.restore'
```

Comprobar esquema, conteos, seguimiento y roles tras restaurar. La prueba de copia/recuperación real debe completarse antes del piloto. No se declara ejecutada si no hay motor Docker activo. No añadir --clean sin un plan de recuperación aprobado. Respaldar también APP_SECRET en un gestor autorizado y manifiesto/artefacto propio; un dump sin APP_SECRET no conserva acceso de seguimiento.

SQLite individual: cerrar escritores y usar `sqlite3.Connection.backup`, no copiar únicamente `.db` durante WAL activo. Comando `python -m scripts.sqlite_backup demo.db backups/demo.db`. No es copia PostgreSQL ni prueba de equivalencia. Mantener versiones y permisos de respaldos conforme al plazo aprobado.

## Versiones y rollback

`ml.cli activate reports/runs/<candidato>` comprueba integridad y umbral congelado. Candidato real requiere evaluación independiente; operador revisa métricas/limitaciones. Conserva activo anterior en `models/archive/<UTC>/`, copia artefacto bajo nombre de versión y reemplaza manifiesto atómicamente. Reiniciar procesos API para cargar. Rollback: `python -m scripts.rollback_model models/archive/<UTC>` y reiniciar API. No modifica predicciones históricas ni correcciones.

Corregir datos: exportación manual autorizada de revisiones sin identidades; doble anotación/adjudicación; nueva versión de corpus y manifiesto; entrenamiento explícito; nueva evaluación independiente; activación tras revisión humana. Nunca usar predicciones como etiqueta de referencia ni seleccionar nuevas versiones mirando indefinidamente el mismo test. Auditoría DB no es registro resistente a administradores de DB: para entorno institucional definir controles de custodia/inmutabilidad.

Eliminación: decidir plazo y derechos antes de recopilar. Procedimiento bajo custodio: listar IDs autorizados, respaldar si la política lo permite, eliminar referencias relacionadas y caso mediante transacción revisada, registrar constancia sin contenido identificable, propagar a respaldos conforme a su política. Este MVP no expone borrado masivo público. No eliminar todo un volumen por rutina.
