// Guarda só os arquivos do app para funcionar sem internet. Nenhum dado pessoal passa por aqui.
const CACHE='financas-e918d5982d';
const FILES=['./','./index.html','./manifest.webmanifest','./icon-192.png','./icon-512.png'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(CACHE).then(c=>c.addAll(FILES)).then(()=>self.skipWaiting()))});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim()))});
self.addEventListener('fetch',e=>{
  const u=new URL(e.request.url);
  if(e.request.method!=='GET'||u.origin!==location.origin) return; // Google Drive e qualquer outro site passam direto
  e.respondWith(caches.match(e.request,{ignoreSearch:true}).then(r=>{
    const net=fetch(e.request).then(resp=>{ if(resp.ok) caches.open(CACHE).then(c=>c.put(e.request,resp.clone())); return resp; }).catch(()=>r);
    return r||net;
  }));
});
