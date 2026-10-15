"""Informe Word académico; ejecutar con el Python de dependencias de Codex."""
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/Informe_proyecto_PLN_Juliaca_APA7.docx'
QA=ROOT/'docs/.qa_informe'
TITLE='Sistema de apoyo para la clasificación y derivación sugerida de incidencias ciudadanas mediante procesamiento de lenguaje natural en Juliaca'
QA.mkdir(parents=True,exist_ok=True)
experiment=json.loads((ROOT/'reports/runs/demo-v3/experiment.json').read_text(encoding='utf-8'))
functional=json.loads((ROOT/'reports/runs/demo-v3/functional_evaluation.json').read_text(encoding='utf-8'))
challenge=json.loads((ROOT/'reports/runs/demo-v3/challenge_evaluation.json').read_text(encoding='utf-8'))
expanded=json.loads((ROOT/'reports/runs/pln-expanded-demo-20261014/experiment.json').read_text(encoding='utf-8'))
expanded_functional=json.loads((ROOT/'reports/runs/pln-expanded-demo-20261014/functional_evaluation.json').read_text(encoding='utf-8'))
expanded_challenge=json.loads((ROOT/'reports/runs/pln-expanded-demo-20261014/challenge_evaluation.json').read_text(encoding='utf-8'))
source=json.loads((ROOT/'reports/sources/valladolid_2020.json').read_text(encoding='utf-8'))
browser=json.loads((ROOT/'reports/playwright.json').read_text(encoding='utf-8'))
base_tests=ET.parse(ROOT/'reports/pytest.xml').getroot()[0].attrib
data_tests=ET.parse(ROOT/'reports/pytest_dataset.xml').getroot()[0].attrib
categories=json.loads((ROOT/'config/categories.json').read_text(encoding='utf-8'))['categories']

def font(size,bold=False):
    return ImageFont.truetype('C:/Windows/Fonts/timesbd.ttf' if bold else 'C:/Windows/Fonts/times.ttf',size)

def centered(draw,box,lines,size=36):
    x0,y0,x1,y1=box
    step=size*1.2
    y=(y0+y1)/2-len(lines)*step/2
    for line in lines:
        f=font(size)
        width=draw.textlength(line,font=f)
        draw.text(((x0+x1-width)/2,y),line,font=f,fill='black');y+=step

def diagram():
    image=Image.new('RGB',(1800,1150),'white');d=ImageDraw.Draw(image)
    boxes={
        'ui':((40,130,430,310),['React y TypeScript','Ciudadanía y personal']),
        'api':((570,130,970,310),['FastAPI y Pydantic','Contratos y permisos']),
        'db':((1330,130,1750,310),['Registro y auditoría','PostgreSQL o SQLite']),
        'policy':((550,500,990,705),['Revisión y competencia','Tema y destino separados']),
        'model':((1300,500,1770,705),['Pipeline calibrado','Texto anonimizado']),
        'data':((40,890,480,1080),['Datos autorizados','Grupos y particiones']),
        'train':((640,890,1150,1080),['Experimentación administrativa','CV y calibración por grupos']),
        'artifact':((1330,890,1760,1080),['Modelo versionado','Manifiesto y hash'])}
    for rect,lines in boxes.values():d.rounded_rectangle(rect,14,fill='#f5f5f5',outline='black',width=3);centered(d,rect,lines,34)
    def arrow(points):
        d.line(points,fill='black',width=4)
        (px,py),(x,y)=points[-2:]
        if x==px:
            v=1 if y>py else -1; triangle=[(x,y),(x-12,y-v*20),(x+12,y-v*20)]
        else:
            v=1 if x>px else -1;triangle=[(x,y),(x-v*20,y-12),(x-v*20,y+12)]
        d.polygon(triangle,fill='black')
    for points in [[(430,220),(570,220)],[(970,220),(1330,220)],[(770,310),(770,500)],[(990,603),(1300,603)],[(480,985),(640,985)],[(1150,985),(1330,985)],[(1545,890),(1545,705)]]:arrow(points)
    d.text((80,45),'Flujo de aplicación',font=font(38,True),fill='black')
    d.text((80,790),'Flujo experimental separado de las peticiones HTTP',font=font(38,True),fill='black')
    image.save(QA/'arquitectura.png')

def comparison():
    image=Image.new('RGB',(1800,1000),'white');d=ImageDraw.Draw(image)
    names={'dummy':'Clase mayoritaria','keywords':'Palabras clave','logistic':'Regresión logística','svc':'LinearSVC','nb':'Naive Bayes'}
    left,right,top=510,1620,90
    for x in range(6):
        px=left+x/5*(right-left)
        d.line((px,top,px,865),fill='#d9d9d9',width=2)
        d.text((px-25,895),f'{x/5:.1f}',font=font(28),fill='black')
    for i,row in enumerate(experiment['results']):
        y=125+i*145;v=row['cv_macro_f1']
        d.text((35,y+15),names[row['model']],font=font(34),fill='black')
        d.rectangle((left,y,left+v*(right-left),y+70),fill='#3d3d3d' if row['model']=='keywords' else '#838383')
        d.text((left+v*(right-left)+15,y+15),f'{v:.3f}',font=font(32),fill='black')
    d.text((700,953),'Macro F1 de validación cruzada',font=font(32),fill='black')
    image.save(QA/'comparacion.png')

diagram();comparison()
doc=Document()
sec=doc.sections[0]
sec.page_width=Inches(8.5);sec.page_height=Inches(11)
sec.top_margin=sec.bottom_margin=sec.left_margin=sec.right_margin=Inches(1)
sec.header_distance=Inches(.5)
for name in ['Normal','Title','Subtitle','Heading 1','Heading 2','Heading 3','Caption','TOC 1','TOC 2']:
    if name not in doc.styles:continue
    s=doc.styles[name];s.font.name='Times New Roman';s.font.size=Pt(12);s.font.color.rgb=RGBColor(0,0,0)
    s.paragraph_format.space_before=Pt(0);s.paragraph_format.space_after=Pt(0);s.paragraph_format.line_spacing=2
    s.paragraph_format.first_line_indent=Inches(.5) if name=='Normal' else Inches(0)
    s.paragraph_format.widow_control=True
    if name.startswith('Heading'):
        s.font.bold=True;s.paragraph_format.keep_with_next=True
        s.paragraph_format.alignment=WD_ALIGN_PARAGRAPH.CENTER if name=='Heading 1' else WD_ALIGN_PARAGRAPH.LEFT
doc.styles['Title'].font.bold=True
doc.styles['Title'].paragraph_format.alignment=WD_ALIGN_PARAGRAPH.CENTER
# La plantilla base incluye fuentes de tema y un borde en Title; eliminarlos
# evita reglas azules y fuentes distintas a las indicadas por APA.
for style in doc.styles:
    for border in style.element.xpath('.//w:pBdr'):
        border.getparent().remove(border)
    for fonts in style.element.xpath('.//w:rFonts'):
        for attribute in ['asciiTheme','hAnsiTheme','csTheme','eastAsiaTheme']:
            fonts.attrib.pop(qn('w:'+attribute),None)
lang=OxmlElement('w:lang');lang.set(qn('w:val'),'es-PE');doc.styles['Normal'].element.get_or_add_rPr().append(lang)
header=sec.header.paragraphs[0];header.alignment=WD_ALIGN_PARAGRAPH.RIGHT
header.paragraph_format.first_line_indent=Inches(0)
field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');header._p.append(field)
doc.core_properties.title=TITLE
doc.core_properties.subject='Informe académico y documentación técnica del prototipo'
doc.core_properties.author=''
doc.core_properties.last_modified_by=''

def p(text,indent=True):
    para=doc.add_paragraph(text)
    if not indent:para.paragraph_format.first_line_indent=Inches(0)
    return para

