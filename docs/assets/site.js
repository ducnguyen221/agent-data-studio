// powerbi-agent shared site JS: sticky header, reveal, copy, quick-nav highlight, netbg
(function(){
  var h=document.getElementById('siteHeader');
  if(h){var f=function(){h.classList.toggle('scrolled',window.scrollY>8)};window.addEventListener('scroll',f,{passive:true});f();}
})();
(function(){
  var reduce=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var els=document.querySelectorAll('.reveal');
  if(reduce||!('IntersectionObserver' in window)){els.forEach(function(e){e.classList.add('in')});return;}
  var io=new IntersectionObserver(function(es){es.forEach(function(en){
    if(en.isIntersecting){en.target.classList.add('in');io.unobserve(en.target);}
  })},{threshold:0.12,rootMargin:'0px 0px -8% 0px'});
  els.forEach(function(e){io.observe(e)});
})();
// copy buttons: <button class="copy-btn" data-copy="..."> hoặc copy pre kế bên
(function(){
  document.querySelectorAll('.copy-btn').forEach(function(btn){
    btn.addEventListener('click',function(){
      var txt=btn.getAttribute('data-copy');
      if(!txt){var card=btn.closest('.code-card');var code=card&&card.querySelector('pre code');txt=code?code.innerText:'';}
      function flash(ok){btn.classList.toggle('done',ok);var l=btn.querySelector('.lbl');
        if(l){l.textContent=ok?'Đã chép':'Lỗi';setTimeout(function(){btn.classList.remove('done');l.textContent='Sao chép';},1800);}}
      if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(txt).then(function(){flash(true)},function(){flash(false)});}
      else flash(false);
    });
  });
})();
// quick-nav: highlight mục theo section đang xem
(function(){
  var qn=document.querySelectorAll('.quicknav a[href^="#"]');
  if(!qn.length||!('IntersectionObserver' in window))return;
  var map={};
  qn.forEach(function(a){var id=a.getAttribute('href').slice(1);var el=document.getElementById(id);if(el)map[id]=a;});
  var io=new IntersectionObserver(function(es){
    es.forEach(function(en){
      if(en.isIntersecting){
        qn.forEach(function(a){a.classList.remove('on')});
        var a=map[en.target.id];if(a)a.classList.add('on');
      }
    });
  },{rootMargin:'-40% 0px -55% 0px'});
  Object.keys(map).forEach(function(id){io.observe(document.getElementById(id))});
})();
// tech network background
(function(){
  var c=document.getElementById('netbg'); if(!c) return;
  var ctx=c.getContext('2d');
  var reduce=matchMedia('(prefers-reduced-motion: reduce)').matches;
  var darkQ=matchMedia('(prefers-color-scheme: dark)');
  var dpr=Math.min(window.devicePixelRatio||1,2), W=0,H=0,pts=[];
  var mouse={x:-9999,y:-9999};
  function col(a){return (darkQ.matches?'rgba(120,160,255,':'rgba(47,109,246,')+a+')';}
  function resize(){
    W=window.innerWidth;H=window.innerHeight;
    c.width=Math.floor(W*dpr);c.height=Math.floor(H*dpr);
    c.style.width=W+'px';c.style.height=H+'px';
    ctx.setTransform(dpr,0,0,dpr,0,0);
    var n=Math.min(70,Math.max(22,Math.floor(W*H/26000)));
    pts=Array.from({length:n},function(){return{x:Math.random()*W,y:Math.random()*H,
      vx:(Math.random()-0.5)*0.28,vy:(Math.random()-0.5)*0.28};});
    if(reduce)draw();
  }
  function draw(){
    ctx.clearRect(0,0,W,H);var i,j;
    if(!reduce){for(i=0;i<pts.length;i++){var p=pts[i];p.x+=p.vx;p.y+=p.vy;
      if(p.x<0||p.x>W)p.vx*=-1;if(p.y<0||p.y>H)p.vy*=-1;}}
    for(i=0;i<pts.length;i++){
      for(j=i+1;j<pts.length;j++){
        var a=pts[i],b=pts[j],dx=a.x-b.x,dy=a.y-b.y,d=Math.sqrt(dx*dx+dy*dy);
        if(d<150){ctx.strokeStyle=col((0.13*(1-d/150)).toFixed(3));ctx.lineWidth=1;
          ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);ctx.stroke();}
      }
      var mx=pts[i].x-mouse.x,my=pts[i].y-mouse.y,md=Math.sqrt(mx*mx+my*my);
      if(md<170){ctx.strokeStyle=col((0.18*(1-md/170)).toFixed(3));ctx.lineWidth=1;
        ctx.beginPath();ctx.moveTo(pts[i].x,pts[i].y);ctx.lineTo(mouse.x,mouse.y);ctx.stroke();}
    }
    for(i=0;i<pts.length;i++){ctx.fillStyle=col(0.5);ctx.beginPath();
      ctx.arc(pts[i].x,pts[i].y,1.5,0,6.2832);ctx.fill();}
    if(!reduce)requestAnimationFrame(draw);
  }
  window.addEventListener('resize',resize,{passive:true});
  window.addEventListener('mousemove',function(e){mouse.x=e.clientX;mouse.y=e.clientY;},{passive:true});
  window.addEventListener('mouseout',function(){mouse.x=-9999;mouse.y=-9999;});
  resize(); if(!reduce)draw();
})();

