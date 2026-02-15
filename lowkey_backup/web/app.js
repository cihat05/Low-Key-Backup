let connected = { src:false, dst:false };
let browseCtx = { which:null, path:"/", items:[] };
let editingJobId = null;

async function api(path, method="GET", body=null){
  const opts={method, headers:{}};
  if(body){opts.headers["Content-Type"]="application/json"; opts.body=JSON.stringify(body);}
  const res=await fetch(path, opts);
  const txt=await res.text();
  let data; try{data=JSON.parse(txt);}catch{data=txt;}
  if(!res.ok) throw new Error(data?.detail || txt);
  return data;
}
const q=(id)=>document.getElementById(id);
const esc=(s)=>String(s||"").replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;");

function buildSSH(which){
  const auth=q(which+"_auth").value;
  const secret=q(which+"_secret").value||"";
  return {
    host:q(which+"_host").value.trim(),
    port:parseInt(q(which+"_port").value,10),
    user:q(which+"_user").value.trim(),
    auth_type:auth,
    key_path:auth==="key" ? (secret.trim()||null) : null,
    password:auth==="password" ? (secret||null) : null
  };
}

async function connectSSH(which){
  const btn=q(which+"_connect");
  const st=q(which+"_status");
  btn.disabled=true; st.textContent="connecting...";
  try{
    await api("/api/ssh/test","POST",buildSSH(which));
    connected[which]=true;
    btn.classList.add("ok");
    st.textContent="connected";
    q(which+"_browse").disabled=false;
    maybeAdvance();
  }catch(e){
    connected[which]=false;
    btn.classList.remove("ok");
    st.textContent="ERROR: "+e.message;
    q(which+"_browse").disabled=true;
  }finally{btn.disabled=false;}
}

function maybeAdvance(){
  if(connected.src && connected.dst) q("step_jobcfg").classList.add("active");
}

async function openBrowse(which){
  if(!connected[which]) return;
  browseCtx.which=which;
  browseCtx.path=(which==="src"?q("src_path").value:q("dst_path").value) || "/";
  q("browse_where").textContent=which.toUpperCase();
  q("browse_modal").classList.add("active");
  await loadBrowse();
}
function closeBrowse(){ q("browse_modal").classList.remove("active"); }

async function loadBrowse(){
  q("browse_err").textContent="";
  q("browse_path").value=browseCtx.path;
  q("browse_list").innerHTML="";
  try{
    const data=await api("/api/ssh/browse","POST",{...buildSSH(browseCtx.which), path:browseCtx.path});
    browseCtx.items=data.items;
    q("browse_list").innerHTML=data.items.map((it,idx)=> it.is_dir
      ? `<div class="item" onclick="enterDir(${idx})"><span>📁 ${esc(it.name)}</span><span class="muted">dir</span></div>`
      : `<div class="item"><span>📄 ${esc(it.name)}</span><span class="muted">file</span></div>`
    ).join("");
  }catch(e){ q("browse_err").textContent="ERROR: "+e.message; }
}
function enterDir(idx){
  const it=browseCtx.items[idx]; if(!it||!it.is_dir) return;
  let p=browseCtx.path; if(!p.endsWith("/")) p+="/";
  browseCtx.path=(p==="/" ? "/" : p)+it.name;
  if(!browseCtx.path.startsWith("/")) browseCtx.path="/"+browseCtx.path;
  loadBrowse();
}
function browseUp(){
  let p=browseCtx.path; if(p==="/"||!p) return;
  p=p.replace(/\/+$/,"");
  const parts=p.split("/").filter(Boolean); parts.pop();
  browseCtx.path="/"+parts.join("/"); if(browseCtx.path==="") browseCtx.path="/";
  loadBrowse();
}
function selectBrowse(){
  if(browseCtx.which==="src") q("src_path").value=browseCtx.path;
  else q("dst_path").value=browseCtx.path;
  closeBrowse();
}

function initTime(){
  const sel=q("job_time"); sel.innerHTML="";
  for(let h=0;h<24;h++)for(let m=0;m<60;m++){
    const hh=String(h).padStart(2,"0"), mm=String(m).padStart(2,"0");
    const v=`${hh}:${mm}`; const o=document.createElement("option"); o.value=v; o.textContent=v; sel.appendChild(o);
  }
  sel.value="00:30";
}