def h(text,level=1):return doc.add_heading(text,level)
def page():doc.add_page_break()
def caption(number,title,kind='Tabla'):
    para=p('',False);para.paragraph_format.keep_with_next=True
    para.add_run(f'{kind} {number}').bold=True
    title_p=p('',False);title_p.add_run(title).italic=True;title_p.paragraph_format.keep_with_next=True

def table(headers,rows,widths):
    t=doc.add_table(rows=1,cols=len(headers));t.alignment=WD_TABLE_ALIGNMENT.CENTER;t.autofit=False
    for i,width in enumerate(widths):t.columns[i].width=Inches(width)
    for i,label in enumerate(headers):t.rows[0].cells[i].text=label
    repeat=OxmlElement('w:tblHeader');t.rows[0]._tr.get_or_add_trPr().append(repeat)
    for values in rows:
        cells=t.add_row().cells
        for cell,value in zip(cells,values):cell.text=str(value)
    props=t._tbl.tblPr
    borders=OxmlElement('w:tblBorders')
    for edge in ['top','left','bottom','right','insideH','insideV']:
        b=OxmlElement('w:'+edge);b.set(qn('w:val'),'single' if edge in ['top','bottom'] else 'nil');b.set(qn('w:sz'),'6');b.set(qn('w:color'),'000000');borders.append(b)
    props.append(borders)
    for i,row in enumerate(t.rows):
        trpr=row._tr.get_or_add_trPr();avoid=OxmlElement('w:cantSplit');trpr.append(avoid)
        for j,cell in enumerate(row.cells):
            cell.width=Inches(widths[j]);cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            tcpr=cell._tc.get_or_add_tcPr()
            margins=OxmlElement('w:tcMar')
            for edge in ['top','left','bottom','right']:
                m=OxmlElement('w:'+edge);m.set(qn('w:w'),'85');m.set(qn('w:type'),'dxa');margins.append(m)
            tcpr.append(margins)
            if i==0:
                header_border=OxmlElement('w:tcBorders');bottom=OxmlElement('w:bottom');bottom.set(qn('w:val'),'single');bottom.set(qn('w:sz'),'6');bottom.set(qn('w:color'),'000000');header_border.append(bottom);tcpr.append(header_border)
            for para in cell.paragraphs:
                para.paragraph_format.first_line_indent=Inches(0);para.paragraph_format.line_spacing=1.15
                para.paragraph_format.space_after=Pt(2)
                if j==0 and widths[j]<1.1:para.alignment=WD_ALIGN_PARAGRAPH.CENTER
                for run in para.runs:run.font.size=Pt(10);run.font.bold=i==0
    p('',False).paragraph_format.line_spacing=1
    return t

def note(text):
    para=p('',False);para.paragraph_format.line_spacing=1.5
    para.add_run('Nota. ').italic=True;para.add_run(text)

def picture(path,width=6.4):
    para=p('',False);para.alignment=WD_ALIGN_PARAGRAPH.CENTER
    run=para.add_run();run.add_picture(str(path),width=Inches(width))
    for item in run._r.iter(qn('wp:docPr')):item.set('descr',Path(path).stem.replace('_',' '))

def code(lines):
    for line in lines:
        para=p('',False);para.paragraph_format.line_spacing=1.15
        para.paragraph_format.space_after=Pt(5)
        run=para.add_run(line);run.font.name='Consolas';run.font.size=Pt(9)

# Portada de trabajo estudiantil APA 7.
title=doc.add_paragraph(TITLE,style='Title');title.paragraph_format.space_before=Pt(72)
p('',False)
for text in ['Autor o autores ______________________________','Universidad Nacional del Altiplano','Procesamiento de Lenguaje Natural','Docente ______________________________','14 de octubre de 2026']:
    para=p(text,False);para.alignment=WD_ALIGN_PARAGRAPH.CENTER
page()
h('Resumen')
p('Se desarrolló y amplió un prototipo académico que sugiere temas y prioridades para incidencias urbanas en español y apoya su revisión humana en Juliaca. Integra React, FastAPI, SQLAlchemy y un clasificador TF-IDF calibrado. La nueva sección Proceso de PLN permite observar la traza de una inferencia, sus características y pesos, extraer campos preliminares, pedir aclaraciones, consultar casos relacionados y revisar resultados experimentales. La prioridad alta, media o baja se estima mediante reglas con motivo y evidencia textual, independiente del tema y siempre sujeta a revisión. La demostración mantiene 86 textos elaborados. El modelo activo demo-v3 obtuvo macro-F1 de 0,540 en validación cruzada por grupos, por debajo de la referencia de palabras clave (0,973). Una búsqueda expandida seleccionó regresión logística con n-gramas de caracteres (0,768), pero tampoco superó esa referencia y el candidato no se activó. Las pruebas recientes de prioridad/API/PLN y navegador pasaron 38 y 9 casos, respectivamente. Estos resultados verifican funciones de software; no acreditan desempeño con mensajes reales, validez de la prioridad o utilidad municipal. La evaluación local requiere datos autorizados, anotación independiente y validación de competencias.',False)
kw=p('',False);kw.add_run('Palabras clave: ').italic=True;kw.add_run('procesamiento de lenguaje natural, clasificación de texto, incidencias urbanas, revisión humana, Juliaca')
page()
doc.add_paragraph('Contenido',style='Title')
# Campo actualizable por Word; los títulos permanecen como navegación nativa.
toc=p('',False);fld=OxmlElement('w:fldSimple');fld.set(qn('w:instr'),'TOC \\o "1-1" \\h \\z \\u');toc._p.append(fld)
intro=h('Introducción');intro.paragraph_format.page_break_before=True
p('Clasificar una descripción ciudadana implica reconocer el problema principal y distinguirlo de su ubicación, urgencia o posible entidad competente. En este proyecto, el ámbito de interés es el español y las incidencias urbanas de Juliaca. El sistema recibe un mensaje, propone un tema y registra evidencia de la clasificación y de las actuaciones posteriores. La aplicación permite que una persona confirme, corrija o solicite aclaración sin perder la predicción original.')
p('El resultado principal es un prototipo integrado y reproducible, ampliado con una traza observacional del proceso de PLN, control de versiones analíticas, reglas de prioridad y herramientas administrativas de auditoría. Su funcionamiento se verificó mediante pruebas de API, persistencia, navegación y compilación. El rendimiento observado corresponde a ejemplos elaborados y no demuestra capacidad predictiva sobre mensajes reales de Juliaca. Sin validación real y competencias documentadas, las sugerencias permanecen en revisión.')
p('El alcance académico excluye la comprobación de veracidad, la solución física de problemas y la aceptación oficial por una municipalidad. Tampoco cubre trámites, reclamaciones administrativas formales o solicitudes generales de información. La alerta de posible urgencia es independiente del tema y requiere comprobación humana; no constituye un servicio de emergencias. No se anuncia soporte validado en quechua o aimara.')
h('Planteamiento del problema')
p('Un mensaje puede mencionar varias situaciones, utilizar vocabulario ambiguo o describir un problema fuera del alcance. También puede expresar un tema reconocible cuya competencia no esté confirmada. Una clasificación automática que confunda estas dimensiones puede producir destinos injustificados o estados de atención que no reflejen actuaciones reales. El problema de diseño consiste en organizar estas decisiones y conservar la incertidumbre de forma auditable.')
p('La pregunta del proyecto es cómo implementar un sistema reproducible que sugiera la clasificación temática de descripciones urbanas en español y apoye la revisión y derivación orientativa en Juliaca, manteniendo control humano y evitando afirmaciones de rendimiento sin evidencia local. No se dispone de un diagnóstico cuantitativo municipal que permita estimar ahorro de tiempo o impacto en la atención; esas mediciones pertenecen a un piloto posterior.')
h('Objetivos y justificación')
h('Objetivo general',2)
p('Desarrollar y documentar un sistema de apoyo que reciba descripciones urbanas en español, sugiera una categoría C1–C8 mediante procesamiento de lenguaje natural, aplique criterios de revisión humana, consulte reglas de destino y permita registrar, seguir y corregir los casos de forma auditable.')
h('Objetivos específicos',2)
for text in [
'Definir una taxonomía de ocho categorías y criterios de anotación que distingan problemas principales, casos fronterizos y entradas fuera del alcance.',
'Establecer un contrato de datos con procedencia, grupos, particiones y transformaciones, y controlar duplicados y fuga de información.',
'Comparar una referencia mayoritaria, palabras clave, regresión logística, LinearSVC y Naive Bayes bajo el mismo diseño experimental.',
'Separar la puntuación del modelo, la revisión, la posible urgencia y la competencia administrativa, habilitando abstención cuando falte evidencia.',
'Integrar interfaz, API y persistencia para conservar predicciones, correcciones y estados, con permisos y seguimiento privado.',
'Documentar resultados ejecutados, reproducibilidad y limitaciones, y establecer el procedimiento de evaluación real y piloto autorizado.']:
    p(text)