// ===== i18n language toggle =====
(function(){
  var KEY='powerbi-lang';
  // Migration: nguoi dung cu luu duoi key 'pbi-lang' (truoc v0.5.0) — doc lai 1 lan
  // roi ghi sang key moi, de ho khong bi reset ve mac dinh.
  try{ if(!localStorage.getItem(KEY)){ var _o=localStorage.getItem('pbi-lang');
    if(_o){ localStorage.setItem(KEY,_o); localStorage.removeItem('pbi-lang'); } } }catch(e){}
  function cur(){ return localStorage.getItem(KEY) || document.documentElement.getAttribute('data-lang') || 'vi'; }
  function apply(l){
    document.documentElement.setAttribute('data-lang', l);
    try{ localStorage.setItem(KEY, l); }catch(e){}
    document.querySelectorAll('.langsel').forEach(function(sel){
      var lbl=sel.querySelector('.langsel-cur'); if(lbl) lbl.textContent = (l==='en'?'EN':'VN');
      sel.querySelectorAll('li button').forEach(function(b){ b.classList.toggle('on', b.getAttribute('data-set')===l); });
    });
  }
  // dựng UI trong mọi header có .nav
  document.querySelectorAll('header.site .nav').forEach(function(nav){
    if(nav.querySelector('.langsel')) return;
    var sel=document.createElement('div'); sel.className='langsel';
    sel.innerHTML='<button aria-haspopup="listbox" aria-label="Language">'+
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a15 15 0 0 1 0 18M12 3a15 15 0 0 0 0 18"/></svg>'+
      '<span class="langsel-cur">VN</span>'+
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="m6 9 6 6 6-6"/></svg></button>'+
      '<ul role="listbox">'+
      '<li><button data-set="vi"><span class="fl">🇻🇳</span> Tiếng Việt</button></li>'+
      '<li><button data-set="en"><span class="fl">🇬🇧</span> English</button></li></ul>';
    // chèn sau cùng trong nav (sau nút GitHub)
    nav.appendChild(sel);
    var btn=sel.querySelector('button');
    btn.addEventListener('click',function(e){ e.stopPropagation(); sel.classList.toggle('open'); });
    sel.querySelectorAll('li button').forEach(function(b){
      b.addEventListener('click',function(){ apply(b.getAttribute('data-set')); sel.classList.remove('open'); });
    });
    document.addEventListener('click',function(){ sel.classList.remove('open'); });
  });
  apply(cur());
})();
