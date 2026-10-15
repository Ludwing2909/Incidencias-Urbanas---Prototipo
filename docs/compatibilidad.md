# Versiones y documentación contrastada

Directas Python fijadas en `requirements.in`; transitivas resueltas realmente en Python 3.12.14 y congeladas en `requirements.lock.txt`. No se inventó resolución ni salida de instalaciones. Frontend usa versiones exactas y `package-lock.json` generado por npm. Vite 6.4.4, React 19.0.0, React Router 7.18.4, Tailwind/plugin Vite 4.1.4, TypeScript 5.8.3 y Playwright 1.64.0; instalación y build verificados con Node 24.11.0. Imágenes Compose fijan Python 3.12.10, Node 22.14.0, PostgreSQL 16.8 y Nginx 1.27.5; verificación de ejecución depende del motor Docker.

| Decisión | Fuente primaria consultada |
|---|---|
| Vite 6 y Node compatible; SPA con plugin React | [Vite 6: guía](https://v6.vite.dev/guide/) |
| Tailwind 4 mediante plugin, sin configuración de Tailwind 3 | [Tailwind: instalación Vite](https://tailwindcss.com/docs/installation/using-vite) |
| React Router en modo declarativo, sin plugin/framework innecesario | [React Router: instalación declarativa](https://reactrouter.com/start/declarative/installation) |
| FastAPI/Pydantic 2 y contenedor Python propio | [FastAPI: contenedores](https://fastapi.tiangolo.com/deployment/docker/) |
| Calibración sigmoide y CV iterable explícito | [scikit-learn 1.6.1: CalibratedClassifierCV](https://scikit-learn.org/1.6/modules/generated/sklearn.calibration.CalibratedClassifierCV.html) |
| Partición estratificada por grupos | [scikit-learn: validación cruzada](https://scikit-learn.org/1.6/modules/cross_validation.html) |
| Incrementos transaccionales PostgreSQL | [SQLAlchemy 2: ON CONFLICT](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#insert-on-conflict-upsert) |

La primera auditoría npm encontró vulnerabilidades en Vite/React Router/Playwright; se actualizaron a versiones corregidas dentro de la familia compatible. La instalación corregida reportó cero vulnerabilidades. Esto es una consulta puntual, no garantía permanente. No migrar a versiones mayores sin nueva resolución y verificación. Una advertencia de deprecación AnyIO/Starlette quedó registrada en pytest; no afectó las pruebas.