h('Justificación',2)
p('El aporte técnico es la trazabilidad del ciclo completo y la separación entre inferencia y decisiones humanas. El aporte metodológico es conservar el mismo Pipeline durante entrenamiento e inferencia, impedir que fuentes sin texto se transformen en un corpus ficticio y distinguir validación de software de evaluación predictiva. La pertinencia local debe comprobarse con mensajes autorizados de Juliaca; no se deduce de una interfaz operativa ni de datos de otra ciudad.')
h('Fundamento conceptual')
h('Clasificación supervisada de texto',2)
p('En clasificación supervisada se aprende una relación entre ejemplos de texto y etiquetas de referencia. Aquí la entrada predictora es exclusivamente el texto anonimizado y la salida temática pertenece a C1–C8. Fuente, destino anterior, estado, contactos y correcciones no se incorporan como variables predictoras. Scikit-learn proporciona componentes que permiten construir y comparar estos modelos bajo una interfaz común (Pedregosa et al., 2011).')
h('Representación TF IDF y modelos lineales',2)
p('TF-IDF representa el texto mediante pesos de términos, combinando su frecuencia en cada documento con su distribución en el conjunto de entrenamiento. Su vocabulario y ponderaciones se ajustan dentro de cada Pipeline y pliegue, para que los textos de validación o prueba no intervengan en ese aprendizaje. Se comparan unigramas y combinaciones de unigramas y bigramas. La normalización conserva tildes, negaciones y expresiones del texto; no se adoptó corrección ortográfica ni eliminación de stopwords sin una comparación previa en desarrollo.')
p('La regresión logística y LinearSVC permiten explorar modelos lineales regularizados; MultinomialNB constituye una alternativa probabilística para representaciones textuales no negativas. Las referencias mayoritaria y de palabras clave sirven para comprobar si el aprendizaje aporta una mejora frente a estrategias simples. Un margen de LinearSVC no equivale a una probabilidad y no debe presentarse como porcentaje de confianza.')
h('Calibración abstención y validación por grupos',2)
p('La calibración sigmoide relaciona las respuestas del clasificador con probabilidades estimadas. CalibratedClassifierCV admite particiones explícitas; por ello se construye una lista de índices por grupos dentro del entrenamiento, sin asumir que el argumento de validación cruzada conserva automáticamente la agrupación (Scikit-learn developers, s. f.-a). La documentación de validación cruzada fundamenta la separación por grupos cuando varios ejemplos proceden del mismo origen (Scikit-learn developers, s. f.-b).')
p('La abstención expresa que una sugerencia no debe habilitarse. Puede deberse a puntuación insuficiente, ausencia de validación del umbral, idioma fuera del alcance, múltiples temas o competencia no validada. Una probabilidad alta no demuestra que el mensaje pertenezca al dominio ni que una oficina sea responsable. La revisión humana constituye una ruta de gestión, no una clase adicional de entrenamiento.')
h('Taxonomía y criterios de revisión')
caption(1,'Categorías temáticas del clasificador')
table(['Código','Categoría','Frontera principal'],[
['C1',categories['C1'],'Basura en parque sigue siendo C1 si domina el problema de residuos.'],
['C2',categories['C2'],'Baches y veredas; distinguir drenaje de lluvia de red sanitaria.'],
['C3',categories['C3'],'Señalización, semáforos y circulación; deterioro físico de pista corresponde a C2.'],
['C4',categories['C4'],'Vigilancia y seguridad; no confirma delito ni determina la urgencia.'],
['C5',categories['C5'],'Vegetación, ornato y mantenimiento del parque; residuos dominantes son C1.'],
['C6',categories['C6'],'Problemas de comercio o fiscalización; trámites formales quedan fuera.'],
['C7',categories['C7'],'Iluminación pública; revisión de competencia obligatoria.'],
['C8',categories['C8'],'Agua y desagüe sanitario; revisión de competencia obligatoria.']],[.55,2.7,3.25])
note('R9 es la ruta de revisión humana. No es una novena categoría, una oficina ni un destino administrativo.')
p('Si un texto contiene varios problemas sin uno dominante, se solicita aclaración o se conserva en revisión. El sistema registra por separado el tema sugerido, el tipo y valor de puntuación, los motivos de revisión, la prioridad y el destino orientativo. C7 y C8 permanecen en revisión de competencia en esta versión. Las reglas de demostración se identifican como no validadas y no habilitan una derivación oficial.')
h('Datos y procedimiento de preparación')
h('Corpus de demostración',2)
p('La versión disponible contiene 86 textos elaborados de forma asistida y etiquetados conforme a la guía del proyecto. Se utilizaron 64 para entrenamiento, con ocho por categoría; ocho casos se reservaron para comprobaciones funcionales y 14 para desafíos. No se dispuso de validación ni prueba reales. El campo validado de estas fixtures expresa comprobación funcional contra la guía, no doble anotación humana independiente. No se acredita revisión lingüística local.')
caption(2,'Distribución y uso de los ejemplos elaborados')
table(['Cohorte','Cantidad','Uso permitido'],[['Entrenamiento','64','Ajuste y comparación por grupos; ocho ejemplos por categoría.'],['Funcional','8','Comprobación separada de casos y fronteras.'],['Desafíos','14','Ambigüedad, insuficiencia, idiomas y entradas fuera del alcance.'],['Validación real','0','Umbral sin validación real; no se sustituye con elaborados.'],['Prueba real','0','Rendimiento de Juliaca pendiente.']],[1.5,.7,4.3])
h('Inspección y selección de fuentes',2)
p('Se investigaron recursos de Avilés, La Carlota, Valladolid y Senace. Avilés se descargó e inspeccionó: 2020 filas y un campo Descripcion con 2000 valores únicos. Contiene identificadores y coordenadas, de modo que requiere minimización, revisión de privacidad y anotación antes de usarlo. La Carlota no pudo descargarse en el intento registrado y su identificador de licencia necesita aclaración. Senace presenta reclamaciones administrativas que no equivalen automáticamente a las categorías urbanas del proyecto. Ninguna de estas fuentes ingresó al entrenamiento.')
p('El archivo de Valladolid fue proporcionado posteriormente y se comprobó frente al catálogo oficial. Contiene 202 296 registros entre el 31 de julio de 2009 y el 30 de diciembre de 2020, con 12 columnas y 156 etiquetas temáticas no vacías. El campo peticion es un identificador numérico en todas las filas; tema es una etiqueta administrativa. No existe una descripción libre que permita entrenar el clasificador de mensajes ciudadanos (Ayuntamiento de Valladolid, 2020).')
h('Uso de los registros de Valladolid',2)
p('Se extrajeron cuatro tablas agregadas de temas, años, tipos y correspondencias orientativas C1–C8. No se incorporaron IDs ni coordenadas a la vista de fuentes o a la base de incidencias. El original se conservó sin modificación y su hash coincide con el informe de extracción. El portal publica como condición general CC BY 3.0 ES salvo indicación específica contraria; se mantiene atribución y se declara la transformación (Ayuntamiento de Valladolid, s. f.).')
caption(3,'Decisiones descriptivas sobre los registros de Valladolid')
table(['Decisión','Registros','Interpretación'],[
['Correspondencia orientativa','127 475','Comparable por etiqueta administrativa; no es verdad de referencia de un texto.'],
['Fuera del alcance','28 639','Temas administrativos ajenos al clasificador.'],
['Ambiguo','28 354','La etiqueta no determina problema dominante.'],
['Sin correspondencia','17 826','No existe mapeo documentado.'],
['Sin tema','2','Etiqueta administrativa vacía.'],
['Total','202 296','Reconciliación exacta con el archivo inspeccionado.']],[1.6,1.0,3.9])
p('Las correspondencias orientativas suman 40 312 registros en C1, 15 853 en C2, 16 886 en C3, 13 489 en C4, 24 464 en C5, ninguno en C6, 12 768 en C7 y 3703 en C8. C6 queda sin correspondencia inequívoca; no se completó mediante asignaciones artificiales. Jardines. Limpieza permanece ambiguo, Tapas de registro no distingue drenaje o red sanitaria y Tasa de basuras se excluye por su naturaleza tributaria. El mapeo no está validado independientemente por personas.')
p('Renombrar tema como texto_reclamo filtraría la respuesta al modelo. Duplicar una etiqueta miles de veces tampoco crea ejemplos independientes. El validador bloquea tanto el formato administrativo bruto como un supuesto corpus real que declare esta fuente sin texto libre. Su utilidad en el proyecto es descriptiva: muestra cobertura y exclusiones, pero no mejora ni acredita el rendimiento del modelo de texto.')
h('Contrato y privacidad',2)
p('El CSV académico utiliza UTF-8 y las columnas id, texto_reclamo, categoria, fuente, tipo_dato, validado, grupo_origen, particion, motivo_revision, transformacion y licencia_autorizacion. La categoría solo admite C1–C8 o vacío en desafíos sin tema asignable. La procedencia distingue real y elaborado; los grupos vinculan originales y variantes. La validación revisa columnas, IDs, vacíos, etiquetas, procedencia, duplicados y solapamientos.')
p('La redacción preliminar detecta DNI, teléfonos, correos y algunos patrones de nombres y domicilios. Las expresiones regulares no garantizan anonimización completa: las identidades residuales y referencias indirectas requieren revisión humana. Los contactos operativos se separan del corpus y no se solicitan en el MVP. No deben subirse registros identificables a Colab o servicios externos. Antes de recopilar datos reales deben definirse finalidad, acceso, conservación, eliminación y requisitos institucionales de protección de datos; el Reglamento aprobado por el Decreto Supremo 016-2024-JUS es una referencia normativa que debe contrastarse antes del piloto (Ministerio de Justicia y Derechos Humanos, 2024).')
h('Protocolo de corpus local y anotación',2)
p('La meta de planificación es aproximarse a 800 textos clasificables y unos 100 desafíos, procurando cobertura temática sin duplicar registros para completar cuotas. Estas cifras no expresan suficiencia estadística. Se debe reservar primero una prueba real independiente, preferentemente de Juliaca, y registrar los criterios de selección, periodos y sesgos de adquisición.')
p('Dos personas deben etiquetar independientemente al menos el 20 % del conjunto y todos los casos de prueba y desafío cuando sea viable. El acuerdo porcentual y kappa de Cohen se calculan antes de resolver desacuerdos. Las adjudicaciones conservan ID, etiqueta final, responsable, fecha, explicación y versión de guía. Las predicciones del sistema no se utilizan como verdad de referencia. Este protocolo está documentado, pero no se completó una anotación humana independiente para el corpus entregado.')
h('Metodología experimental')
h('Diseño y control de fuga de información',2)
p('El proyecto tiene un propósito aplicado y un componente experimental de clasificación supervisada. La unidad temática es un texto anonimizado; la unidad de separación es grupo_origen. Originales, paráfrasis, plantillas y subcasos relacionados deben compartir el grupo para que no crucen entrenamiento, validación o prueba. El experimento distingue la verificación técnica del prototipo de la evaluación empírica sobre el contexto objetivo.')
p('Se usa 60/20/20 como referencia para datos reales cuando el soporte por grupos permite esa distribución. Si ya existe prueba independiente reservada, se conserva antes de distribuir el desarrollo restante. Los tamaños efectivos, semilla 42, IDs, grupos y hashes se registran en manifiestos. En la demo se conservó entrenamiento elaborado y cohortes funcionales y de desafío aparte; no se creó una validación o prueba real artificial.')
p('La validación cruzada es estratificada por grupos dentro del entrenamiento. El número de pliegues se adapta entre dos y cinco y se exige soporte de las ocho categorías en cada subconjunto de ajuste y evaluación. Si los grupos no permiten el experimento, el comando falla con un mensaje explicativo. TF-IDF se ajusta dentro de cada Pipeline y pliegue; no se aprende vocabulario ni parámetros con la prueba. Los duplicados cercanos se revisan mediante similitud léxica y agrupación, reconociendo que ese control no prueba ausencia de equivalencia semántica.')
h('Modelos e hiperparámetros',2)
caption(4,'Comparación y espacio de búsqueda')
table(['Modelo','Configuración explorada'],[
['DummyClassifier','Clase mayoritaria como referencia.'],
['Palabras clave','Lista documentada y congelada en desarrollo; hash en manifiesto.'],
['Regresión logística','TF-IDF de unigramas o unigramas y bigramas; C = 0,1, 1 y 10; ponderación nula o balanced.'],
['LinearSVC','Mismas opciones de TF-IDF y C; ponderación nula o balanced.'],
['MultinomialNB','TF-IDF de unigramas o unigramas y bigramas; alpha = 0,1 y 1.']],[1.75,4.75])
p('Los modelos aprendidos se seleccionan por macro-F1 media de validación cruzada. Los desempates numéricos priorizan simplicidad según el orden logística, SVC y Naive Bayes. Las referencias se comparan para determinar si existe mejora; no se ocultan cuando superan al modelo aprendido. Con datos reales suficientes debe compararse entrenamiento solo real frente a híbrido, manteniendo la misma prueba independiente y selección separada en desarrollo.')
h('Calibración y umbral',2)
p('Se aplicó calibración sigmoide al mejor Pipeline de logística, SVC y Naive Bayes utilizando los índices explícitos relativos al subconjunto correcto de entrenamiento. La calibración no consulta validación del umbral ni prueba. En validación real adecuada se exploran umbrales de 0,50 a 0,95, con paso 0,05, y se elige la mayor cobertura con exactitud selectiva observada de al menos 0,90. Se registra el número de aceptados y un intervalo Wilson del 95 %, con su limitación de independencia.')
p('Si no hay validación real adecuada o ningún umbral cumple, el umbral es nulo y todas las entradas requieren revisión. El código utiliza mínimos conservadores de ingeniería de 40 textos, ocho clases y 16 grupos reales; no los presenta como suficiencia estadística. Las metas macro-F1 de al menos 0,75, mejora sobre ambas referencias y exactitud selectiva de al menos 0,90 son provisionales. No se permite ajustar reiteradamente con el test para alcanzarlas.')
h('Evaluación y denominadores',2)
p('La clasificación sin abstención se mide solo donde existe tema conocido, mediante accuracy, precisión, recall, F1 por clase, soporte, macro-F1 y matriz de confusión con orden C1–C8. Una clase ausente no se presenta como evaluada. Se separan datos reales locales, reales externos, elaborados y desafíos, y se realiza análisis de errores por fuente cuando existe soporte. El remuestreo por grupos ofrece intervalos exploratorios cuyo alcance es limitado con pocos grupos.')
p('La revisión se evalúa por separado. Cobertura es el número de sugerencias habilitadas dividido por las entradas de la cohorte. Error selectivo considera solo aceptados con etiqueta temática conocida. La aceptación errónea fuera del alcance necesita un denominador de casos fuera del dominio; la coincidencia del destino requiere una referencia administrativa revisada. Un denominador ausente se informa como no calculable, evitando interpretar un nulo como desempeño perfecto.')
h('Arquitectura e implementación')
p('La interfaz inicialmente planteada en Streamlit se adaptó a React, TypeScript, Vite, React Router y Tailwind CSS. FastAPI y Pydantic ofrecen contratos HTTP y separan presentación, servicios y persistencia. El experimento permanece en Python con pandas, scikit-learn y joblib, de modo que el cambio de interfaz no reemplaza la metodología experimental. La recomendación de construir un contenedor Python propio para FastAPI se sigue en la configuración de ejecución (FastAPI, s. f.).')
caption(1,'Separación de aplicación y experimentación',kind='Figura')
picture(QA/'arquitectura.png')
note('El modelo se entrena por comandos administrativos, no durante las peticiones HTTP. PostgreSQL está configurado en Compose; SQLite se verificó como demostración individual.')
h('Servicios y persistencia',2)
p('Los servicios de clasificación, revisión y destino componen un resultado común a la API y la evaluación. El servicio de registro realiza la transacción y maneja idempotencia. El clasificador carga una vez por proceso un artefacto propio con manifiesto, versiones y verificación de integridad. Si falta el modelo o falla la inferencia, la incidencia válida se conserva con tema y puntuación nulos, y un motivo de revisión explícito.')
p('Las entidades de persistencia incluyen usuarios y roles, sesiones, incidencias, predicciones, revisiones, historial de estados, reglas versionadas, modelos y auditoría. Cada incidencia tiene UUID interno y un código REC-AAAA-NNNNN generado mediante un contador transaccional anual. El año corresponde a America/Lima; las fechas se guardan en UTC. La secuencia se incrementa con UPSERT, con restricciones únicas, y no mediante COUNT más uno.')
p('Las correcciones mantienen tema y destino anteriores, valores revisados, usuario, fecha y explicación. La predicción original se conserva. Las actualizaciones exigen la versión observada del caso; un conflicto concurrente devuelve 409 y requiere recargar. Editar una regla crea una versión nueva, archivando la anterior. Las correcciones no provocan reentrenamiento: deben incorporarse a una nueva versión de datos después de revisión y adjudicación.')
h('Interfaz y ciclo de uso',2)
p('El inicio explica el alcance y las ocho categorías. El formulario recibe hasta 3000 caracteres y ubicación general opcional. La confirmación muestra código y secreto privado de seguimiento. La consulta pública envía ambos por POST y solo devuelve estado y fechas. El panel del personal presenta conteos reales, bandeja con filtros, detalle, revisión, actuaciones, reglas, modelo y experimentos. La vista de fuentes muestra los agregados de Valladolid separadamente de los casos operativos. Se simplificaron el encabezado, el pie y algunos textos de registro para retirar mensajes institucionales de prueba que distraían del flujo.')
p('Una ruta protegida sin sesión lleva al formulario de acceso y conserva el destino para volver después de la autenticación. Errores de servicio mantienen la opción de reintento. Se incluyen estados de carga, vacío, error y confirmación, navegación responsive, etiquetas de formularios y foco visible. React escapa el texto ciudadano y no lo interpreta como instrucciones ejecutables.')
h('Proceso de PLN y prioridad del mensaje',2)
p('La ruta pública /pln analiza un texto sin crear una incidencia, código de seguimiento ni estado operativo. Cada etapa informa su resultado, tiempo y versión cuando está disponible. La traza de inferencia observa las transformaciones reales del mismo artefacto TF-IDF y del clasificador calibrado mediante copias superficiales por solicitud. Devuelve las características producidas, sus frecuencias, IDF y pesos; limita la salida y aclara que los pesos no son explicaciones causales. La observación no vuelve a ajustar el modelo ni modifica su objeto compartido. La comparación de redacción oculta los segmentos sustituidos antes de responder.')
p('El análisis preliminar extrae fragmentos literales para problema, ubicación y referencia temporal; los campos ausentes permanecen nulos. Si detecta información faltante o varios temas posibles, propone preguntas. El personal puede guardar un análisis versionado, registrar respuestas o corregir campos extraídos, preservando el texto y la predicción originales. Las aclaraciones generan una inferencia contextual nueva; corregir una extracción no reescribe la predicción. Los casos relacionados se buscan con un índice TF-IDF que se construye fuera de las solicitudes web. Una coincidencia se registra para revisión y nunca fusiona casos ni altera su estado.')
caption(6,'Reglas de prioridad de demostración')
table(['Nivel','Señales orientativas','Tratamiento'],[
['Alta','Riesgo explícito para personas o interrupción de un servicio esencial.','Mostrar motivo y fragmento; revisión humana obligatoria.'],
['Media','Falla de servicio, acumulación o problema persistente.','Sugerencia orientativa; confirmar impacto y alcance.'],
['Baja','Mantenimiento, poda, ornato o mejora sin riesgo expresado.','Sugerencia orientativa; puede elevarse con evidencia adicional.'],
['Media provisional','Texto insuficiente o sin señal reconocida.','Indicar falta de información; no interpretar como riesgo medio confirmado.']],[1.2,2.8,2.5])
note('La regla priority-rules-v1 es independiente del clasificador temático. Las negaciones próximas a una señal se consideran, pero la lista de expresiones no cubre todas las formas de describir un riesgo. La prioridad no ha sido entrenada ni validada contra anotaciones locales y siempre requiere revisión.')
h('Auditoría de datos y capacidades',2)
p('La vista administrativa de Datos y entrenamiento asocia reportes experimentales con su conjunto de datos y artefacto mediante hashes. Presenta por separado la validación cruzada, las cohortes funcionales y los desafíos; los valores sin evidencia aparecen como no evaluados. La selección de un candidato para consulta no cambia el modelo activo. La ruta Situación y mejoras resume las capacidades A–L, sus problemas, dependencias y evidencias. Este inventario distingue la implementación técnica de la validación local pendiente.')
h('Reglas de destino estados y seguridad')
p('Las reglas son independientes del modelo y registran categoría, ámbito, destino, condiciones, validación, vigencia, fuente documental, responsable y versión. Las de demostración carecen de competencia institucional validada. La coincidencia temática no confirma responsabilidad municipal. Cuando faltan reglas, existen condiciones no verificadas o varias reglas aplicables, el caso permanece en revisión.')
caption(5,'Estados y actuación requerida')
table(['Estado','Condición de uso'],[
['Pendiente de revisión','Incertidumbre, modelo ausente, falta de umbral o competencia pendiente.'],
['Sugerencia disponible','Sugerencia orientativa que supera la política; no representa derivación oficial.'],
['Revisado','Persona confirma o corrige tema y destino con motivo.'],
['Derivado','Administrador confirma una actuación humana con evidencia, desde Revisado.'],
['Resuelto','Administrador confirma resolución con evidencia, desde Derivado.']],[1.75,4.75])
p('El rol revisor consulta y revisa; el administrador también gestiona reglas y confirma actuaciones oficiales. El backend verifica estos permisos. Se emplean contraseñas con Argon2id, sesiones con expiración y revocación, cookies HttpOnly y SameSite, token CSRF para mutaciones y CORS restringido. El modo Secure debe configurarse para HTTPS antes de un piloto.')
p('El código visible no es una credencial. El secreto de seguimiento se deriva con HMAC a partir de una clave aleatoria de registro y un secreto externo, y se almacena solo su hash. Código inexistente y secreto incorrecto reciben la misma respuesta pública. Se limitan intentos de login, consulta y registro; no se registran cuerpos identificables ni secretos en logs. No existe carga web de modelos arbitrarios ni una ruta pública de entrenamiento.')
h('Resultados ejecutados')
h('Comparación en ejemplos elaborados',2)
p('La ejecución demo-v3 comparó las cinco referencias con 64 textos elaborados y cinco pliegues por grupos. Las cifras de la Figura 2 provienen de experiment.json; describen la validación cruzada de desarrollo, no el test real. El mejor modelo aprendido fue LinearSVC, con macro-F1 de 0,540. La referencia de palabras clave alcanzó 0,973 y superó a los modelos aprendidos.')
caption(2,'Macro F1 en validación cruzada de entrenamiento elaborado',kind='Figura')
picture(QA/'comparacion.png')
note('Valores ejecutados: Dummy 0,018; palabras clave 0,973; logística 0,535; LinearSVC 0,540; Naive Bayes 0,511. No son métricas del contexto real de Juliaca.')
caption(7,'Configuración seleccionada y tiempos de búsqueda')
table(['Modelo aprendido','Mejor configuración','Tiempo en segundos'],[
['Logística','C = 0,1; balanced; unigramas',f"{experiment['results'][2]['seconds']:.2f}"],
['LinearSVC','C = 1; balanced; unigramas y bigramas',f"{experiment['results'][3]['seconds']:.2f}"],
['Naive Bayes','alpha = 0,1; unigramas y bigramas',f"{experiment['results'][4]['seconds']:.2f}"]],[1.5,3.5,1.5])
p('La superioridad de palabras clave evidencia que los ejemplos son limpios y léxicamente cercanos a la referencia. El corpus es pequeño y su distribución se construyó artificialmente. No se alcanzó la meta de macro-F1 de 0,75 en CV ni la mejora frente a ambas referencias; esas limitaciones se conservan en los reportes, sin ajustar repetidamente una prueba para ocultarlas. Los tiempos registrados corresponden a la búsqueda en ese entorno, no a tiempos de atención municipal.')
h('Búsqueda expandida del 14 de octubre',2)
p('Se ejecutó una segunda búsqueda, identificada como pln-expanded-demo-20261014, sobre el mismo entrenamiento elaborado de 64 ejemplos y cinco pliegues por grupos. Amplió TF-IDF a n-gramas de caracteres y comparó regresión logística, LinearSVC, Naive Bayes y SVC con kernel RBF, además de las referencias. La logística con caracteres de longitud 3 a 5 y C = 0,1 obtuvo la mejor macro-F1 aprendida. Esta búsqueda es un experimento separado y el candidato resultante no reemplazó demo-v3.')
caption(8,'Resultados de la búsqueda expandida')
table(['Referencia o modelo','Macro F1 CV','Configuración o interpretación'],[
['Clase mayoritaria',f"{expanded['results'][0]['cv_macro_f1']:.3f}",'Referencia Dummy.'],
['Palabras clave',f"{expanded['results'][1]['cv_macro_f1']:.3f}",'Referencia léxica; supera a los modelos aprendidos.'],
['Regresión logística',f"{expanded['results'][2]['cv_macro_f1']:.3f}",'Seleccionada entre modelos aprendidos; caracteres 3–5, C = 0,1.'],
['LinearSVC',f"{expanded['results'][3]['cv_macro_f1']:.3f}",'Caracteres 3–5.'],
['Naive Bayes',f"{expanded['results'][4]['cv_macro_f1']:.3f}",'Caracteres 3–5.'],
['SVC con kernel RBF',f"{expanded['results'][5]['cv_macro_f1']:.3f}",'Caracteres 3–5.']],[1.65,.9,3.95])
note('Los resultados pertenecen a textos elaborados; la métrica de validación cruzada no constituye una evaluación externa. La referencia de palabras clave sigue por encima de todos los modelos aprendidos.')
caption(9,'Cohortes separadas de la búsqueda expandida')
table(['Cohorte','Casos evaluables','Accuracy','Macro F1 de clases presentes'],[
['Funcional',str(expanded_functional['results'][0]['classification']['n']),f"{expanded_functional['results'][0]['classification']['accuracy']:.3f}",f"{expanded_functional['results'][0]['classification']['macro_f1_present_classes']:.3f}"],
['Desafíos con tema conocido',str(expanded_challenge['results'][0]['classification']['n']),f"{expanded_challenge['results'][0]['classification']['accuracy']:.3f}",f"{expanded_challenge['results'][0]['classification']['macro_f1_present_classes']:.3f}"]],[2.3,1.2,1.0,2.0])
note('La cohorte de desafíos contiene 14 textos, de los cuales solo seis tienen tema conocido; los ocho restantes no entran en las métricas temáticas. La cohorte funcional tiene ocho casos, uno por clase. Los denominadores pequeños y el origen elaborado impiden extrapolar estos resultados a Juliaca.')
h('Pruebas funcionales y desafíos',2)
caption(10,'Resultados temáticos en cohortes elaboradas separadas')
table(['Cohorte','Total','Con tema conocido','Accuracy','Macro F1'],[
['Funcional','8','8','0,875','0,833'],
['Desafíos','14','6','0,667','0,733']],[1.6,.65,1.65,.8,1.8])
note('En funcional hay un caso por categoría. En desafíos solo se representa C1, C2, C4, C7 y C8; macro-F1 se calcula sobre clases presentes. Ocho desafíos no tienen tema conocido y no ingresan al denominador temático.')
p('En la cohorte funcional, siete de ocho casos se clasificaron con el tema de referencia. El error fue FUNC-C1, basura dentro de un parque, predicho como C5 en lugar de C1. Este fallo concreta la frontera entre lugar y problema dominante y muestra que la interfaz no puede sustituir una política de revisión. En desafíos se observaron dos errores sobre C1: CH-09 se predijo C2 y CH-12 se predijo C5.')
p('La cobertura operativa fue cero en las cohortes funcional y de desafíos. No hubo casos aceptados con etiqueta conocida, por lo que el error selectivo y la exactitud selectiva no son calculables. En desafíos se identificaron cuatro entradas fuera del alcance y ninguna fue habilitada; esto no acredita un detector general de dominio, pues todo el conjunto estaba bloqueado por la política demostrativa. Tampoco hubo referencias administrativas de destino y su coincidencia no es calculable.')
h('Verificación de software',2)
caption(11,'Evidencias de pruebas y ejecución')
table(['Evidencia','Resultado','Alcance'],[
['Suites base y de datos','58 y 45 pasadas','API, ML, permisos, transacciones, migraciones, SQLite y fuentes; hay solapamiento.'],
['Suite focalizada prioridad/API/PLN','38 pasadas','Reglas de prioridad, traza, API, privacidad, persistencia, aclaraciones y relaciones.'],
['Suite completa anterior','78 pasadas','Regresión general de PLN antes del último cambio de prioridad; no sumar con las suites focalizadas.'],
['Playwright reciente','9 pasadas','Registro, seguimiento, revisión, móvil, prioridad, encabezado, auditoría y proceso PLN.'],
['TypeScript y Vite','Compilación pasada','41 módulos; JavaScript 287,78 kB (89,14 kB comprimido).'],
['Docker Compose','Configuración pasada','Motor Linux no disponible; contenedores/PostgreSQL sin ejecución verificada.'],
['Notebooks','Estructura y código válidos','No se ejecutaron completos en Colab.']],[1.6,1.05,3.85])
note('Las cifras se solapan y no se suman como un total de pruebas únicas. La suite completa de 78 casos antecede al cambio de prioridad; el cambio posterior se verificó con las 38 pruebas focalizadas y nueve pruebas de navegador. Las pruebas acreditan comportamiento de software, no calidad predictiva ni eficacia municipal.')
p('Se comprobaron 12 registros concurrentes y reintentos de la misma clave sin duplicar códigos en SQLite, conservación de casos tras reinicio, correcciones sin pérdida de predicción, conflictos de versión, transiciones autorizadas y rechazo de secretos incorrectos. La correspondencia entre predicción del script y la API también pasó. Estas garantías deben volver a verificarse con PostgreSQL en un motor operativo antes de un piloto.')
h('Discusión y limitaciones')
p('El prototipo permite reproducir el ciclo de datos elaborados, entrenamiento, inferencia, registro y revisión. Esa integración técnica es un resultado concreto, pero no implica rendimiento suficiente para mensajes reales. Las métricas de CV y de ocho casos funcionales pertenecen a cohortes pequeñas; no se pueden combinar ni extrapolar como una precisión única del sistema en Juliaca.')
p('La fuente de Valladolid ilustra una limitación de adquisición: una gran cantidad de filas no equivale a un corpus útil para PLN. Las etiquetas y metadatos permiten un análisis descriptivo, pero entrenar con ellas confundiría frecuencia administrativa con lenguaje ciudadano. Su exclusión protege la evaluación y evita fabricar ejemplos reales. Además, ninguna frecuencia externa determina la prioridad de un caso local.')
p('Las heurísticas de idioma, ambigüedad y urgencia presentan falsos positivos y negativos. Una coincidencia de términos puede indicar varios temas aun cuando el mensaje tenga uno dominante; una urgencia expresada con vocabulario diferente puede no disparar la alerta. C7 y C8 requieren revisión de competencia y las reglas demostrativas no están contrastadas con documentación institucional vigente. La redacción preliminar tampoco elimina todas las posibilidades de identificación.')
p('La prioridad alta/media/baja utiliza expresiones y reglas escritas, con una prioridad media provisional cuando falta evidencia suficiente. Las pruebas verifican ejemplos previstos, negaciones y coherencia entre simulación y registro, pero no estiman sensibilidad, especificidad ni acuerdo con revisores. El texto puede expresar riesgo con vocabulario no contemplado o contener contextos que alteren el sentido. Por ello, el nivel no sustituye una valoración humana ni un canal de emergencia.')
p('La evaluación independiente humana, la recopilación autorizada y la medición de un piloto siguen pendientes. El experimento no permite sostener disminución de tiempo, resolución de incidencias, utilidad municipal o superioridad sobre procedimientos de una entidad real. Para versiones futuras debe evitarse utilizar indefinidamente el mismo test como criterio de selección.')
h('Conclusiones y siguientes pasos')
p('Se implementó una aplicación académica integrada con clasificación temática, revisión humana, seguimiento privado y auditoría. La separación entre tema, puntuación, prioridad, competencia y estados permite conservar la incertidumbre y comprobar qué actuación ocurrió. El modelo demostrativo se entrenó y se carga desde un artefacto propio versionado, sin reentrenamiento automático en la API.')
p('La comparación ejecutada no demostró mejora del modelo aprendido sobre la referencia de palabras clave. La ausencia de validación real conduce a un umbral nulo y revisión de todas las entradas. El archivo de Valladolid se incorporó exclusivamente como fuente estructurada de análisis, porque no contiene descripciones ciudadanas utilizables para entrenar el clasificador.')
p('La ampliación del Proceso de PLN aporta observación de etapas, extracción preliminar, aclaraciones versionadas, consulta de casos relacionados y auditoría de experimentos. La regla de prioridad agrega un nivel sugerido con evidencia textual. Estas funciones mejoran la inspección y el control del flujo técnico; todavía necesitan evaluación con mensajes autorizados y criterios acordados localmente.')
p('Antes de un piloto se requiere un corpus real local autorizado, revisión de privacidad, anotación independiente y adjudicación, prueba reservada, calibración y umbral real, referencia administrativa de destinos y validación de reglas vigentes. También se debe ejecutar Compose con PostgreSQL, comprobar respaldo y restauración, definir HTTPS y conservación, y obtener autorización institucional. Estos pasos deben completarse con evidencia antes de afirmar rendimiento o impacto local.')
page()
h('Referencias')
references=[
('Ayuntamiento de Valladolid. (2020). Incidencias, quejas, sugerencias y reclamaciones hasta 2020 [Conjunto de datos]. https://www.valladolid.es/es/temas/hacemos/open-data-datos-abiertos/catalogo-datos/ficheros-datos-elaborados-clasificados-sectores/sector-publico','Incidencias, quejas, sugerencias y reclamaciones hasta 2020'),
('Ayuntamiento de Valladolid. (s. f.). Open Data Datos Abiertos. Recuperado el 14 de octubre de 2026, de https://www.valladolid.es/es/temas/hacemos/open-data-datos-abiertos','Open Data Datos Abiertos'),
('FastAPI. (s. f.). FastAPI in containers Docker. https://fastapi.tiangolo.com/deployment/docker/','FastAPI in containers Docker'),
('Ministerio de Justicia y Derechos Humanos. (2024, 30 de noviembre). Decreto Supremo 016-2024-JUS que aprueba el Reglamento de la Ley 29733 Ley de Protección de Datos Personales. Diario Oficial El Peruano. https://www3.congreso.gob.pe/Docs/DGP/DIDP/files/ds_016-2024-jus.pdf','Decreto Supremo 016-2024-JUS que aprueba el Reglamento de la Ley 29733 Ley de Protección de Datos Personales'),
('Pedregosa, F., Varoquaux, G., Gramfort, A., Michel, V., Thirion, B., Grisel, O., Blondel, M., Prettenhofer, P., Weiss, R., Dubourg, V., Vanderplas, J., Passos, A., Cournapeau, D., Brucher, M., Perrot, M., & Duchesnay, E. (2011). Scikit-learn: Machine learning in Python. Journal of Machine Learning Research, 12, 2825–2830. https://jmlr.org/papers/v12/pedregosa11a.html','Journal of Machine Learning Research, 12'),
('Scikit-learn developers. (s. f.-a). CalibratedClassifierCV. Scikit-learn 1.6.1 documentation. https://scikit-learn.org/1.6/modules/generated/sklearn.calibration.CalibratedClassifierCV.html','CalibratedClassifierCV'),
('Scikit-learn developers. (s. f.-b). Cross-validation Evaluating estimator performance. Scikit-learn 1.6.1 documentation. https://scikit-learn.org/1.6/modules/cross_validation.html','Cross-validation Evaluating estimator performance')]
for text,italic in references:
    para=p('',False);para.paragraph_format.left_indent=Inches(.5);para.paragraph_format.first_line_indent=Inches(-.5)
    before,after=text.split(italic,1);para.add_run(before);para.add_run(italic).italic=True;para.add_run(after)
