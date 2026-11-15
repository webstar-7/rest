
// ===================== RESTAURANT LAYER =====================
// What makes this the restaurant edition of the NYANSATEK till:
//  - every order is marked Eat in, Takeaway or Delivery, with a table for eat-in and a note for the kitchen
//  - a Kitchen screen lists open orders as tickets: New -> Preparing -> Ready -> Served
//  - a dish made to order has an Available / Sold out switch instead of a stock count
// The database stores these in sales.order_type / table_label / order_note / kitchen_status and
// products.made_to_order (see supabase/migrations/20261115020000_restaurants.sql in nyansatek-pos).

// A made-to-order dish has nothing to count, so "available" is stored as a large stock number and
// "sold out" as zero. Every existing rule (stock > 0 can be sold; each sale takes stock off) keeps working.
const MTO_STOCK=100000;

// ---- order type, table, note (till) ----
let orderType='eat_in';
const ORDER_TYPES={eat_in:'Eat in',takeaway:'Takeaway',delivery:'Delivery'};
function setOrderType(t){
  orderType=t;
  document.querySelectorAll('#ot-seg button').forEach(b=>b.classList.toggle('on',b.dataset.t===t));
  const tw=document.getElementById('ot-table-wrap');if(tw)tw.style.display=t==='eat_in'?'':'none';
}
function orderFields(){
  const table=(document.getElementById('ot-table')?.value||'').trim();
  const note=(document.getElementById('ot-note')?.value||'').trim();
  return{order_type:orderType,table_label:orderType==='eat_in'&&table?table:null,order_note:note||null,
    kitchen_status:'new',kitchen_updated_at:new Date().toISOString()};
}
function resetOrderFields(){
  const t=document.getElementById('ot-table'),n=document.getElementById('ot-note');
  if(t)t.value='';if(n)n.value='';
}
function orderLabel(o){
  if(!o||!o.order_type)return'';
  return ORDER_TYPES[o.order_type]+(o.order_type==='eat_in'&&o.table_label?' · Table '+o.table_label:'');
}
// The order being printed right now (set by finSale just before the receipt is built).
let rcptOrder=null;
function rcptOrderRows(){
  if(!rcptOrder||!rcptOrder.order_type)return'';
  return `<div class="mr"><span>Order:</span><span><b>${E(orderLabel(rcptOrder))}</b></span></div>`
    +(rcptOrder.order_note?`<div class="mr"><span>Note:</span><span>${E(rcptOrder.order_note)}</span></div>`:'');
}

// ---- made to order: Available / Sold out ----
function stockLabel(p){return p.made_to_order?(p.stock>0?'Available':'Sold out'):(p.stock<=0?'Sold out':p.stock+' left');}
function mtoBadge(it){
  if(!it.made_to_order)return sbadge(it.stock);
  const on=it.stock>0;
  return `<button type="button" class="badge ${on?'bg':'br'}" style="border:0;cursor:pointer;" title="Tap to switch" onclick="toggleSoldOut('${it.id}')">${on?'Available':'Sold out'}</button>`;
}
async function toggleSoldOut(id){
  const p=inv.find(i=>i.id===id);if(!p)return;
  const stock=p.stock>0?0:MTO_STOCK;
  if(!navigator.onLine){alert('Switching a dish on or off needs an internet connection.');return;}
  const{error}=await sb.from('products').update({stock}).eq('id',id);
  if(error){alert('Could not update: '+error.message);return;}
  p.stock=stock;renderPG();renderInvTable(prof.role==='master'?'mit':'ait');
}
function syncMtoCreate(){
  const on=document.getElementById('amto').checked,stk=document.getElementById('astk');
  document.getElementById('astk-wrap').style.display=on?'none':'';
  stk.required=!on;
}
function syncMtoEdit(){
  const on=document.getElementById('ed-mto').checked;
  document.getElementById('ed-qty-wrap').style.display=on?'none':'';
  document.getElementById('ed-avail-wrap').style.display=on?'':'none';
}

// ---- kitchen screen ----
let kitchenTimer=null,kitchenOrders=[];
const K_NEXT={new:['preparing','Start cooking'],preparing:['ready','Mark ready'],ready:['served','Served']};
const K_COLS=[['new','New'],['preparing','Preparing'],['ready','Ready']];
function ago(ts){const m=Math.max(0,Math.round((Date.now()-new Date(ts).getTime())/60000));return m<1?'just now':m<60?m+' min ago':Math.floor(m/60)+' h '+(m%60)+' min ago';}
async function loadKitchen(silent){
  const el=document.getElementById('kv');if(!el)return;
  if(!silent&&!kitchenOrders.length)el.innerHTML='<div class="es">Loading…</div>';
  try{
    const{data,error}=await sb.from('sales')
      .select('id,invoice_id,created_at,order_type,table_label,order_note,kitchen_status,cashier_name_snapshot,sale_items(name_snapshot,qty)')
      .eq('org_id',prof.org_id).in('kitchen_status',['new','preparing','ready']).order('created_at').limit(80);
    if(error)throw error;
    kitchenOrders=data||[];
    renderKitchen();
  }catch(e){
    if(!silent)el.innerHTML='<div class="card"><h2>Kitchen</h2><p class="hint">The kitchen screen needs an internet connection. Orders taken offline appear here once they sync.</p></div>';
  }
  clearInterval(kitchenTimer);
  // keep the board fresh while it is the screen being shown
  kitchenTimer=setInterval(()=>{if(document.getElementById('kv')?.classList.contains('on'))loadKitchen(true);else clearInterval(kitchenTimer);},12000);
}
function renderKitchen(){
  const el=document.getElementById('kv');if(!el)return;
  const col=([k,label])=>{
    const list=kitchenOrders.filter(o=>o.kitchen_status===k);
    return `<div class="k-col"><div class="k-h">${label}<span>${list.length}</span></div>${list.length?list.map(o=>`
      <div class="k-t k-${k}">
        <div class="k-top"><b>${E(orderLabel(o)||'Order')}</b><span>${ago(o.created_at)}</span></div>
        <div class="k-inv">${E(o.invoice_id||'')}${o.cashier_name_snapshot?' · '+E(o.cashier_name_snapshot):''}</div>
        <ul>${(o.sale_items||[]).map(i=>`<li><b>${i.qty}×</b> ${E(i.name_snapshot)}</li>`).join('')}</ul>
        ${o.order_note?`<div class="k-note">${E(o.order_note)}</div>`:''}
        <button class="btn bf" onclick="kitchenStep('${o.id}')">${K_NEXT[k][1]}</button>
      </div>`).join(''):'<div class="k-empty">Nothing here</div>'}</div>`;
  };
  el.innerHTML=`<div class="k-bar"><h2>Kitchen</h2><span class="hint">Orders from the till appear here on their own. Refreshes every few seconds.</span>
    <button class="btn bsm" onclick="loadKitchen()">Refresh</button></div>
    <div class="k-board">${K_COLS.map(col).join('')}</div>`;
}
async function kitchenStep(id){
  const o=kitchenOrders.find(x=>x.id===id);if(!o)return;
  const next=K_NEXT[o.kitchen_status][0];
  const{error}=await sb.from('sales').update({kitchen_status:next,kitchen_updated_at:new Date().toISOString()}).eq('id',id);
  if(error){alert('Could not update the order: '+error.message);return;}
  o.kitchen_status=next;
  if(next==='served')kitchenOrders=kitchenOrders.filter(x=>x.id!==id);
  renderKitchen();
}
// ===================== /RESTAURANT LAYER =====================