function daysSelected(){
  return Array.from(document.querySelectorAll(".day")).filter(x=>x.checked).map(x=>x.value);
}
function jobType(){
  return document.querySelector('input[name="job_type"]:checked')?.value || "FULL";
}

async function saveJob(){
  q("save_msg").textContent="";
  const payload={
    name:q("job_name").value.trim(),
    ...(()=>{
      const s=buildSSH("src");
      return {src_host:s.host,src_port:s.port,src_user:s.user,src_auth_type:s.auth_type,src_key_path:s.key_path,src_password:s.password,src_path:q("src_path").value.trim()};
    })(),
    ...(()=>{
      const d=buildSSH("dst");
      return {dst_host:d.host,dst_port:d.port,dst_user:d.user,dst_auth_type:d.auth_type,dst_key_path:d.key_path,dst_password:d.password,dst_path:q("dst_path").value.trim()};
    })(),
    days:daysSelected(),
    time_hhmm:q("job_time").value,
    keep:q("job_keep").value,
    type:jobType()
  };
  if(!payload.name){ q("save_msg").textContent="Backupname fehlt."; return; }
  if(payload.days.length===0){ q("save_msg").textContent="Bitte mindestens 1 Tag wählen."; return; }
  try{
    if(editingJobId){ await api("/api/jobs/"+editingJobId,"PUT",payload); q("save_msg").textContent="Updated."; }
    else { await api("/api/jobs","POST",payload); q("save_msg").textContent="Saved."; }
    editingJobId=null;
    await loadJobs();
  }catch(e){ q("save_msg").textContent="ERROR: "+e.message; }
}

async function loadJobs(){
  const body=q("jobs_body"); body.innerHTML="";
  const jobs=await api("/api/jobs");
  for(const j of jobs){
    const tr=document.createElement("tr");
    const days=(j.days||"").split(",").filter(Boolean).join(", ");
    tr.innerHTML=`
      <td>${esc(j.name)}</td>
      <td>${esc(days)}</td>
      <td>${esc(j.time_hhmm)}</td>
      <td>${esc(j.keep)}</td>
      <td>${esc(j.type)}</td>
      <td><div class="actions">
        <button class="btn" onclick="editJob(${j.id})">Edit</button>
        <button class="btn bad" onclick="deleteJob(${j.id})">Delete</button>
      </div></td>
      <td>${esc(j.src_host)} → ${esc(j.dst_host)}<br><span class="muted">${esc(j.src_path)} | ${esc(j.dst_path)}</span></td>
    `;
    body.appendChild(tr);
  }
}

async function editJob(id){
  const jobs=await api("/api/jobs");
  const j=jobs.find(x=>x.id===id); if(!j) return;
  editingJobId=id;
  q("job_name").value=j.name;
  q("src_host").value=j.src_host; q("src_port").value=j.src_port; q("src_user").value=j.src_user; q("src_auth").value=j.src_auth_type;
  q("src_secret").value=(j.src_auth_type==="key"? (j.src_key_path||"") : (j.src_password||""));
  q("src_path").value=j.src_path;
  q("dst_host").value=j.dst_host; q("dst_port").value=j.dst_port; q("dst_user").value=j.dst_user; q("dst_auth").value=j.dst_auth_type;
  q("dst_secret").value=(j.dst_auth_type==="key"? (j.dst_key_path||"") : (j.dst_password||""));
  q("dst_path").value=j.dst_path;
  q("job_time").value=j.time_hhmm; q("job_keep").value=j.keep;
  document.querySelectorAll(".day").forEach(cb=>cb.checked=(j.days||"").split(",").includes(cb.value));
  document.querySelectorAll('input[name="job_type"]').forEach(r=>r.checked=(r.value===j.type));
  q("step_jobcfg").classList.add("active");
  q("save_msg").textContent="Edit mode.";
}

async function deleteJob(id){
  if(!confirm("Delete job?")) return;
  await api("/api/jobs/"+id,"DELETE");
  await loadJobs();
}

initTime();
loadJobs();
