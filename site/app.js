let rows=[], layer="gap", scenario="ewa", region="world", worldData=null, dataBase="data", manifest=null;
const fmt=d3.format(".2f");
const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
async function jsonIfOk(url){const r=await fetch(url,{cache:"no-store"});if(!r.ok)throw new Error(url+" -> "+r.status);return r.json()}
async function boot(){
  try{
    try{manifest=await jsonIfOk("data/real/manifest.json");dataBase="data/real";rows=await jsonIfOk(dataBase+"/summary.json")}
    catch(_){manifest=await jsonIfOk("data/manifest.json");dataBase="data";rows=await jsonIfOk(dataBase+"/summary.json")}
    worldData=await jsonIfOk("https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json");
    renderManifest(manifest); draw(worldData);
  }catch(e){document.getElementById("status-banner").textContent="DATA LOAD FAILED · "+e.message;console.error(e)}
}
function isEmpirical(){return String(manifest?.data_status||"").toUpperCase()==="EMPIRICAL"}
function renderManifest(m){
 const empirical=isEmpirical();
 document.getElementById("status-banner").textContent=empirical?("EMPIRICAL EWA · EXIOBASE "+m.year+" · STATIC COUNTERFACTUAL"): "RESEARCH PROTOTYPE · SYNTHETIC DEMONSTRATION DATA · NOT EMPIRICAL FINDINGS";
 if(empirical&&m.embodied_labor){const e=m.embodied_labor;document.getElementById("global-results").innerHTML=`<div><b>Physical embodied labour</b><br>South → North: ${fmt(e.south_to_north_hours/1e9)} bn h · North → South: ${fmt(e.north_to_south_hours/1e9)} bn h · Net: ${fmt(e.net_south_to_north_hours/1e9)} bn h</div><div><b>Valuation comparison</b><br>Northern-wage all-skill: €${fmt(e.hickel_style_all_skill_value_eur/1e12)} tn · EWA origin wage: €${fmt(e.ewa_origin_wage_value_eur/1e12)} tn</div><div><b>Release validation</b><br>${m.validation?.passed?"PASS":"FAIL"} · price residual ${Number(m.validation?.equal_price_residual||0).toExponential(2)}</div>`;}
 document.getElementById("manifest").innerHTML=empirical
 ? `<p><b>Data:</b> EMPIRICAL<br><b>Year:</b> ${esc(m.year)}<br><b>Countries:</b> ${esc(m.countries)}<br><b>Cells:</b> ${esc(m.cells)}<br><b>PPP:</b> ${esc(m.ppp)}<br><b>Productivity:</b> ${esc(m.productivity)}</p>`
 : `<p><b>Model:</b> v${esc(m.model_version)}<br><b>Data:</b> ${esc(m.data_status)}<br><b>Conservation test:</b> ${m.conservation_passed?"PASS":"FAIL"}</p>`;
}
function numericToIso3(id){
 const n=Number(id);
 if(!Number.isFinite(n))return null;
 try{
   const region=new Intl.DisplayNames(["en"],{type:"region"});
   const iso2=region.of(String(n).padStart(3,"0"));
 }catch(_){}
 return null;
}
// world-atlas uses ISO 3166-1 numeric IDs. This table is generated from the
// empirical rows' ISO3 codes using a compact ISO numeric mapping loaded below.
let isoNum={};
async function loadIsoMap(){
 try{isoNum=await jsonIfOk("data/iso_numeric_to_iso3.json")}catch(_){
   isoNum={"840":"USA","276":"DEU","076":"BRA","356":"IND","050":"BGD","710":"ZAF"};
 }
}
function metric(r){
 if(scenario==="hickel"&&layer==="gap")return +(r.hickel_gap_eur_per_hour??r.gap??0);
 if(layer==="actual")return +(r.actual_hourly_comp_eur??r.actual??0);
 if(layer==="equal")return +(scenario==="hickel"?(r.hickel_hourly_comp_eur??r.equal??0):(r.equal_hourly_comp_eur??r.equal??0));
 if(layer==="trade")return +(r.trade_hierarchy_net_million_eur??0);
 if(layer==="price")return +(r.mean_price_gap??0);
 return +(r.wage_gap_eur_per_hour??r.gap??0);
}
function draw(world){
 const svg=d3.select("#map");svg.selectAll("*").remove();
 const features=topojson.feature(world,world.objects.countries).features;
 const shown=rows.filter(d=>region==="world"||region==="compare"||String(d.region_group||"").toLowerCase()===region);
 const by=new Map(shown.map(d=>[d.iso3,d]));
 const vals=shown.map(metric).filter(Number.isFinite), max=Math.max(...vals.map(Math.abs),1);
 const color=d3.scaleDiverging([-max,0,max],d3.interpolateBrBG);
 const projection=d3.geoNaturalEarth1().fitSize([960,500],{type:"FeatureCollection",features}), path=d3.geoPath(projection);
 svg.selectAll("path").data(features).join("path")
  .attr("class",d=>"country "+(by.has(isoNum[String(d.id).padStart(3,"0")])?"hasdata":""))
  .attr("d",path).attr("fill",d=>{const r=by.get(isoNum[String(d.id).padStart(3,"0")]);return r?color(metric(r)):null})
  .on("click",(e,d)=>{const iso=isoNum[String(d.id).padStart(3,"0")];if(iso&&by.has(iso))loadCountry(iso)})
  .on("mousemove",(e,d)=>{const r=by.get(isoNum[String(d.id).padStart(3,"0")]);if(!r)return;const t=document.getElementById("tooltip");t.style.display="block";t.style.left=(e.offsetX+12)+"px";t.style.top=(e.offsetY+12)+"px";t.textContent=`${r.iso3} · ${r.region_group||""}: ${fmt(metric(r))}`})
  .on("mouseleave",()=>document.getElementById("tooltip").style.display="none");
 document.getElementById("legend").textContent=(scenario==="hickel"?"Hickel-style":"EWA")+" · "+(region==="world"?"World":region)+" · "+(isEmpirical()?"EXIOBASE "+manifest.year:"demonstration");
}
async function loadCountry(iso){
 const d=await jsonIfOk(`${dataBase}/countries/${iso}.json`);
 document.getElementById("country-title").textContent=(d.country?d.country+" · ":"")+iso;
 if(isEmpirical()){
   document.getElementById("country-note").textContent="Empirical "+d.year+" country-sector aggregation. Positive wage gap means the Equal World hourly compensation exceeds observed compensation under this specification.";
   const steps=[
    ["Actual hourly compensation","C / L",d.actual_hourly_comp_eur,"EUR / hour"],
    ["Equal World hourly compensation","w* (PPP → effective labour → common currency)",d.equal_hourly_comp_eur,"EUR / hour"],
    ["Equal World wage gap","w* − wᴬ",d.wage_gap_eur_per_hour,"EUR / hour"],
    ["Hickel-style Northern wage","wᴺ",d.hickel_hourly_comp_eur,"EUR / hour"],
    ["Hickel-style wage gap","wᴺ − wᴬ",d.hickel_gap_eur_per_hour,"EUR / hour"],
    ["Mean production-price gap","p* / pᴬ − 1",d.mean_price_gap,"relative price"],
    ["Net trade hierarchy transfer","fixed Z revaluation",d.trade_hierarchy_net_million_eur,"million EUR"]
   ];
   document.getElementById("steps").innerHTML=steps.map((s,i)=>`<div class="step"><div class="num">0${i+1}</div><div><h3>${esc(s[0])}</h3><div class="eq">${esc(s[1])}</div></div><div class="value">${fmt(+s[2])}<span class="unit">${esc(s[3])}</span></div></div>`).join("");
 }else{
   document.getElementById("country-note").textContent=d.status+". "+d.interpretation.note;
   document.getElementById("steps").innerHTML=d.steps.map(s=>`<div class="step"><div class="num">0${s.id}</div><div><h3>${esc(s.title)}</h3><div class="eq">${esc(s.equation)}</div>${s.inputs?`<small>${Object.entries(s.inputs).map(([k,v])=>esc(k)+" = "+fmt(v)).join(" · ")}</small>`:""}</div><div class="value">${fmt(s.value)}<span class="unit">${esc(s.unit)}</span></div></div>`).join("");
 }
}
document.getElementById("layer").addEventListener("change",e=>{layer=e.target.value;if(worldData)draw(worldData)});
document.getElementById("scenario").addEventListener("change",e=>{scenario=e.target.value;if(worldData)draw(worldData)});
document.getElementById("region").addEventListener("change",e=>{region=e.target.value;if(worldData)draw(worldData)});
loadIsoMap().then(boot);
