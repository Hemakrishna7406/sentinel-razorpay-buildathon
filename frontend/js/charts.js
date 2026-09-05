const C = {
  colors: { blue:'#5469d4', navy:'#0a0a12', green:'#10b981', amber:'#f59e0b', red:'#ef4444', gray:'#8b8d98', border:'rgba(255,255,255,0.08)', bg:'#14141f' },

  /* Premium dark tooltip config */
  tooltip: {
    backgroundColor:'rgba(10,10,18,0.95)',
    titleFont:{family:'Inter',size:11,weight:700},
    bodyFont:{family:'Inter',size:10,weight:500},
    padding:{x:14,y:10},
    cornerRadius:10,
    boxPadding:5,
    borderColor:'rgba(84,105,212,0.3)',
    borderWidth:1,
    displayColors:true,
    usePointStyle:true,
    caretSize:7
  },

  base: {
    responsive:true, maintainAspectRatio:false,
    animation:{ duration:800, easing:'easeOutQuart' },
    interaction:{ intersect:false, mode:'index' },
    plugins:{
      legend:{display:false},
      tooltip:{
        backgroundColor:'rgba(10,10,18,0.95)',
        titleFont:{family:'Inter',size:11,weight:700},
        bodyFont:{family:'Inter',size:10,weight:500},
        padding:{x:14,y:10},
        cornerRadius:10,
        boxPadding:5,
        borderColor:'rgba(84,105,212,0.3)',
        borderWidth:1,
        displayColors:true,
        usePointStyle:true
      }
    },
    scales:{
      x:{
        grid:{display:false},
        ticks:{font:{family:'Inter',size:10,weight:500},color:'#8b8d98',padding:6},
        border:{display:false}
      },
      y:{
        grid:{color:'rgba(255,255,255,0.04)',lineWidth:1},
        ticks:{font:{family:'Inter',size:10,weight:500},color:'#8b8d98',padding:10},
        border:{display:false}
      }
    }
  },

  destroy(c){ if(c) c.destroy() },

  /* Create canvas gradient for area fills */
  gradient(ctx, color, height=200){
    const g = ctx.createLinearGradient(0,0,0,height);
    g.addColorStop(0, color + '25');
    g.addColorStop(0.5, color + '08');
    g.addColorStop(1, color + '00');
    return g;
  },

  line(id, labels, datasets, opts={}){
    const el=document.getElementById(id); if(!el) return null;
    const ctx = el.getContext('2d');
    /* Apply gradient fills to datasets that opt-in */
    datasets.forEach(ds => {
      if(ds._gradient) {
        ds.backgroundColor = this.gradient(ctx, ds.borderColor, el.height || 200);
        ds.fill = true;
      }
    });
    return new Chart(el,{type:'line',data:{labels,datasets},options:{...this.base,...opts,plugins:{...this.base.plugins,...(opts.plugins||{})},scales:{...this.base.scales,...(opts.scales||{})}}});
  },

  bar(id, labels, datasets, opts={}){
    const ctx=document.getElementById(id); if(!ctx) return null;
    return new Chart(ctx,{type:'bar',data:{labels,datasets},options:{...this.base,...opts,plugins:{...this.base.plugins,...(opts.plugins||{})},scales:{...this.base.scales,...(opts.scales||{})}}});
  },

  doughnut(id, labels, data, colors, opts={}){
    const ctx=document.getElementById(id); if(!ctx) return null;
    return new Chart(ctx,{type:'doughnut',data:{labels,datasets:[{data,backgroundColor:colors,borderWidth:0,borderRadius:4,spacing:3,hoverOffset:6}]},options:{responsive:true,maintainAspectRatio:false,cutout:'72%',animation:{animateRotate:true,duration:800,easing:'easeOutQuart'},plugins:{legend:{display:false},tooltip:this.tooltip},...opts}});
  },

  gauge(id, val, max=100, color='#10b981'){
    const ctx=document.getElementById(id); if(!ctx) return null;
    return new Chart(ctx,{type:'doughnut',data:{datasets:[{data:[val,max-val],backgroundColor:[color,'rgba(255,255,255,0.08)'],borderWidth:0,borderRadius:8}]},options:{responsive:true,maintainAspectRatio:false,rotation:-90,circumference:180,cutout:'80%',animation:{animateRotate:true,duration:1000},plugins:{legend:{display:false},tooltip:{enabled:false}}}});
  },

  lineDS(label, data, color, extra={}){
    return {label,data,borderColor:color,backgroundColor:color+'15',borderWidth:2.5,pointRadius:0,pointHoverRadius:5,pointHoverBorderWidth:2.5,pointHoverBackgroundColor:'#14141f',pointHoverBorderColor:color,tension:.42,fill:false,shadow:true,...extra};
  },

  barDS(label, data, color, extra={}){
    return {label,data,backgroundColor:color,borderRadius:8,borderSkipped:false,maxBarThickness:32,hoverBackgroundColor:color+'EE',...extra};
  },

  areaDS(label, data, color, extra={}){
    return {label,data,borderColor:color,backgroundColor:color+'12',borderWidth:2.5,pointRadius:0,pointHoverRadius:5,tension:.42,fill:true,_gradient:true,...extra};
  }
};
