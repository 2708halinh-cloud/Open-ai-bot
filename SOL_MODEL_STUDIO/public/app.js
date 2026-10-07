const $=s=>document.querySelector(s);

const defaults={
  preset:"sol",
  provider:"ollama",
  endpoint:"http://127.0.0.1:11434",
  model:"ggdv-human-sol:1.0",
  temperature:.65,
  num_ctx:16384,
  system:""
};

const presets={
  sol:{provider:"ollama",endpoint:"http://127.0.0.1:11434",model:"ggdv-human-sol:1.0",temperature:.65,num_ctx:16384,system:""},
  xtime:{provider:"ollama",endpoint:"http://127.0.0.1:11434",model:"x-time-ggdv-human:1.0",temperature:.35,num_ctx:32768,system:""},
  coder:{provider:"ollama",endpoint:"http://127.0.0.1:11434",model:"ggdv-human-sol-coder:1.0",temperature:.2,num_ctx:32768,system:""}
};

let cfg={...defaults,...JSON.parse(localStorage.getItem("solstudio_cfg")||"{}")};
let messages=JSON.parse(localStorage.getItem("solstudio_chat")||"[]");

function save(){
  const safe={...cfg};
  delete safe.apiKey;
  localStorage.setItem("solstudio_cfg",JSON.stringify(safe));
  localStorage.setItem("solstudio_chat",JSON.stringify(messages));
}

function providerDefaults(p){
  if(p==="ollama")return {endpoint:"http://127.0.0.1:11434",model:"ggdv-human-sol:1.0"};
  if(p==="openai")return {endpoint:"http://127.0.0.1:1234/v1",model:"local-model"};
  return {endpoint:"http://127.0.0.1:8080/v1",model:"Hermes"};
}

function bind(){
  $("#preset").value=cfg.preset||"custom";
  $("#provider").value=cfg.provider;
  $("#endpoint").value=cfg.endpoint;
  $("#temp").value=cfg.temperature;
  $("#tempN").textContent=cfg.temperature;
  $("#ctx").value=String(cfg.num_ctx);
  $("#system").value=cfg.system||"";
  const labels={sol:"GGDV HUMAN SOL 1.0",xtime:"X‑TIME · GGDV HUMAN 1.0",coder:"GGDV HUMAN SOL CODER",custom:"CUSTOM RUNTIME"};
  $("#title").textContent=labels[cfg.preset]||labels.custom;
}

function draw(){
  const c=$("#chat");
  c.innerHTML="";
  for(const m of messages){
    const d=document.createElement("div");
    d.className="msg "+m.role;
    const meta=document.createElement("div");
    meta.className="meta";
    meta.textContent=m.role==="user"?"YOU":"SOL";
    const t=document.createElement("div");
    t.textContent=m.content;
    d.append(meta,t);
    c.appendChild(d);
  }
  c.scrollTop=c.scrollHeight;
}

async function post(url,body){
  const r=await fetch(url,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
  const d=await r.json();
  if(!r.ok)throw new Error(d.error+(d.detail?" · "+JSON.stringify(d.detail):""));
  return d;
}

function setStatus(t,c=""){
  $("#status").textContent=t;
  $("#status").className="status "+c;
}

async function refreshModels(){
  setStatus("LOADING");
  try{
    const provider=cfg.provider==="ollama"?"ollama":"openai";
    const d=await post("/api/models",{provider,endpoint:cfg.endpoint,apiKey:$("#apiKey").value});
    const sel=$("#model");
    sel.innerHTML="";
    for(const m of d.models){
      const o=document.createElement("option");
      o.value=m.id;o.textContent=m.label;
      sel.appendChild(o);
    }
    if([...sel.options].some(o=>o.value===cfg.model)) sel.value=cfg.model;
    else if(sel.options[0]) cfg.model=sel.options[0].value;
    save();
    setStatus(d.models.length+" MODELS","ok");
  }catch(e){
    setStatus("MODEL ERR","bad");
    $("#sub").textContent=e.message;
  }
}

async function health(){
  setStatus("CHECK…");
  try{
    const provider=cfg.provider==="ollama"?"ollama":"openai";
    const d=await post("/api/health",{provider,endpoint:cfg.endpoint,apiKey:$("#apiKey").value});
    setStatus("ONLINE","ok");
    $("#sub").textContent=(d.provider||cfg.provider)+" · "+cfg.endpoint;
  }catch(e){
    setStatus("OFFLINE","bad");
    $("#sub").textContent=e.message;
  }
}

async function send(){
  const input=$("#input");
  const text=input.value.trim();
  if(!text)return;
  input.value="";
  messages.push({role:"user",content:text});
  draw();save();
  $("#send").disabled=true;
  setStatus("THINKING…");
  try{
    const chain=[];
    if((cfg.system||"").trim())chain.push({role:"system",content:cfg.system.trim()});
    chain.push(...messages.slice(-30));
    const provider=cfg.provider==="ollama"?"ollama":"openai";
    const d=await post("/api/chat",{provider,endpoint:cfg.endpoint,apiKey:$("#apiKey").value,model:cfg.model,messages:chain,temperature:cfg.temperature,num_ctx:cfg.num_ctx});
    messages.push({role:"assistant",content:d.reply||"(empty response)"});
    setStatus("ONLINE","ok");
  }catch(e){
    messages.push({role:"assistant",content:"[RUNTIME ERROR] "+e.message});
    setStatus("ERROR","bad");
  }finally{
    $("#send").disabled=false;
    save();draw();
  }
}

$("#preset").onchange=e=>{
  const k=e.target.value;
  if(presets[k]){
    cfg={...cfg,...presets[k],preset:k};
    bind();save();refreshModels();health();
  }else{
    cfg.preset="custom";save();bind();
  }
};

$("#provider").onchange=e=>{
  cfg.preset="custom";
  cfg.provider=e.target.value;
  Object.assign(cfg,providerDefaults(cfg.provider));
  bind();save();refreshModels();
};
$("#endpoint").onchange=e=>{cfg.preset="custom";cfg.endpoint=e.target.value.trim();save();bind()};
$("#model").onchange=e=>{cfg.model=e.target.value;save()};
$("#temp").oninput=e=>{cfg.temperature=Number(e.target.value);$("#tempN").textContent=cfg.temperature;save()};
$("#ctx").onchange=e=>{cfg.num_ctx=Number(e.target.value);save()};
$("#system").onchange=e=>{cfg.system=e.target.value;save()};
$("#refreshModels").onclick=refreshModels;
$("#health").onclick=health;
$("#send").onclick=send;
$("#input").onkeydown=e=>{if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();send()}};
$("#newChat").onclick=()=>{messages=[];save();draw()};
$("#export").onclick=()=>{
  const safe={...cfg};delete safe.apiKey;
  const b=new Blob([JSON.stringify({schema:"SOL_MODEL_STUDIO/1.0",cfg:safe,messages},null,2)],{type:"application/json"});
  const a=document.createElement("a");a.href=URL.createObjectURL(b);a.download="sol-model-studio-session.json";a.click();
  setTimeout(()=>URL.revokeObjectURL(a.href),1000);
};
$("#import").onchange=async e=>{
  try{
    const f=e.target.files?.[0];if(!f)return;
    const o=JSON.parse(await f.text());
    if(o.schema!=="SOL_MODEL_STUDIO/1.0")throw new Error("schema");
    cfg={...defaults,...o.cfg};
    messages=Array.isArray(o.messages)?o.messages:[];
    bind();draw();save();refreshModels();health();
  }catch{
    alert("Sai schema SOL_MODEL_STUDIO/1.0");
  }
};

bind();draw();refreshModels();health();