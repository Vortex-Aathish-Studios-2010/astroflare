export const UPSTREAM = 'https://astroflare.onrender.com';
const ALLOWED = new Map([
 ['/api/schema','GET'],['/api/status','GET'],['/api/evidence','GET'],['/api/nasa/flares','GET'],
 ...['guide/interpret','guide/flow','guide/profile','assess','compare','investigate','report','ask','evidence/verify','research/ask'].map(p=>['/api/'+p,'POST'])
]);
function assetHeaders(asset,request,url){
 const h={'Content-Type':asset.type,'X-Content-Type-Options':'nosniff','Referrer-Policy':'strict-origin-when-cross-origin','Cache-Control':/^(image|font)\//.test(asset.type)||/font|ttf/.test(asset.type)?'public, max-age=86400':'no-cache'};
 if(asset.csp){h['Content-Security-Policy']=asset.csp;h['X-Frame-Options']='DENY';h['Permissions-Policy']='camera=(), microphone=(), geolocation=(), payment=()';h['Cross-Origin-Opener-Policy']='same-origin';}
 if(url.protocol==='https:'||request.headers.get('x-forwarded-proto')==='https')h['Strict-Transport-Security']='max-age=15552000';
 return h;
}
export async function handleRequest(request, fetcher=fetch, upstreamBase=UPSTREAM) {
 const base=(upstreamBase||UPSTREAM).replace(/\/+$/,'');
 const url=new URL(request.url);
 if(url.pathname==='/healthz')return Response.json({ok:true,assessmentEngine:base===UPSTREAM?'remote-original':'local-engine'});
 if(url.pathname.startsWith('/api/')){
  if(!ALLOWED.has(url.pathname))return Response.json({error:'Unknown API route'},{status:404});
  if(request.method!==ALLOWED.get(url.pathname))return Response.json({error:'Method not allowed'},{status:405});
  const controller=new AbortController();const timer=setTimeout(()=>controller.abort(),90000);
  try {
   const body=request.method==='POST'?await request.text():undefined;
   if(body && new TextEncoder().encode(body).length>262144)return Response.json({error:'Request too large'},{status:413});
   const forwarded=request.headers.get('x-forwarded-for');
   const upstream=await fetcher(base+url.pathname,{method:request.method,headers:{'Accept':'application/json',...(body?{'Content-Type':'application/json'}:{}),...(forwarded?{'X-Forwarded-For':forwarded.slice(0,200)}:{})},body,signal:controller.signal,redirect:'manual'});
   if(upstream.status>=300&&upstream.status<400)throw new Error('Unexpected upstream redirect');
   return new Response(upstream.body,{status:upstream.status,headers:{'Content-Type':upstream.headers.get('Content-Type')||'application/json','Cache-Control':'no-store','X-Assessment-Engine':base===UPSTREAM?'original-remote':'local-engine','X-Content-Type-Options':'nosniff',...(upstream.headers.has('Retry-After')?{'Retry-After':upstream.headers.get('Retry-After')}:{})}});
  }catch(error){console.error('ASTROFLARE_UPSTREAM_UNAVAILABLE',{route:url.pathname,name:error?.name,message:String(error?.message||'Unknown fetch failure').slice(0,200)});return Response.json({error:'The assessment engine is temporarily unavailable. Your answers are unchanged. Retry later; the hypothetical demo and NASA explorer still work offline from the engine.'},{status:502});}finally{clearTimeout(timer);}
 }
 if(request.method!=='GET'&&request.method!=='HEAD')return new Response('Method not allowed',{status:405});
 if(url.pathname==='/favicon.ico')return new Response(null,{status:204});
 const asset=ASSETS[url.pathname];if(!asset)return new Response('Not found',{status:404});
 return new Response(request.method==='HEAD'?null:(asset.base64?Uint8Array.from(atob(asset.body),c=>c.charCodeAt(0)):asset.body),{headers:assetHeaders(asset,request,url)});
}
export default {fetch:(request,env)=>handleRequest(request,fetch,env&&env.ASTROFLARE_UPSTREAM)};
