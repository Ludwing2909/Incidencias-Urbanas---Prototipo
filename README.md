# Sistema de apoyo para la clasificación y derivación sugerida de incidencias ciudadanas mediante procesamiento de lenguaje natural en Juliaca

Prototipo académico ejecutable: React + FastAPI + PostgreSQL; inferencia TF-IDF con scikit-learn, revisión humana y auditoría. No es recepción municipal, verificación de veracidad, chatbot ni servicio de emergencias. Español e incidencias urbanas. No conecta con entidades reales.

El encargo adjunto es la especificación disponible; no se recibió un documento metodológico revisado independiente. La adaptación de Streamlit a React/FastAPI conserva el experimento en Python y separa la interfaz de la lógica. Véanse [arquitectura](docs/arquitectura.md), [metodología](docs/metodologia.md), [matriz de cumplimiento](docs/matriz_cumplimiento.md) y [verificación](docs/verificacion.md).

## Inicio en Windows PowerShell

**Nuevo: Proceso de PLN.** Abra `/pln` para analizar un mensaje sin registrar ni entrenar. El panel del personal incluye Datos y entrenamiento (reportes asociados por hash y consulta de candidatos) y análisis/aclaraciones/relaciones en el detalle. `/pln/mejoras` muestra capacidades A–L y dependencias. Actualice la base a la migración 0002 antes de arrancar. [Manual y guía docente](docs/proceso_pln.md), [contratos](docs/contratos_pln.md) y [matriz de requisitos](docs/matriz_pln.md). El índice de relacionados se construye fuera de HTTP con `python -m scripts.build_related_index`. La búsqueda experimental adicional usa `ml.cli train ... --demo --expanded`, sin activación automática. El modelo activo sigue demo-v3 (LinearSVC calibrado); los resultados nuevos están separados.

Requiere Python **3.12 de python.org**, Node **22.12 o posterior** (verificado con 24.11), y opcionalmente Docker Desktop con motor Linux iniciado. Ejecute desde la raíz del proyecto:

```powershell
python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
& .\scripts\init_env.ps1
& .\.venv\Scripts\python.exe -m alembic upgrade head
& .\.venv\Scripts\python.exe -m backend.manage seed-rules
& .\.venv\Scripts\python.exe -m backend.manage create-user --username admin-demo --role administrador
& .\.venv\Scripts\python.exe -m backend.manage create-user --username revisor-demo --role revisor
npm.cmd ci --prefix frontend
```

Los comandos de usuario piden una contraseña de al menos 12 caracteres por entrada oculta. No existen contraseñas fijas. `init_env.ps1` genera secretos aleatorios y conserva un `.env` existente. No versionar `.env`. En esta entrega ya existe el entorno local preparado; no es necesario repetir creación del entorno o de secretos. El `.env.example` selecciona SQLite para una demostración individual; Docker Compose usa PostgreSQL. Las dos bases no son equivalentes en concurrencia ni operación.

La demostración local ya tiene los usuarios `admin-demo` y `revisor-demo`, creados explícitamente con `python -m scripts.setup_demo`. Sus contraseñas aleatorias están únicamente en `.env` bajo `DEMO_ADMIN_PASSWORD` y `DEMO_REVIEWER_PASSWORD`; consúltelas localmente. Ese comando no modifica cuentas existentes ni funciona contra PostgreSQL. En otra instalación puede usar este comando en vez de los dos `create-user` anteriores. No reutilizar esas contraseñas ni ese procedimiento como aprovisionamiento de producción.

En dos terminales:

```powershell
& .\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --no-access-log
```

```powershell
npm.cmd run dev --prefix frontend
```