page()
h('Apéndice A')
h('Guía de reproducción y uso',2)
p('Requisitos locales: Python 3.12, Node 22.12 o posterior, PowerShell y, para PostgreSQL, Docker Desktop con motor Linux activo. Las dependencias están fijadas en requirements.lock.txt y frontend/package-lock.json. La alternativa SQLite está orientada a demostración individual. Ejecutar los comandos desde la raíz del proyecto y utilizar un nombre nuevo para cada experimento para conservar resultados previos.')
code(['python -m venv .venv',r'& .\.venv\Scripts\python.exe -m pip install -r requirements.lock.txt',r'& .\scripts\init_env.ps1',r'& .\.venv\Scripts\python.exe -m alembic upgrade head',r'& .\.venv\Scripts\python.exe -m backend.manage seed-rules','npm.cmd ci --prefix frontend'])
p('El script de entorno conserva un .env existente y genera secretos aleatorios al crear uno nuevo. Los usuarios se crean explícitamente mediante backend.manage create-user o scripts.setup_demo para SQLite. La contraseña no se publica en el informe ni en la interfaz. Se debe evitar incluir .env, bases operativas y fuentes originales en Git o en archivos enviados a servicios externos.')
code([r'& .\.venv\Scripts\python.exe -m scripts.setup_demo',r'& .\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --no-access-log','npm.cmd run dev --prefix frontend'])
p('La API y el frontend se ejecutan en terminales separadas. La interfaz está en http://127.0.0.1:5173 y los contratos en http://127.0.0.1:8000/docs. Para el experimento demostrativo se usan los siguientes comandos; la calibración se realiza durante train y threshold congela el umbral, aunque sea nulo.')
code([r'& .\.venv\Scripts\python.exe -m ml.cli validate data/demostracion.csv',r'& .\.venv\Scripts\python.exe -m ml.cli split data/demostracion.csv data/demo_particionado.csv',r'& .\.venv\Scripts\python.exe -m ml.cli train data/demo_particionado.csv reports/runs/nueva-demo --demo',r'& .\.venv\Scripts\python.exe -m ml.cli threshold data/demo_particionado.csv reports/runs/nueva-demo',r'& .\.venv\Scripts\python.exe -m ml.cli evaluate data/demo_particionado.csv reports/runs/nueva-demo --partition functional',r'& .\.venv\Scripts\python.exe -m ml.cli evaluate data/demo_particionado.csv reports/runs/nueva-demo --partition challenge',r'& .\.venv\Scripts\python.exe -m ml.cli activate reports/runs/nueva-demo'])
p('Después de activar un modelo se reinicia la API. Los manifiestos registran hashes, clases, parámetros, versiones, grupos, umbral y fecha. El modelo anterior se conserva para rollback. Una evaluación real debe seguir el protocolo de corpus autorizado antes de sustituir la demostración. Los notebooks reutilizan estos módulos y solo pueden recibir datos anonimizados autorizados.')
p('Para usar el sistema, registrar una descripción sin datos identificables y guardar el código y el secreto. Consultar seguimiento con ambos valores. El personal inicia sesión, abre la bandeja y registra la revisión con motivo; el administrador confirma actuaciones posteriores con evidencia. La predicción original y el historial quedan disponibles. La vista Fuentes de datos muestra los agregados externos sin convertirlos en incidencias.')
code(['docker compose config --quiet','docker compose up --build -d',r'& .\.venv\Scripts\python.exe -m pytest --junitxml=reports/pytest.xml',r'& .\.venv\Scripts\python.exe -m pytest tests/test_priority.py tests/test_api.py tests/test_pln.py','npm.cmd run build --prefix frontend','npm.cmd run test:integration --prefix frontend'])
note('Playwright utiliza una base de pruebas aislada y puertos 8000 y 5173. Antes de ejecutarlo, detener los servidores de demostración que ocupen esos puertos. La ejecución Docker no fue verificada en el entorno registrado.')
page()
h('Apéndice B')
h('Diccionario de datos y contratos API',2)
caption(12,'Campos del corpus académico')
table(['Campo','Regla principal'],[
['id','Identificador único y estable, sin identidad ciudadana.'],['texto_reclamo','Texto anonimizado no vacío; única variable predictora.'],['categoria','C1–C8; vacío en desafíos sin tema asignable.'],['fuente','Referencia de procedencia autorizada e inspeccionada.'],['tipo_dato','real o elaborado; no se confunden transformaciones con origen.'],['validado','true o false conforme al protocolo; demo distingue verificación funcional.'],['grupo_origen','Original o plantilla común que no cruza particiones.'],['particion','train, validation, test, challenge o functional.'],['motivo_revision','Razones de revisión esperadas, independientes del tema.'],['transformacion','Proceso y versión de elaboración, normalización o redacción.'],['licencia_autorizacion','Referencia verificable de permiso o licencia.']],[1.8,4.7])
caption(13,'Rutas principales bajo api v1')
table(['Método y ruta relativa','Finalidad'],[
['POST /incidencias','Registrar; 201 nuevo, 200 reintento idéntico.'],['POST /seguimiento/consulta','Consultar código y secreto; respuesta pública mínima.'],['POST /auth/login y /auth/logout','Crear o revocar sesión del personal.'],['GET /categorias','Taxonomía C1–C8 y explicación de R9.'],['GET /admin/incidencias y /{id}','Bandeja paginada y detalle autorizado.'],['POST /admin/incidencias/{id}/revision','Confirmar o corregir con motivo y versión.'],['POST /admin/incidencias/{id}/transiciones','Actuaciones humanas y evidencia.'],['GET POST PATCH /admin/reglas','Consultar, crear y versionar reglas; mutaciones para administrador.'],['GET /admin/estadisticas','Conteos reales de casos operativos.'],['GET /admin/modelo y /admin/experimentos','Disponibilidad, manifiesto y ejecuciones.'],['GET /admin/fuentes','Resúmenes externos agregados; acceso del personal.'],['GET /health/live y /health/ready','Proceso y persistencia; registro puede estar listo sin modelo.']],[3.0,3.5])
p('Los contratos completos están en docs/openapi.json. La simulación se ofrece en POST /api/v1/pln/analizar; los metadatos y capacidades se consultan en GET /api/v1/pln/metadatos y GET /api/v1/pln/capacidades. El personal autorizado usa GET /api/v1/admin/pln/datos para auditoría experimental y las rutas de incidencias para guardar análisis, aclaraciones, correcciones de extracción y decisiones sobre casos relacionados. Estas operaciones exigen sesión y, cuando modifican datos, protección CSRF. Los estados HTTP distinguen falta de sesión 401, permisos o CSRF 403, conflicto 409, entrada inválida 422, límite de intentos 429 y persistencia no disponible 503. La respuesta de clasificación conserva tema y puntuación nulos cuando faltan inferencia o artefacto; nunca inventa un resultado para completar el formulario.')
page()
h('Apéndice C')
h('Evidencias y pendientes para un piloto',2)
caption(14,'Archivos que respaldan los resultados del informe')
table(['Evidencia','Ubicación en el proyecto'],[
['Corpus elaborado y procedencia','data/demostracion.csv y data/demo_manifest.json'],['Particiones por grupos','data/demo_particionado.manifest.json'],['Comparación ejecutada','reports/runs/demo-v3/experiment.json'],['Umbral y cohortes separadas','reports/runs/demo-v3/threshold.json, functional_evaluation.json y challenge_evaluation.json'],['Modelo activo','models/active.json y artefacto propio demo-v3.joblib'],['Extracción de Valladolid','reports/sources/valladolid_2020.json y cuatro tablas CSV agregadas'],['Pruebas base y de datos','reports/pytest.xml y reports/pytest_dataset.xml'],['Pruebas recientes de navegador','reports/playwright.json'],['Código y protocolos','backend, frontend, ml, notebooks, config, tests y docs'],['Trazabilidad de requisitos','docs/matriz_cumplimiento.md']],[2.0,4.5])
p('Las mejoras añadidas se respaldan en tests/test_priority.py, reports/pytest_priority.xml, reports/runs/pln-expanded-demo-20261014/experiment.json, docs/proceso_pln.md, docs/contratos_pln.md y docs/matriz_pln.md. La aprobación de un piloto requiere evidencia de permiso para el corpus, anonimización humana, doble anotación y acuerdo, particiones independientes, evaluación real y revisión del umbral. Las competencias deben contrastarse con documentos vigentes y responsables identificados. No se debe atribuir responsabilidad oficial a partir de una categoría.')
p('También se deben comprobar operación con PostgreSQL, copia y restauración, control de acceso y conservación, HTTPS y límites de uso acordes al entorno.')

doc.save(OUT)
print(str(OUT))
print('Párrafos:',len(doc.paragraphs),'Tablas:',len(doc.tables))
