import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname=path.dirname(fileURLToPath(import.meta.url));
const PUBLIC=path.join(__dirname,"public");
const HOST=process.env.SOL_STUDIO_HOST||"127.0.0.1";
const PORT=Number(process.env.SOL_STUDIO_PORT||4789);
const ALLOW_REMOTE=process.env.SOL_ALLOW_REMOTE_ENDPOINTS==="1";

function send(res,code,body,type="application/json; charset=utf-8"){
  const b=Buffer.isBuffer(body)?body:Buffer.from(typeof body==="string"?body:JSON.stringify(body));
  res.writeHead(code,{
    "Content-Type":type,"Content-Length":b.length,"Cache-Control":"no-store",
    "X-Content-Type-Options":"nosniff","Referrer-Policy":"no-referrer"
  });res.end(b);
}
function readJson(req,limit=2_000_000){
  return new Promise((resolve,reject)=>{
    let n=0,parts=[];
    req.on("data",c=>{n+=c.length;if(n>limit){reject(new Error("body_too_large"));req.destroy();}else parts.push(c)});
    req.on("end",()=>{try{resolve(JSON.parse(Buffer.concat(parts).toString("utf8")||"{}"))}catch(e){reject(e)}});
    req.on("error",reject);
  });
}
function isLoopback(host){
  return host==="127.0.0.1"||host==="localhost"||host==="::1"||host==="[::1]";
}
function validatedBase(raw){
  const u=new URL(raw);
  if(!["http:","https:"].includes(u.protocol)) throw new Error("endpoint_scheme");
  if(!ALLOW_REMOTE && !isLoopback(u.hostname)) throw new Error("remote_endpoint_blocked");
  return u.href.replace(/\/$/,"");
}
async function fetchJson(url,opts={}){
  const r=await fetch(url,{...opts,signal:AbortSignal.timeout(180000)});
  const text=await r.text();
  let data;try{data=JSON.parse(text)}catch{data={raw:text}};
  if(!r.ok) throw Object.assign(new Error("upstream_"+r.status),{status:r.status,data});
  return data;
}
function authHeaders(apiKey){
  const h={"Content-Type":"application/json"};
  if(apiKey) h.Authorization="Bearer "+apiKey;
  return h;
}
async function apiHealth(body){
  const base=validatedBase(body.endpoint);
  if(body.provider==="ollama"){
    const v=await fetchJson(base+"/api/version");
    return {ok:true,provider:"ollama",version:v.version||null,endpoint:base};
  }
  const d=await fetchJson(base+"/models",{headers:authHeaders(body.apiKey)});
  return {ok:true,provider:"openai-compatible",models:Array.isArray(d.data)?d.data.length:null,endpoint:base};
}
async function apiModels(body){
  const base=validatedBase(body.endpoint);
  if(body.provider==="ollama"){
    const d=await fetchJson(base+"/api/tags");
    return {models:(d.models||[]).map(x=>({id:x.name,label:x.name,size:x.size||null,details:x.details||null}))};
  }
  const d=await fetchJson(base+"/models",{headers:authHeaders(body.apiKey)});
  return {models:(d.data||[]).map(x=>({id:x.id,label:x.id}))};
}
async function apiChat(body){
  const base=validatedBase(body.endpoint);
  const messages=(body.messages||[]).slice(-40).filter(m=>["system","user","assistant"].includes(m.role)&&typeof m.content==="string");
  const temperature=Math.max(0,Math.min(2,Number(body.temperature??0.7)));
  if(body.provider==="ollama"){
    const d=await fetchJson(base+"/api/chat",{
      method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({model:body.model,messages,stream:false,think:false,options:{temperature,num_ctx:Number(body.num_ctx||8192),num_predict:Number(body.num_predict||384)}})
    });
    return {reply:d?.message?.content||"",model:d.model||body.model,provider:"ollama",raw_meta:{done_reason:d.done_reason||null,total_duration:d.total_duration||null}};
  }
  const d=await fetchJson(base+"/chat/completions",{
    method:"POST",headers:authHeaders(body.apiKey),
    body:JSON.stringify({model:body.model,messages,temperature,stream:false})
  });
  return {reply:d?.choices?.[0]?.message?.content||"",model:d.model||body.model,provider:"openai-compatible",raw_meta:{usage:d.usage||null}};
}
function staticFile(req,res){
  const u=new URL(req.url,"http://localhost");
  const rel=u.pathname==="/"?"/index.html":u.pathname;
  const file=path.normalize(path.join(PUBLIC,rel));
  if(!file.startsWith(PUBLIC)) return send(res,403,"forbidden","text/plain; charset=utf-8");
  fs.readFile(file,(err,b)=>{
    if(err)return send(res,404,"not found","text/plain; charset=utf-8");
    const ext=path.extname(file).toLowerCase();
    const types={".html":"text/html; charset=utf-8",".js":"text/javascript; charset=utf-8",".css":"text/css; charset=utf-8",".json":"application/json; charset=utf-8",".svg":"image/svg+xml"};
    send(res,200,b,types[ext]||"application/octet-stream");
  });
}
const server=http.createServer(async(req,res)=>{
  try{
    if(req.method==="GET"&&req.url==="/api/runtime") return send(res,200,{ok:true,host:HOST,port:PORT,allow_remote_endpoints:ALLOW_REMOTE});
    if(req.method==="POST"&&req.url==="/api/health") return send(res,200,await apiHealth(await readJson(req)));
    if(req.method==="POST"&&req.url==="/api/models") return send(res,200,await apiModels(await readJson(req)));
    if(req.method==="POST"&&req.url==="/api/chat") return send(res,200,await apiChat(await readJson(req)));
    if(req.method==="GET") return staticFile(req,res);
    send(res,405,{error:"method_not_allowed"});
  }catch(e){
    send(res,e?.status||400,{error:e.message||"error",detail:e.data||null});
  }
});
server.listen(PORT,HOST,()=>console.log("SOL MODEL STUDIO http://"+HOST+":"+PORT));
