#!/usr/bin/env python3
"""Build napalai v5 from v4 — apply all 10 improvements"""
import re

with open("/home/bill/horoscope_app/templates/index_v4.html") as f:
    c = f.read()

# 1. Title
c = c.replace("Luxury Digital Oracle", "Sentient Astrology")
c = c.replace("NAPA LAI v4", "NAPA LAI v5")

# 2. PWA meta
c = c.replace(
    '<meta name="theme-color" content="#080b12">',
    '<meta name="theme-color" content="#080b12">\n<link rel="manifest" href="/static/manifest.json">\n<meta name="apple-mobile-web-app-capable" content="yes">\n<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">'
)

# 3. Extra CSS (toast, history, modal-actions)
CSS = """
/* ── Toast ── */
.toast{position:fixed;bottom:2rem;left:50%;transform:translateX(-50%);z-index:200;
  background:var(--gold);color:var(--navy-deep);padding:0.7rem 2rem;border-radius:100px;
  font-family:'Anuphan',sans-serif;font-size:0.85rem;font-weight:500;
  opacity:0;pointer-events:none;transition:opacity 0.3s;box-shadow:0 4px 20px rgba(201,168,76,0.3)}
.toast.show{opacity:1}
/* ── History ── */
.history-section{padding-top:var(--space-md)}
.history-list{max-width:420px;margin:0 auto;display:flex;flex-direction:column;gap:0.5rem}
.history-item{font-size:0.78rem;color:var(--ivory-dim);padding:0.6rem 1rem;border-bottom:1px solid rgba(255,255,255,0.04);cursor:pointer;transition:all 0.3s}
.history-item:hover{color:var(--gold)}
.history-item .hi-type{font-size:0.65rem;color:var(--gold-soft);text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.15rem}
.history-item .hi-date{font-size:0.62rem;color:var(--ivory-muted);float:right}
.history-empty{text-align:center;font-size:0.8rem;color:var(--ivory-muted);padding:2rem}
.history-clear{text-align:center;margin-top:1rem}
.history-clear button{background:none;border:1px solid var(--gold-dim);color:var(--ivory-muted);font-size:0.7rem;padding:0.4rem 1.2rem;border-radius:100px;cursor:pointer;font-family:'Anuphan',sans-serif;transition:all 0.3s}
.history-clear button:hover{border-color:var(--gold);color:var(--gold)}
/* ── Modal Actions ── */
.modal-actions{display:flex;gap:0.5rem;margin-top:var(--space-md);flex-wrap:wrap}
.modal-action-btn{flex:1;min-width:80px;font-family:'Anuphan',sans-serif;font-size:0.72rem;font-weight:400;padding:0.5rem 0.8rem;background:rgba(255,255,255,0.04);border:1px solid var(--gold-dim);border-radius:100px;color:var(--ivory-dim);cursor:pointer;text-align:center;transition:all 0.3s}
.modal-action-btn:hover{border-color:var(--gold);color:var(--gold);background:var(--gold-glow)}
"""
c = c.replace("/* ── Responsive ── */", CSS + "\n/* ── Responsive ── */")

# 4. Starfield with IntersectionObserver (pause when not visible)
c = c.replace(
    """(function(){
  const c=document.getElementById('starfield'),x=c.getContext('2d');
  let s=[];const N=100;
  function R(){c.width=innerWidth;c.height=innerHeight}
  function C(){s=[];for(let i=0;i<N;i++)s.push({x:Math.random()*c.width,y:Math.random()*c.height,r:Math.random()*1+0.2,a:Math.random()*0.4+0.1,f:Math.random()*0.004+0.001,d:Math.random()>.5?1:-1})}
  function D(){x.clearRect(0,0,c.width,c.height);for(const t of s){t.a+=t.f*t.d;if(t.a>0.55)t.d=-1;if(t.a<0.08)t.d=1;x.beginPath();x.arc(t.x,t.y,t.r,0,Math.PI*2);x.fillStyle=`rgba(229,218,198,${t.a})`;x.fill()}requestAnimationFrame(D)}
  R();C();D();addEventListener('resize',()=>{R();C()})
})();""",
    """(function(){
  const c=document.getElementById('starfield'),x=c.getContext('2d');
  let s=[],running=true,rafId=null;const N=100;
  function R(){c.width=innerWidth;c.height=innerHeight}
  function C(){s=[];for(let i=0;i<N;i++)s.push({x:Math.random()*c.width,y:Math.random()*c.height,r:Math.random()*1+0.2,a:Math.random()*0.4+0.1,f:Math.random()*0.004+0.001,d:Math.random()>.5?1:-1})}
  function D(){if(!running){rafId=null;return}x.clearRect(0,0,c.width,c.height);for(const t of s){t.a+=t.f*t.d;if(t.a>0.55)t.d=-1;if(t.a<0.08)t.d=1;x.beginPath();x.arc(t.x,t.y,t.r,0,Math.PI*2);x.fillStyle=`rgba(229,218,198,${t.a})`;x.fill()}rafId=requestAnimationFrame(D)}
  function stop(){running=false;if(rafId){cancelAnimationFrame(rafId);rafId=null}}
  function start(){if(!running){running=true;D()}}
  R();C();start();addEventListener('resize',()=>{R();C()});
  new IntersectionObserver(e=>{e[0].isIntersecting?start():stop()},{threshold:0}).observe(c);
})();"""
)

