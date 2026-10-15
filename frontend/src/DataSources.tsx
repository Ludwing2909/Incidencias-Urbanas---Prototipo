import {useEffect,useState} from 'react'
import {api,categories,Category} from './api'

interface Topic {tema_original:string;registros:number;categoria_orientativa:Category|null;estado_mapeo:string;motivo:string;validado_humano:boolean}
interface SourceReport {
  source_id:string;entity:string;location:string;rows:number;unique_topic_labels:number;
  has_free_text:boolean;training_eligible:boolean;training_rows_extracted:number;
  source_url:string;license:string;license_url:string;attribution:string;sha256:string;
  period:{from:string|null;to:string|null;invalid_dates:number};
  by_category:Record<Category,number>;by_mapping_status:Record<string,number>;
  by_type:Record<string,number>;by_year:{anio:number;registros:number}[];
  topics:Topic[];exclusion_reasons:string[];limitations:string[];
}
const labels:Record<string,string>={compatible_orientativo:'Correspondencia orientativa',ambiguo:'Ambiguo',fuera_de_alcance:'Fuera de alcance',sin_correspondencia:'Sin correspondencia',vacio:'Tema vacío'}
const count=(n:number)=>new Intl.NumberFormat('es-PE').format(n)

export function DataSources(){
  const [reports,setReports]=useState<SourceReport[]>([])
  const [loading,setLoading]=useState(true)
  const [error,setError]=useState('')
  const [attempt,setAttempt]=useState(0)
  const [query,setQuery]=useState('')
  const [status,setStatus]=useState('')
  useEffect(()=>{
    let alive=true
    setLoading(true);setError('')
    api<SourceReport[]>('/admin/fuentes').then(r=>{if(alive)setReports(r)}).catch(e=>{if(alive)setError(e.message)}).finally(()=>{if(alive)setLoading(false)})
    return()=>{alive=false}
  },[attempt])
  return <>
    <p className="eyebrow">ADQUISICIÓN Y CALIDAD DE DATOS</p>
    <h1>Fuentes de datos</h1>
    <p>Los conteos de fuentes externas se muestran aparte de las incidencias registradas en el prototipo. Una fila administrativa no equivale a una descripción disponible para entrenar.</p>
    {loading?<p role="status">Cargando fuentes…</p>:error?<div role="alert" className="notice error"><p>{error}</p><button className="secondary" onClick={()=>setAttempt(n=>n+1)}>Reintentar</button></div>:reports.length===0?<div className="notice">No hay fuentes inspeccionadas importadas. Ejecute el comando de análisis desde el README.</div>:reports.map(r=>{
      const topics=r.topics.filter(t=>(!status||t.estado_mapeo===status)&&t.tema_original.toLocaleLowerCase('es').includes(query.toLocaleLowerCase('es')))
      return <section key={r.source_id}>
        <h2>{r.entity} · {r.location}</h2>
        <div className="stats">
          <article><span>Registros históricos</span><strong>{count(r.rows)}</strong></article>
          <article><span>Etiquetas temáticas distintas</span><strong>{r.unique_topic_labels}</strong></article>
          <article><span>Textos extraídos para entrenamiento</span><strong>{r.training_rows_extracted}</strong></article>
          <article><span>Periodo observado</span><p>{r.period.from} → {r.period.to}</p></article>
        </div>
        <div className="notice"><strong>{r.has_free_text?'Fuente con texto por revisar':'Esta fuente no contiene descripciones libres.'}</strong><p>{r.exclusion_reasons.join('. ')}.</p><p>El modelo activo conserva su versión. Las correspondencias siguientes son orientativas y no cuentan como anotación humana validada.</p></div>
        <div className="two-col">
          <div className="card"><h2>Correspondencia temática orientativa</h2>
            {Object.entries(r.by_category).map(([c,n])=><div className="bar-row" key={c}><span>{c} · {categories[c as Category]}</span><b>{count(n)}</b><div className="bar"><i style={{width:`${n/r.rows*100}%`}}/></div></div>)}
            <p className="field-help">Denominador: {count(r.rows)} registros externos. C6 carece de una etiqueta inequívoca en el mapeo documentado. Esto no describe la distribución de Juliaca.</p>
          </div>
          <div className="card"><h2>Calidad y alcance del mapeo</h2>{Object.entries(r.by_mapping_status).map(([s,n])=><p className="count-row" key={s}><span>{labels[s]||s}</span><b>{count(n)}</b></p>)}
            <h3>Tipo de registro original</h3>{Object.entries(r.by_type).map(([s,n])=><p className="count-row" key={s}><span>{s||'Vacío'}</span><b>{count(n)}</b></p>)}
            <p className="field-help">No se exportan identificadores, coordenadas ni filas individuales desde esta vista.</p>
          </div>
        </div>
        <div className="card"><h2>Registros por año</h2><div className="table-wrap"><table><thead><tr><th>Año</th><th>Registros</th></tr></thead><tbody>{r.by_year.map(y=><tr key={y.anio}><td>{y.anio}</td><td>{count(y.registros)}</td></tr>)}</tbody></table></div></div>
        <h2>Etiquetas de origen y criterios</h2>
        <div className="form-grid">
          <label>Buscar tema original<input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Limpieza, alumbrado, aceras…"/></label>
          <label>Estado de correspondencia<select value={status} onChange={e=>setStatus(e.target.value)}><option value="">Todos</option>{Object.entries(labels).map(([s,l])=><option key={s} value={s}>{l}</option>)}</select></label>
        </div>
        <p className="field-help">{topics.length} etiquetas mostradas; frecuencias preservadas, sin completar categorías artificialmente.</p>
        <div className="table-wrap"><table><thead><tr><th>Tema original</th><th>Registros</th><th>Categoría orientativa</th><th>Criterio</th></tr></thead><tbody>{topics.map(t=><tr key={t.tema_original}><td>{t.tema_original||'Sin tema'}</td><td>{count(t.registros)}</td><td>{t.categoria_orientativa||'Sin asignación'}</td><td>{labels[t.estado_mapeo]}<small>{t.motivo}</small></td></tr>)}</tbody></table>{topics.length===0&&<p>No hay etiquetas con estos filtros.</p>}</div>
        <details className="card"><summary>Procedencia, atribución y limitaciones</summary><p>{r.attribution}</p><p>{r.license}</p><p><a href={r.source_url} target="_blank" rel="noreferrer">Catálogo oficial</a> · <a href={r.license_url} target="_blank" rel="noreferrer">Condiciones publicadas por la fuente</a></p><p>SHA-256 del original: <code>{r.sha256}</code></p><ul>{r.limitations.map(l=><li key={l}>{l}</li>)}</ul></details>
      </section>
    })}
  </>
}
