import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { fileURLToPath } from "node:url";

const __dirname=path.dirname(fileURLToPath(import.meta.url));
const PUBLIC=path.join(__dirname,"public");
const HOST=process.env.SOL_STUDIO_HOST||"127.0.0.1";
const PORT=Number(process.env.SOL_STUDIO_PORT||4789);
const ALLOW_REMOTE=process.env.SOL_ALLOW_REMOTE_ENDPOINTS==="1";
const OLLAMA_BASE=(process.env.SOL_OLLAMA_ENDPOINT||"http://127.0.0.1:11434").replace(/\/$/,"");
const API_KEY=(process.env.SOL_STUDIO_API_KEY||"").trim();

function send(res,code,body,type="application/json; charset=utf-8"){
  const b=Buffer.isBuffer(body)?body:Buffer.from(typeof body==="string"?body:JSON.stringify(body));
  res.writeHead(code,{
    "Content-Type":type,
    "Content-Length":b.length,
    "Cache-Control":"no-store",
    "X-Content-Type-Options":"nosniff",
    "Referrer-Policy":"no-referrer"
  });
  res.end(b);
}

function readJson(req,limit=2_000_000){
  return new Promise((resolve,reject)=>{
    let n=0,parts=[];
    req.on("data",c=>{
      n+=c.length;
      if(n>limit){
        reject(new Error("body_too_large"));
        req.destroy();
      }else parts.push(c);
    });
    req.on("end",()=>{
      try{resolve(JSON.parse(Buffer.concat(parts).toString("utf8")||"{}"))}
      catch(e){reject(e)}
    });
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
  let data;
  try{data=JSON.parse(text)}catch{data={raw:text}};
  if(!r.ok) throw Object.assign(new Error("upstream_"+r.status),{status:r.status,data});
  return data;
}

function authHeaders(apiKey){
  const h={"Content-Type":"application/json"};
  if(apiKey) h.Authorization="Bearer "+apiKey;
  return h;
}

function safeEqual(a,b){
  const aa=Buffer.from(a||"");
  const bb=Buffer.from(b||"");
  return aa.length===bb.length && crypto.timingSafeEqual(aa,bb);
}

function requireApiAuth(req,res){
  if(!API_KEY){
    send(res,503,{error:{message:"SOL Studio API key is not configured",type:"server_error",code:"api_key_not_configured"}});
    return false;
  }
  const auth=req.headers.authorization||"";
  const provided=auth.startsWith("Bearer ")?auth.slice(7):"";
  if(!safeEqual(provided,API_KEY)){
    send(res,401,{error:{message:"Invalid API key",type:"invalid_request_error",code:"invalid_api_key"}});
    return false;
  }
  return true;
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
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify({
        model:body.model,
        messages,
        stream:false,
        think:false,
        options:{
          temperature,
          num_ctx:Number(body.num_ctx||8192),
          num_predict:Number(body.num_predict||384)
        }
      })
    });
    return {
      reply:d?.message?.content||"",
      model:d.model||body.model,
      provider:"ollama",
      raw_meta:{done_reason:d.done_reason||null,total_duration:d.total_duration||null}
    };
  }
  const d=await fetchJson(base+"/chat/completions",{
    method:"POST",
    headers:authHeaders(body.apiKey),
    body:JSON.stringify({model:body.model,messages,temperature,stream:false})
  });
  return {
    reply:d?.choices?.[0]?.message?.content||"",
    model:d.model||body.model,
    provider:"openai-compatible",
    raw_meta:{usage:d.usage||null}
  };
}

function mapModelList(tags){
  const now=Math.floor(Date.now()/1000);
  return {
    object:"list",
    data:(tags.models||[]).map(x=>({
      id:x.name,
      object:"model",
      created:now,
      owned_by:"sol-local"
    }))
  };
}

function openAiCompletionId(){
  return "chatcmpl-sol-"+crypto.randomBytes(12).toString("hex");
}

function normalizeOpenAiMessages(input){
  return (input||[])
    .slice(-64)
    .filter(m=>["system","user","assistant","tool"].includes(m.role)&&typeof m.content==="string")
    .map(m=>({role:m.role,content:m.content}));
}

async function openAiModels(req,res){
  if(!requireApiAuth(req,res)) return;
  const d=await fetchJson(OLLAMA_BASE+"/api/tags");
  send(res,200,mapModelList(d));
}