Abra [interfaz](http://127.0.0.1:5173) y [contratos OpenAPI](http://127.0.0.1:8000/docs). Vite sirve la UI y reenvía `/api` al backend. Las fechas se almacenan en UTC y se muestran en America/Lima.

## Demostración reproducible

`data/demostracion.csv` contiene **86 textos elaborados**: 64 de entrenamiento, 8 funcionales y 14 desafíos; cero textos reales. El generador y el manifiesto identifican el método y su versión. `validado=true` significa coherencia de estas fixtures con la guía, no anotación independiente por personas. La interfaz distingue el modelo demostrativo. No se han completado cuotas con duplicados.

Use un nombre nuevo para cada ejecución; nunca sobrescriba resultados:

```powershell
& .\.venv\Scripts\python.exe -m scripts.build_demo
& .\.venv\Scripts\python.exe -m ml.cli validate data/demostracion.csv
& .\.venv\Scripts\python.exe -m ml.cli split data/demostracion.csv data/demo_particionado.csv
& .\.venv\Scripts\python.exe -m ml.cli train data/demo_particionado.csv reports/runs/mi-demo-01 --demo
& .\.venv\Scripts\python.exe -m ml.cli threshold data/demo_particionado.csv reports/runs/mi-demo-01
& .\.venv\Scripts\python.exe -m ml.cli evaluate data/demo_particionado.csv reports/runs/mi-demo-01 --partition functional
& .\.venv\Scripts\python.exe -m ml.cli evaluate data/demo_particionado.csv reports/runs/mi-demo-01 --partition challenge
& .\.venv\Scripts\python.exe -m ml.cli activate reports/runs/mi-demo-01
& .\.venv\Scripts\python.exe -m ml.cli predict 'La luminaria del barrio no enciende durante la noche.'
```

La calibración sigmoide se ejecuta durante `train` con pliegues explícitos por grupos del entrenamiento. `threshold` congela la decisión; sin validación real adecuada establece umbral nulo. Todas las sugerencias demo requieren revisión por ese motivo y por reglas no validadas. La API carga el artefacto una vez: reiníciela después de activarlo. No se reentrena al iniciar ni al corregir casos.

El modelo activo y los reportes ejecutados se conservan localmente en `models/` y `reports/runs/` y están excluidos de Git por tamaño y trazabilidad de datos. Los scripts los reproducen. El registro también funciona sin artefacto: tema y puntuación nulos, motivo explícito y revisión humana.

## Datos reales y experimento

El archivo de Valladolid `682291-D0072-2020.csv` proporcionado posteriormente fue inspeccionado: **202 296 registros estructurados y ninguna descripción libre**. Se aprovechó para análisis descriptivo y una nueva vista **Personal → Fuentes de datos**, con conteos, cobertura temática orientativa y exclusiones. No se utiliza para entrenar ni evaluar el modelo: `peticion` es un ID y `tema` una etiqueta administrativa. [Informe y procedimiento](docs/dataset_valladolid.md).

```powershell
& .\.venv\Scripts\python.exe -m ml.source_import 'C:\Users\Usuario\Downloads\682291-D0072-2020.csv'
```

El comando deja cuatro tablas agregadas en `reports/sources/valladolid_2020/` y un manifiesto con hash. No modifica el original ni exporta identificadores/coordenadas. La API debe reiniciarse para incorporar su nueva ruta. La licencia general publicada por el portal es CC BY 3.0 ES salvo indicación específica contraria; la atribución está en el informe. El mapeo administrativo no es anotación validada ni evidencia local de Juliaca.

Primero lea [adquisición y privacidad](docs/datos_y_privacidad.md), [guía de anotación](docs/anotacion.md) y [diccionario](docs/diccionario_datos.md). Las fuentes candidatas y sus intentos de inspección están en `config/sources.json` y `reports/source_inspection.json`. No se incorporaron registros de terceros al entrenamiento.

```powershell
& .\.venv\Scripts\python.exe -m scripts.inspect_sources
# Guardar originales restringidos fuera de Git; revisar permiso antes de reutilizar.
& .\.venv\Scripts\python.exe -m ml.cli prepare data/private/autorizado.csv data/processed/redactado.csv
# Revisar manualmente privacidad, etiquetas y grupos; después marcar validado=true.
& .\.venv\Scripts\python.exe -m ml.cli agreement data/processed/doble_anotacion.csv
& .\.venv\Scripts\python.exe -m ml.cli validate data/processed/corpus.csv
& .\.venv\Scripts\python.exe -m ml.cli split data/processed/corpus.csv data/processed/particionado.csv
& .\.venv\Scripts\python.exe -m ml.cli train data/processed/particionado.csv reports/runs/real-v1 --mode real
& .\.venv\Scripts\python.exe -m ml.cli threshold data/processed/particionado.csv reports/runs/real-v1
& .\.venv\Scripts\python.exe -m ml.cli evaluate data/processed/particionado.csv reports/runs/real-v1
```

Reserve primero los casos reales independientes marcándolos `test`. Grupos y variantes no cruzan particiones. `split` aplica aproximadamente 60/20/20 cuando existen grupos suficientes y no hay test previamente reservado; con test reservado deja 80/20 del desarrollo restante. No preserva estratificación temporal automáticamente: para prueba temporal/local reservada marque sus grupos antes de ejecutar. El validador falla ante grupos compartidos, duplicados exactos/cercanos o datos elaborados en validación/test. CV falla con mensaje si faltan grupos por clase.

Comparar solo real con híbrido exige otra ejecución `--mode hybrid`, la misma prueba reservada y selección independiente dentro de entrenamiento. Congelar previamente la comparación; no decidir repetir por resultados del test. La activación de candidatos reales requiere el reporte de prueba. El operador debe revisar resultados y limitaciones antes de activar; el sistema no aplica un criterio automático de calidad municipal.

## Uso ciudadano y personal

1. Registrar una descripción y ubicación general opcional, sin identidades ni domicilios exactos.
2. Guardar el código `REC-AAAA-00001` y el secreto mostrado en la confirmación. El código no es una credencial. Conservar el secreto fuera de URLs y logs.
3. Consultar seguimiento con ambos valores. La respuesta pública muestra únicamente estados y fechas.
4. Entrar en Personal con el usuario creado explícitamente, abrir Bandeja y revisar el caso.
5. Confirmar/corregir tema y destino con motivo obligatorio. Se conserva la predicción y el historial; el caso pasa a Revisado.
6. Un administrador puede confirmar Derivado/Resuelto con evidencia de una actuación humana. En la demo use referencias académicas; no simule aceptación municipal real.

## Docker Compose (PostgreSQL)

Inicie Docker Desktop. `.env` debe contener secretos propios; el archivo generado cumple ese requisito.

```powershell
docker compose config --quiet
docker compose up --build -d
docker compose exec api python -m backend.manage seed-rules
docker compose exec api python -m backend.manage create-user --username admin-demo --role administrador
docker compose ps
```

Abra [prototipo Docker](http://localhost:8080). El puerto publicado se limita a loopback; la API y PostgreSQL se comunican dentro de Compose. Migraciones al arrancar, health checks y volumen persistente `postgres_data`. `docker compose down` conserva datos. No usar `down -v` si necesita conservarlos.

Para un piloto configure HTTPS, `COOKIE_SECURE=true`, dominios CORS explícitos y política de conservación aprobada. No despliegue este prototipo en una entidad sin autorización y revisión institucional. [Operación y respaldo](docs/operacion.md) incluye PostgreSQL, SQLite, rollback y eliminación controlada.

## Verificación

```powershell
& .\.venv\Scripts\python.exe -m pytest --junitxml=reports/pytest.xml
npm.cmd run build --prefix frontend
Push-Location frontend
npx.cmd playwright install chromium
npm.cmd run test:integration
Pop-Location
& .\.venv\Scripts\python.exe -m scripts.export_contract
```

Playwright inicia una API y una UI reales sobre una base de pruebas aislada; cierre antes servidores que usen 8000/5173. El usuario `test-admin` / `Test-password-123!` existe solo en esa base de pruebas y nunca se crea en la base operativa. Elimina esa base siguiendo el procedimiento de pruebas si quiere empezar limpio. El bloqueo Python congela dependencias transitivas; npm conserva integridad en `package-lock.json`. Para regenerar Python en un entorno normal use `python -m pip freeze > requirements.lock.txt` y revise el diff. No actualizar dependencias silenciosamente.

## Estructura

`frontend/` interfaz y pruebas de navegador; `backend/` API, seguridad y migraciones; `ml/` datos, experimentación e inferencia; `notebooks/` exploración y experimento compatibles con Colab; `config/` taxonomía, palabras clave, reglas y fuentes; `tests/` contratos/ML/persistencia; `docs/` protocolos y manuales; `reports/` evidencias; `models/` artefactos locales; `data/` plantilla y ejemplos propios; `scripts/` comandos reproducibles.

Pendientes externos concretos: corpus local autorizado, doble anotación independiente, revisión lingüística local, evaluación real de Juliaca, competencias documentadas vigentes y aprobación de un piloto. Los resultados demo no sustituyen ninguno de ellos.
