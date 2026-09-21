const isoNum={"840":"USA","276":"DEU","076":"BRA","356":"IND","050":"BGD","710":"ZAF"};
let rows=[], layer="gap";
const fmt=d3.format(".2f");
Promise.all([
 fetch("data/summary.json").then(r=>r.json()),
 fetch("data/manifest.json").then(r=>r.json()),
 fetch("https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json").then(r=>r.json())
]).then(([s,m,world])=>{rows=s; renderManifest(m); draw(world);});
function renderManifest(m){document.getElementById("manifest").innerHTML=`<p><b>Model:</b> v${m.model_version}<br><b>Data:</b> ${m.data_status}<br><b>Conservation test:</b> ${m.conservation_passed?"PASS":"FAIL"}</p>`}
function draw(world){
 const svg=d3.select("#map"), features=topojson.feature(world,world.objects.countries).features;
 const projection=d3.geoNaturalEarth1().fitSize([960,500],{type:"FeatureCollection",features}), path=d3.geoPath(projection);
 const by=new Map(rows.map(d=>[d.iso3,d]));
 const vals=rows.map(d=>d[layer]); const extent=d3.extent(vals.map(Math.abs)); const max=Math.max(...vals.map(Math.abs),1);
 const color=d3.scaleDiverging([-max,0,max],d3.interpolateBrBG);
 svg.selectAll("path").data(features).join("path").attr("class",d=>"country "+(by.has(isoNum[d.id])?"hasdata":""))
  .attr("d",path).attr("fill",d=>{const r=by.get(isoNum[d.id]);return r?color(r[layer]):null})
  .on("click",(e,d)=>{const iso=isoNum[d.id];if(iso) loadCountry(iso)})
  .on("mousemove",(e,d)=>{const r=by.get(isoNum[d.id]);if(!r)return; const t=document.getElementById("tooltip");t.style.display="block";t.style.left=(e.offsetX+12)+"px";t.style.top=(e.offsetY+12)+"px";t.textContent=`${r.country}: ${fmt(r[layer])}`})
  .on("mouseleave",()=>document.getElementById("tooltip").style.display="none");
 document.getElementById("legend").textContent="Demo values · international $ / hour";
}
async function loadCountry(iso){
 const d=await fetch(`data/countries/${iso}.json`).then(r=>r.json());
 document.getElementById("country-title").textContent=d.country;
 document.getElementById("country-note").textContent=d.status+". "+d.interpretation.note;
 document.getElementById("steps").innerHTML=d.steps.map(s=>`<div class="step"><div class="num">0${s.id}</div><div><h3>${s.title}</h3><div class="eq">${s.equation}</div>${s.inputs?`<small>${Object.entries(s.inputs).map(([k,v])=>k+" = "+fmt(v)).join(" · ")}</small>`:""}</div><div class="value">${fmt(s.value)}<span class="unit">${s.unit}</span></div></div>`).join("");
}
document.getElementById("layer").addEventListener("change",e=>{layer=e.target.value;location.reload()});
