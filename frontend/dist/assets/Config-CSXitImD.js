import{A as C,i as g,d as b,o as k,a0 as S,c as j,b as r,w as c,k as d,l as x,a as h,u as y,a4 as N,n as v,L as T,E as p,_ as V}from"./index-DgeW9NR8.js";import{e as Y}from"./toggleHighContrast-CHlMmjzD.js";const B=C("config",()=>{const u=g({}),s=g(""),l=g(!1);async function t(){l.value=!0;try{const o=await(await fetch("/admin/ai/v1/config")).json();o.code===200&&(u.value=o.data,s.value=o.data._raw||"")}catch(e){console.error("Failed to fetch config:",e)}finally{l.value=!1}}async function m(e,o){try{return(await(await fetch("/admin/ai/v1/config",{method:"PUT",headers:{"Content-Type":"application/json"},body:JSON.stringify({path:e,value:o})})).json()).code===200?(await t(),!0):!1}catch(a){return console.error("Failed to update config:",a),!1}}async function _(e){try{return(await(await fetch("/admin/ai/v1/config/raw",{method:"PUT",headers:{"Content-Type":"application/json"},body:JSON.stringify({yaml:e})})).json()).code===200?(await t(),!0):!1}catch(o){return console.error("Failed to save config:",o),!1}}async function i(){try{return(await(await fetch("/admin/ai/v1/config/reload",{method:"POST"})).json()).code===200}catch(e){return console.error("Failed to reload config:",e),!1}}function n(e){const o=e.split(".");let a=u.value;for(const f of o)if(a&&typeof a=="object")a=a[f];else return;return a}return{config:u,rawYaml:s,loading:l,fetchConfig:t,updateConfig:m,saveRawYaml:_,reloadConfig:i,getConfigValue:n}}),F={class:"config"},L={class:"card-header"},w=`# AI Gateway Configuration
# 注意: 此文件通过UI编辑，请勿直接修改文件

ai-gateway:
  virtual_models: {}
  
  databases:
    mongodb:
      host: localhost
      port: 27017
      database: ai_gateway
    redis:
      host: localhost
      port: 6379
      db: 0
    qdrant:
      host: localhost
      port: 6333
      collection: documents
  
  search:
    searxng:
      enabled: true
      url: http://localhost:8080
    librex:
      enabled: true
      url: http://localhost:8081
    fourget:
      enabled: true
      url: http://localhost:8082
`,O=b({__name:"Config",setup(u){const s=B(),l=g();let t=null;k(()=>{l.value&&(t=Y.create(l.value,{value:s.rawYaml||w,language:"yaml",theme:"vs-dark",minimap:{enabled:!1},fontSize:14,lineNumbers:"on",roundedSelection:!1,scrollBeyondLastLine:!1,readOnly:!1,automaticLayout:!0}))}),S(()=>{t==null||t.dispose()});const m=async()=>{if(!t)return;const i=t.getValue();await s.saveRawYaml(i)?p.success("配置保存成功"):p.error("配置保存失败")},_=async()=>{await s.reloadConfig()?(await s.fetchConfig(),t&&t.setValue(s.rawYaml||w),p.success("配置重载成功")):p.error("配置重载失败")};return(i,n)=>{const e=d("el-icon"),o=d("el-button"),a=d("el-button-group"),f=d("el-card");return x(),j("div",F,[r(f,{class:"config-card"},{header:c(()=>[h("div",L,[n[2]||(n[2]=h("span",null,"系统配置 (config.yml)",-1)),r(a,null,{default:c(()=>[r(o,{type:"primary",onClick:m},{default:c(()=>[r(e,null,{default:c(()=>[r(y(N))]),_:1}),n[0]||(n[0]=v("保存 ",-1))]),_:1}),r(o,{onClick:_},{default:c(()=>[r(e,null,{default:c(()=>[r(y(T))]),_:1}),n[1]||(n[1]=v("重载 ",-1))]),_:1})]),_:1})])]),default:c(()=>[h("div",{ref_key:"editorContainer",ref:l,class:"editor-container"},null,512)]),_:1})])}}}),I=V(O,[["__scopeId","data-v-cae6d60e"]]);export{I as default};
//# sourceMappingURL=Config-CSXitImD.js.map
