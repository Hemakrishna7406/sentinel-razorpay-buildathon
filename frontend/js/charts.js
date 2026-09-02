const C = {
  colors: { blue:'#2563EB', navy:'#0A0F1F', green:'#10B981', amber:'#F59E0B', red:'#EF4444', gray:'#94A3B8', border:'#E2E8F0', bg:'#F7F8FB' },

  /* Premium tooltip config */
  tooltip: {
    backgroundColor:'rgba(10,15,31,0.92)',
    titleFont:{family:'Inter',size:11,weight:700},
    bodyFont:{family:'Inter',size:10,weight:500},
    padding:{x:12,y:8},
    cornerRadius:8,
    boxPadding:4,
    borderColor:'rgba(255,255,255,0.06)',
    borderWidth:1,
    displayColors:true,
    usePointStyle:true,
    caretSize:6
  },

  base: {
    responsive:true, maintainAspectRatio:false,
    animation:{ duration:700, easing:'easeOutQuart' },
    interaction:{ intersect:false, mode:'index' },
    plugins:{
      legend:{display:false},
      tooltip:{
        backgroundColor:'rgba(10,15,31,0.92)',
        titleFont:{family:'Inter',size:11,weight:700},
        bodyFont:{family:'Inter',size:10,weight:500},
        padding:{x:12,y:8},
        cornerRadius:8,
        boxPadding:4,
        borderColor:'rgba(255,255,255,0.06)',
        borderWidth:1,
        displayColors:true,
        usePointStyle:true
      }
    },
    scales:{
      x:{
        grid:{display:false},
        ticks:{font:{family:'Inter',size:10,weight:500},color:'#94A3B8',padding:4},
        border:{display:false}
      },
      y:{
        grid:{color:'rgba(0,0,0,.03)',lineWidth:1},
        ticks:{font:{family:'Inter',size:10,weight:500},color:'#94A3B8',padding:8},
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

  gauge(id, val, max=100, color='#10B981'){
    const ctx=document.getElementById(id); if(!ctx) return null;
    return new Chart(ctx,{type:'doughnut',data:{datasets:[{data:[val,max-val],backgroundColor:[color,'#E2E8F0'],borderWidth:0,borderRadius:6}]},options:{responsive:true,maintainAspectRatio:false,rotation:-90,circumference:180,cutout:'80%',animation:{animateRotate:true,duration:900},plugins:{legend:{display:false},tooltip:{enabled:false}}}});
  },

  lineDS(label, data, color, extra={}){
    return {label,data,borderColor:color,backgroundColor:color+'12',borderWidth:2,pointRadius:0,pointHoverRadius:4,pointHoverBorderWidth:2,pointHoverBackgroundColor:'#fff',pointHoverBorderColor:color,tension:.4,fill:false,...extra};
  },

  barDS(label, data, color, extra={}){
    return {label,data,backgroundColor:color,borderRadius:6,borderSkipped:false,maxBarThickness:28,hoverBackgroundColor:color+'DD',...extra};
  },

  areaDS(label, data, color, extra={}){
    return {label,data,borderColor:color,backgroundColor:color+'10',borderWidth:2,pointRadius:0,pointHoverRadius:4,tension:.4,fill:true,_gradient:true,...extra};
  }
};