# 5. Add utility JS before FORTUNE_META
NEWJS = """
/* ── API Timeout ── */
function fetchWithTimeout(url,opts,timeout){
  timeout=timeout||10000;
  return Promise.race([
    fetch(url,opts),
    new Promise(function(_,rej){setTimeout(function(){rej(new Error('TIMEOUT'))},timeout)})
  ]);
}
/* ── History ── */
var HK='napalai_history_v5';
function saveToHistory(type,title,reading){
  try{var h=JSON.parse(localStorage.getItem(HK)||'[]');h.unshift({type:type,title:title,reading:reading,ts:new Date().toISOString()});if(h.length>30)h.length=30;localStorage.setItem(HK,JSON.stringify(h));renderHistory()}catch(e){}
}
function getHistory(){try{return JSON.parse(localStorage.getItem(HK)||'[]')}catch(e){return[]}}
function clearHistory(){localStorage.removeItem(HK);renderHistory()}
function renderHistory(){
  var el=document.getElementById('historyList');if(!el)return;
  var h=getHistory();
  if(!h.length){el.innerHTML='<div class="history-empty">ยังไม่มีประวัติการทำนาย</div>';return}
  var html='';
  for(var i=0;i<Math.min(h.length,10);i++){
    html+='<div class="history-item" onclick="replayHistory('+i+')"><div class="hi-type">'+h[i].type+'</div><div class="hi-date">'+new Date(h[i].ts).toLocaleDateString('th-TH')+'</div><div style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'+(h[i].title||h[i].reading.slice(0,60))+'</div></div>';
  }
  el.innerHTML=html;
}
function replayHistory(i){
  var h=getHistory();if(!h[i])return;
  var meta=FORTUNE_META[h[i].type];if(!meta)return;
  openFortune(h[i].type);
  setTimeout(function(){var re=document.getElementById('fortuneResult');if(re)re.innerHTML='<div class="result-block-v4"><p>'+escapeHtml(h[i].reading).replace(/\\n/g,'<br>')+'</p></div>'},300);
}
/* ── Toast ── */
function showToast(msg){
  var t=document.getElementById('toast');if(!t){t=document.createElement('div');t.id='toast';t.className='toast';document.body.appendChild(t)}
  t.textContent=msg;t.classList.add('show');setTimeout(function(){t.classList.remove('show')},2500);
}
/* ── Share ── */
function shareReading(text){
  var url=location.href;var shareText=text.slice(0,200)+(text.length>200?'...':'')+'\\n\\nดูดวงฟรีที่: '+url;
  if(navigator.share){navigator.share({title:'คำทำนายจากนภาลัย',text:shareText}).catch(function(){})}
  else{navigator.clipboard.writeText(shareText).then(function(){showToast('📋 คัดลอกคำทำนายแล้ว!')}).catch(function(){showToast('คัดลอกไม่สำเร็จ')})}
}
"""
c = c.replace("/* ── Fortune Modal ── */", NEWJS + "\n/* ── Fortune Modal ── */")