async function openAiChat(req,res){
  if(!requireApiAuth(req,res)) return;
  const body=await readJson(req);
  const model=String(body.model||"ggdv-human-sol:1.0");
  const messages=normalizeOpenAiMessages(body.messages);
  const temperature=Math.max(0,Math.min(2,Number(body.temperature??0.7)));
  const maxTokens=Number(body.max_tokens??body.max_completion_tokens??384);
  const numCtx=Number(body.num_ctx??body.context_length??8192);
  const stream=body.stream===true;
  const id=openAiCompletionId();
  const created=Math.floor(Date.now()/1000);
  const ollamaPayload={
    model,
    messages,
    stream,
    think:false,
    options:{
      temperature,
      num_ctx:numCtx,
      num_predict:maxTokens
    }
  };

  if(!stream){
    const d=await fetchJson(OLLAMA_BASE+"/api/chat",{
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify(ollamaPayload)
    });
    return send(res,200,{
      id,
      object:"chat.completion",
      created,
      model:d.model||model,
      choices:[{
        index:0,
        message:{role:"assistant",content:d?.message?.content||""},
        finish_reason:d.done_reason||"stop"
      }],
      usage:{
        prompt_tokens:Number(d.prompt_eval_count||0),
        completion_tokens:Number(d.eval_count||0),
        total_tokens:Number(d.prompt_eval_count||0)+Number(d.eval_count||0)
      }
    });
  }

  const upstream=await fetch(OLLAMA_BASE+"/api/chat",{
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify(ollamaPayload),
    signal:AbortSignal.timeout(180000)
  });

  if(!upstream.ok){
    const detail=await upstream.text();
    return send(res,upstream.status,{error:{message:detail||"Ollama upstream error",type:"server_error"}});
  }

  res.writeHead(200,{
    "Content-Type":"text/event-stream; charset=utf-8",
    "Cache-Control":"no-cache, no-transform",
    "Connection":"keep-alive",
    "X-Accel-Buffering":"no",
    "X-Content-Type-Options":"nosniff"
  });

  const decoder=new TextDecoder();
  let carry="";
  let sentRole=false;

  const emit=(payload)=>res.write("data: "+JSON.stringify(payload)+"\n\n");

  try{
    for await (const chunk of upstream.body){
      carry+=decoder.decode(chunk,{stream:true});
      const lines=carry.split(/\r?\n/);
      carry=lines.pop()||"";
      for(const line of lines){
        if(!line.trim()) continue;
        let d;
        try{d=JSON.parse(line)}catch{continue}
        const content=d?.message?.content||"";
        if(content||!sentRole){
          emit({
            id,
            object:"chat.completion.chunk",
            created,
            model:d.model||model,
            choices:[{
              index:0,
              delta:{
                ...(sentRole?{}:{role:"assistant"}),
                ...(content?{content}:{})
              },
              finish_reason:null
            }]
          });
          sentRole=true;
        }
        if(d.done){
          emit({
            id,
            object:"chat.completion.chunk",
            created,
            model:d.model||model,
            choices:[{index:0,delta:{},finish_reason:d.done_reason||"stop"}]
          });
        }
      }
    }
  }finally{
    res.write("data: [DONE]\n\n");
    res.end();
  }
}

function staticFile(req,res){
  const u=new URL(req.url,"http://localhost");
  const rel=u.pathname==="/"?"/index.html":u.pathname;
  const file=path.normalize(path.join(PUBLIC,rel));
  if(!file.startsWith(PUBLIC)) return send(res,403,"forbidden","text/plain; charset=utf-8");
  fs.readFile(file,(err,b)=>{
    if(err) return send(res,404,"not found","text/plain; charset=utf-8");
    const ext=path.extname(file).toLowerCase();
    const types={
      ".html":"text/html; charset=utf-8",
      ".js":"text/javascript; charset=utf-8",
      ".css":"text/css; charset=utf-8",
      ".json":"application/json; charset=utf-8",
      ".svg":"image/svg+xml"
    };
    send(res,200,b,types[ext]||"application/octet-stream");
  });
}

const server=http.createServer(async(req,res)=>{
  try{
    if(req.method==="GET"&&req.url==="/api/runtime"){
      return send(res,200,{
        ok:true,
        host:HOST,
        port:PORT,
        allow_remote_endpoints:ALLOW_REMOTE,
        openai_compatible:"/v1",
        api_key_configured:Boolean(API_KEY)
      });
    }

    if(req.method==="POST"&&req.url==="/api/health") return send(res,200,await apiHealth(await readJson(req)));
    if(req.method==="POST"&&req.url==="/api/models") return send(res,200,await apiModels(await readJson(req)));
    if(req.method==="POST"&&req.url==="/api/chat") return send(res,200,await apiChat(await readJson(req)));

    if(req.method==="GET"&&req.url==="/v1/models") return await openAiModels(req,res);
    if(req.method==="POST"&&req.url==="/v1/chat/completions") return await openAiChat(req,res);

    if(req.method==="GET") return staticFile(req,res);
    send(res,405,{error:"method_not_allowed"});
  }catch(e){
    send(res,e?.status||400,{error:e.message||"error",detail:e.data||null});
  }
});

server.listen(PORT,HOST,()=>{
  console.log("SOL MODEL STUDIO http://"+HOST+":"+PORT);
  console.log("OpenAI-compatible endpoint http://"+HOST+":"+PORT+"/v1");
  console.log("API key configured:",Boolean(API_KEY));
});
