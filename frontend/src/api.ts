export type Category = 'C1'|'C2'|'C3'|'C4'|'C5'|'C6'|'C7'|'C8'
export const categories: Record<Category,string> = {C1:'Limpieza pública y residuos sólidos',C2:'Infraestructura urbana y drenaje pluvial',C3:'Transporte, tránsito y seguridad vial',C4:'Seguridad ciudadana y Serenazgo',C5:'Parques, áreas verdes y ornato',C6:'Comercio y fiscalización municipal',C7:'Alumbrado público',C8:'Agua y alcantarillado'}
export const states = ['Pendiente de revisión','Sugerencia disponible','Revisado','Derivado','Resuelto']
export interface Destination {area:string|null;confirmada:boolean;mensaje:string;validada:boolean;vigente:boolean;desde:string|null;hasta:string|null;version:string|null;origen:string}
export interface Classification {tema:Category|null; puntuacion:number|null; tipo_puntuacion:string|null; requiere_revision:boolean; motivos_revision:string[]; destino_sugerido:string|null; destino?:Destination|null; prioridad:string; evaluacion_prioridad?:{nivel:string;motivo:string;evidencias:{fragmento:string;criterio:string}[];version:string;requiere_revision:boolean}|null; alerta_posible_urgencia:boolean; motivo_urgencia:string|null; estado:string; version_modelo:string|null; version_umbral:string|null; version_reglas:string|null; demostrativo:boolean}
export interface Registration {id:string; codigo:string; secreto_seguimiento:string; clasificacion:Classification}
export interface Incident {id:string; code:string; state:string; current_topic:Category|null; current_destination:string|null; created_at:string; revision:number}
export interface History {id:string; state:string; previous:string|null; reason:string; evidence:string|null; created_at:string; user_id:string|null}
export interface Review {id:string; original_topic:Category|null; topic:Category|null; original_destination:string|null; destination:string|null; reason:string; created_at:string; user_id:string}
export interface Detail extends Incident {texto:string; ubicacion_general:string|null; prediccion:Classification; revisiones:Review[]; historial:History[];latencia_ms:number}
export interface Rule {id?:string; category:Category; territory:string; destination:string; conditions:string; validated:boolean; valid_from:string; valid_until:string; source:string; responsible:string; version:number; active:boolean}
export interface Stats {total:number;por_categoria:Record<Category,number>;sin_tema:number;por_estado:Record<string,number>;motivos_revision:Record<string,number>;revisados:number;correcciones:number;latencia_media_ms:number|null;tasa_revision_inicial:number|null;correcciones_por_categoria:Record<string,number>}
export interface Session {usuario:string;rol:'administrador'|'revisor';csrf_token:string}
export interface TraceStage {id:string;nombre:string;estado:string;motivo:string;entrada:Record<string,unknown>;salida:Record<string,unknown>;transformaciones:string[];version:string|null;tiempo_ms:number;limitacion:string|null}
export interface Extraction {version:string;campos:Record<string,{valor:string|null;evidencia:string|null;origen:string|null}>;limite:string}
export interface Analysis {version_traza:string;version_modelo:string|null;valida:boolean;simulacion:boolean;etapas:TraceStage[];clasificacion:Classification|null;extraccion:Extraction|Record<string,never>;preguntas:{id:string;pregunta:string}[];tiempo_total_ms:number}
export interface AnalysisVersion {version:number;original:string;respuestas:Record<string,string>;analisis:Analysis;fecha:string}
export class ApiError extends Error {
  constructor(message:string,public readonly status:number){super(message);this.name='ApiError'}
}
export async function api<T>(path:string, method='GET', body?:unknown, headers:Record<string,string>={}):Promise<T> {
  const response = await fetch(`/api/v1${path}`,{method,credentials:'include',headers:{'Content-Type':'application/json','X-CSRF-Token':sessionStorage.getItem('csrf')||'',...headers},body:body===undefined?undefined:JSON.stringify(body)})
  if(!response.ok){const value=await response.json().catch(()=>({detail:'No se pudo leer la respuesta'}));throw new ApiError(typeof value.detail==='string'?value.detail:response.status===422?'Revise los campos del formulario':`Error ${response.status}`,response.status)}
  return response.status===204?undefined as T:response.json()
}
export function date(value:string){return new Intl.DateTimeFormat('es-PE',{dateStyle:'medium',timeStyle:'short',timeZone:'America/Lima'}).format(new Date(value.endsWith('Z')||/[+-]\d\d:\d\d$/.test(value)?value:value+'Z'))}