# 6. Update fetchFortune with timeout + history + share
c = c.replace(
    "const r=await fetch(endpoint,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});\n    const d=await r.json();\n    if(type==='colorme'){renderColorme(d,re);return}\n    let h='<div class=\"result-block-v4\">';\n    const txt=d.reading||d.response||d.result||d.message||JSON.stringify(d,null,2);\n    h+=`<p>${escapeHtml(txt).replace(/\\n/g,'<br>')}</p>`;\n    h+='</div>';re.innerHTML=h;\n  }catch(e){re.innerHTML=`<p style=\"color:#e88;text-align:center\">❌ เกิดข้อผิดพลาด: ${e.message}</p>`}",
    """const r=await fetchWithTimeout(endpoint,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)},12000);
    const d=await r.json();
    if(type==='colorme'){renderColorme(d,re);return}
    var h='<div class="result-block-v4">';
    var txt=d.reading||d.response||d.result||d.message||JSON.stringify(d,null,2);
    var eTxt=escapeHtml(txt);
    h+='<p>'+eTxt.replace(/\\n/g,'<br>')+'</p>';
    h+='</div>';
    h+='<div class="modal-actions"><button class="modal-action-btn" onclick="shareReading(\\''+eTxt.replace(/'/g,'\\\\\\'').slice(0,180)+'\\')">📤 แชร์</button><button class="modal-action-btn" onclick="navigator.clipboard.writeText(\\''+eTxt.replace(/'/g,'\\\\\\'').slice(0,300)+'\\').then(function(){showToast(\\'📋 คัดลอกแล้ว!\\')})">📋 คัดลอก</button></div>';
    re.innerHTML=h;
    saveToHistory(type,meta.title,txt);
  }catch(e){if(e.message==='TIMEOUT'){re.innerHTML='<p style=\"color:#e88;text-align:center\">⏰ ระบบกำลังประมวลผลนานกว่าปกติ กรุณาลองใหม่อีกครั้ง</p>'}else{re.innerHTML='<p style=\"color:#e88;text-align:center\">❌ เกิดข้อผิดพลาด: '+escapeHtml(e.message)+'</p>'}}"""
)

# 7. Phone validation
c = c.replace(
    "phone:()=>{const v=document.getElementById('fortuneInput')?.value.trim();return v?{number:v}:null},",
    "phone:function(){var v=document.getElementById('fortuneInput');if(!v)return null;v=v.value.trim();if(!v)return null;var clean=v.replace(/[-\\s]/g,'');if(!/^0\\d{8,9}$/.test(clean)){var re=document.getElementById('fortuneResult');if(re)re.innerHTML='<p style=\"color:#e88;text-align:center\">⚠ กรุณากรอกเบอร์โทร 10 หลัก (เช่น 0812345678)</p>';var b=document.querySelector('.modal-btn-v4');if(b){b.disabled=false;b.textContent='🔮 ดูดวงเลย'};return null}return{number:v}},"
)

# 8. loadDaily timeout
c = c.replace("const cr=await fetch('/api/colorme'", "const cr=await fetchWithTimeout('/api/colorme'")
c = c.replace("const tr=await fetch('/api/tarot'", "const tr=await fetchWithTimeout('/api/tarot'")

# 9. SW + renderHistory init
c = c.replace(
    "window.addEventListener('DOMContentLoaded',()=>{const h=location.hash.replace('#','');if(h&&FORTUNE_META[h])openFortune(h)});",
    "if('serviceWorker' in navigator){navigator.serviceWorker.register('/static/sw.js').catch(function(){})}\nwindow.addEventListener('DOMContentLoaded',function(){renderHistory();var h=location.hash.replace('#','');if(h&&FORTUNE_META[h])openFortune(h)});"
)

# 10. HTML body additions (toast + history section)
c = c.replace(
    "</body>",
    """
<div id="toast" class="toast"></div>

<!-- ═══════ HISTORY ═══════ -->
<section class="history-section" style="padding-bottom:var(--space-xl)">
  <div class="section-label reveal" style="margin-top:1rem">✦ Your Journey ✦</div>
  <h2 class="section-title reveal reveal-d1" style="font-size:clamp(1.4rem,4vw,1.8rem)">ประวัติการทำนาย</h2>
  <div class="section-divider"></div>
  <div class="history-list" id="historyList">
    <div class="history-empty">กำลังโหลด...</div>
  </div>
  <div class="history-clear reveal reveal-d2">
    <button onclick="clearHistory()">🗑 ล้างประวัติ</button>
  </div>
</section>

</body>"""
)

with open("/home/bill/horoscope_app/templates/index_v5.html", "w") as f:
    f.write(c)

print("✅ v5 built —", len(c), "chars")
