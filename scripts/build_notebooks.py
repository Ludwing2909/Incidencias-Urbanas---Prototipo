from pathlib import Path
import nbformat as nbf
ROOT=Path(__file__).resolve().parents[1]
directory=ROOT/'notebooks';directory.mkdir(exist_ok=True)
setup="""from pathlib import Path
import os, sys
# En Colab suba solo código y corpus anonimizado autorizado, nunca .env, bases o fuentes originales.
root = next((p for p in [Path.cwd(), *Path.cwd().parents, Path('/content/Proyecto_PLN')] if (p/'ml/cli.py').exists()), None)
assert root is not None, 'Sitúe el código del proyecto en el entorno primero'
os.chdir(root)
sys.path.insert(0, str(root))
print('Código local:', root)
"""
notebooks={
'01_exploracion.ipynb':[
nbf.v4.new_markdown_cell('# Exploración y control de datos\nLos ejemplos elaborados no acreditan rendimiento en Juliaca. No subir registros identificables a Colab. Instalar en una celda `%pip install -r /content/Proyecto_PLN/requirements.lock.txt` después de cargar código autorizado. Reiniciar el runtime si cambian dependencias.'),
nbf.v4.new_code_cell(setup),
nbf.v4.new_code_cell("from ml.data import validate, near_pairs\nframe = validate('data/demostracion.csv')\nframe.groupby(['tipo_dato','particion','categoria']).size().to_frame('n')"),
nbf.v4.new_code_cell("frame.assign(longitud=frame.texto_reclamo.str.len()).groupby('categoria').longitud.describe()"),
nbf.v4.new_code_cell("pairs = near_pairs(frame)\nprint('Pares cercanos para inspección:', len(pairs))\nprint('Grupos:', frame.grupo_origen.nunique())"),
nbf.v4.new_markdown_cell('Para datos reales, completar la adquisición, revisión de privacidad, doble anotación y adjudicación antes de validarlos. El 20 % mínimo de doble anotación se mide sobre textos distintos; todos los casos de test/desafío cuando sea viable. Usar `ml.data.agreement` antes de adjudicar. Tildes y negaciones se conservan; stopwords y corrección ortográfica no se adoptaron sin ablation en desarrollo.')],
'02_experimento.ipynb':[
nbf.v4.new_markdown_cell('# Comparación reproducible\nReutiliza módulos del proyecto. Demo: entrenamiento elaborado, sin validación/test reales; umbral nulo. No generar ejemplos con textos de validación o prueba.'),
nbf.v4.new_code_cell(setup),
nbf.v4.new_code_cell("from ml.data import split_data\nfrom ml.experiment import train, choose_threshold, evaluate\nfrom datetime import datetime, timezone\nrun = Path('reports/runs') / ('notebook-demo-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S'))\nsplit_data('data/demostracion.csv','data/notebook_demo.csv')"),
nbf.v4.new_code_cell("result = train('data/notebook_demo.csv',run,seed=42,demo=True)\nimport pandas as pd\npd.DataFrame(result['results'])"),
nbf.v4.new_code_cell("choose_threshold('data/notebook_demo.csv',run)"),
nbf.v4.new_code_cell("functional = evaluate('data/notebook_demo.csv',run,partition='functional')\nchallenge = evaluate('data/notebook_demo.csv',run,partition='challenge')\nprint('Casos funcionales elaborados:', functional['n'])\nprint('Casos desafío elaborados:', challenge['n'])"),
nbf.v4.new_markdown_cell('Para experimento real: `split_data` conserva primero un test marcado; entrenar con `demo=False`, ejecutar umbral una vez y test una vez. Comparar modo `real` e `hybrid` con desarrollo independiente y la misma prueba congelada. No seleccionar ni volver a ajustar con el test. Los JSON registran tamaños, parámetros, hashes, tiempos y versiones.')]
}
for filename,cells in notebooks.items():
    notebook=nbf.v4.new_notebook(cells=cells,metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python','version':'3.12'},'colab':{'name':filename}})
    nbf.validate(notebook);nbf.write(notebook,directory/filename)
print('Dos notebooks válidos; no se fabricaron salidas de celdas')
