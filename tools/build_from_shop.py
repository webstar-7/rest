"""Build nyansatek.rest (the restaurant edition) from the nyansatek.shop source.

nyansatek.rest is not written by hand: it is Shop's index.html with a fixed list of changes applied
(colour, wording, eat in / takeaway / tables, the kitchen screen, made-to-order dishes).
To bring a Shop update across, clone webstar-7/nyansatek-pos next to this repository and run:

    python3 tools/build_from_shop.py

Reads  ../nyansatek-pos   (Shop, untouched; override with SHOP_DIR)
Writes this repository    (index.html, sw.js, manifest.json, menu/index.html)
Every replacement is asserted, so a change in Shop that this script no longer matches fails loudly
instead of producing a half-converted page.
"""
import re, json, shutil, os

P = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(P)
SRC = os.environ.get('SHOP_DIR', os.path.join(os.path.dirname(OUT), 'nyansatek-pos'))

s = open(f'{SRC}/index.html', encoding='utf-8').read()


def sub(old, new, count=1):
    global s
    n = s.count(old)
    assert n == count, (old[:90], n, 'expected', count)
    s = s.replace(old, new)


def sub_any(old, new, at_least=1):
    global s
    n = s.count(old)
    assert n >= at_least, (old[:90], n)
    s = s.replace(old, new)
    return n


def region(start, end, fn):
    """Apply fn to the text between two markers (start inclusive, end exclusive)."""
    global s
    a = s.index(start)
    b = s.index(end, a + len(start))
    s = s[:a] + fn(s[a:b]) + s[b:]


# ------------------------------------------------------------------ colours
# Shop is navy. The restaurant edition is burgundy, with the same gold accent.
for old, new in [
    ('#17264a', '#6b1e2e'), ('#152238', '#4a1220'), ('#0d1630', '#2a0a12'),
    ('linear-gradient(180deg,#1b2d58 0%,#111b37 100%)', 'linear-gradient(180deg,#7a2233 0%,#4a1220 100%)'),
    ('rgba(23,38,74,', 'rgba(107,30,46,'), ('rgba(14,22,38,', 'rgba(30,10,14,'), ('rgba(10,18,32,', 'rgba(26,8,12,'),
    ('#e9f0fc', '#fbf3f1'), ('#b9c9e8', '#e3c9c4'), ('#f8faff', '#fdf7f5'), ('#e9edf7', '#f7ece6'),
]:
    sub_any(old, new)

# ------------------------------------------------------------------ name
sub_any('NYANSATEK Elite POS', 'NYANSATEK Restaurant')
sub_any('NYANSATEK POS', 'NYANSATEK Restaurant')
sub_any('Elite POS', 'Restaurant')
sub_any('<h2>Current Inventory</h2>', '<h2>Current menu</h2>')
sub('<p class="tag">Point of sale, inventory and ledger management built for Ghanaian shops.</p>',
    '<p class="tag">Orders, kitchen, menu and sales for restaurants and eateries in Ghana.</p>')
sub('<li><i></i>Works from a phone, tablet, or the shop computer</li>', '<li><i></i>Works from a phone, tablet, or the counter computer</li>')
sub_any("'assets/pos-reel'", "'assets/rest-reel'")
sub_any('assets/pos-reel', 'assets/rest-reel')
sub("const OFFLINE_SESSION_KEY='nyansatek_pos_cached_session';", "const OFFLINE_SESSION_KEY='nyansatek_rest_cached_session';")

# ------------------------------------------------------------------ this app is for restaurants only
# Shop sends restaurant accounts to nyansatek.rest; here the same check runs the other way round.
sub("""    // Restaurants and eateries have their own app. Their accounts live in the same
    // database (organizations.vertical = 'food') but belong on nyansatek.rest.
    if(org&&org.vertical==='food'){""",
    """    // This is the restaurant app. A shop account lives in the same database
    // (organizations.vertical = 'shop') but belongs on nyansatek.shop.
    if(org&&org.vertical&&org.vertical!=='food'){""")
sub("""eb.innerHTML='This account belongs to a restaurant. Please sign in at <a href="https://nyansatek.rest">nyansatek.rest</a>.';""",
    """eb.innerHTML='This account belongs to a shop. Please sign in at <a href="https://nyansatek.shop">nyansatek.shop</a>.';""")

# ------------------------------------------------------------------ navigation: Till, Kitchen, Menu
sub("?[['ov','Overview'],['cv','Cashier'],['av','Admin Inventory'],['chv','Cashiers'],['lv','SME Ledger'],['bv','Billing'],['stv','Settings'],['hv','How to use']]\n    :[['cv','Cashier'],['hv','How to use']];",
    "?[['ov','Overview'],['cv','Till'],['kv','Kitchen'],['av','Menu'],['chv','Cashiers'],['lv','SME Ledger'],['bv','Billing'],['stv','Settings'],['hv','How to use']]\n    :[['cv','Till'],['kv','Kitchen'],['hv','How to use']];")
sub("  hv:'<circle cx=\"12\" cy=\"12\" r=\"10\"/>",
    "  kv:'<path d=\"M6 13.9A4 4 0 0 1 7.4 6.1a5 5 0 0 1 9.2 0A4 4 0 0 1 18 13.9V20a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1ZM6 17h12\"/>',\n  hv:'<circle cx=\"12\" cy=\"12\" r=\"10\"/>")
sub("  if(v==='olv')renderOnlineOrders();\n}", "  if(v==='olv')renderOnlineOrders();\n  if(v==='kv')loadKitchen();\n}")
sub('    <div id="olv" class="view" style="padding:16px;overflow-y:auto;height:100%;"></div>\n',
    '    <div id="olv" class="view" style="padding:16px;overflow-y:auto;height:100%;"></div>\n\n    <!-- KITCHEN -->\n    <div id="kv" class="view" style="padding:16px;overflow-y:auto;height:100%;"></div>\n')

# ------------------------------------------------------------------ till: the whole menu by section, order type, table, note
sub('<input type="text" id="psch" placeholder="&#128269; Search products...">', '<input type="text" id="psch" placeholder="&#128269; Search the menu...">')
sub("""  if(!search){
    grid.innerHTML='<div class="pgm">Type a product name above to search.</div>';
    return;
  }
  const shown=inv.filter(p=>p.name.toLowerCase().includes(search));
  if(!shown.length){grid.innerHTML='<div class="pgm">No products found.</div>';return;}
  grid.innerHTML='';
  shown.forEach(it=>{
""", """  // A restaurant sells from a menu, so the whole menu is always on screen, grouped by section.
  const shown=(search?inv.filter(p=>p.name.toLowerCase().includes(search)||(p.category||'').toLowerCase().includes(search)):inv.slice())
    .sort((a,b)=>(a.category||'~').localeCompare(b.category||'~')||a.name.localeCompare(b.name));
  if(!shown.length){grid.innerHTML='<div class="pgm">'+(inv.length?'No dishes found.':'Your menu is empty. Add dishes under Menu.')+'</div>';return;}
  grid.innerHTML='';
  let lastSec=null;
  shown.forEach(it=>{
    const secName=it.category||'Other';
    if(secName!==lastSec){lastSec=secName;const h=document.createElement('div');h.className='pg-sec';h.textContent=secName;grid.appendChild(h);}
""")
sub("${it.stock<=0?'Out of stock':it.stock+' in stock'}</div>`;\n    if(it.stock>0)card.onclick=()=>addToCart(it.id);else card.title='Out of stock';",
    "${stockLabel(it)}</div>`;\n    if(it.stock>0)card.onclick=()=>addToCart(it.id);else card.title='Sold out';")
sub("document.getElementById('qm-stock').innerText=`In stock: ${p.stock}`+(ci?` • Already in cart: ${ci.qty}`:'');",
    "document.getElementById('qm-stock').innerText=(p.made_to_order?'Made to order':`In stock: ${p.stock}`)+(ci?` • Already in order: ${ci.qty}`:'');")
sub('const q=document.getElementById(\'qm-qty\');q.value=1;q.max=p.stock;', "const q=document.getElementById('qm-qty');q.value=1;q.max=p.made_to_order?999:p.stock;")
sub('Cart is empty<br><span style="font-size:.75rem;">Tap a product to add', 'No dishes yet<br><span style="font-size:.75rem;">Tap a dish to add it')
sub('<div class="ch">&#128722; Cart <span class="cbdg" id="cbdg">0</span>', '<div class="ch">&#128203; Order <span class="cbdg" id="cbdg">0</span>')
sub("""        <div class="ck">
          <div class="fg"><label>Payment Method</label>""", """        <div class="ck">
          <div class="ot">
            <div class="ot-seg" id="ot-seg">
              <button type="button" class="on" data-t="eat_in" onclick="setOrderType('eat_in')">Eat in</button>
              <button type="button" data-t="takeaway" onclick="setOrderType('takeaway')">Takeaway</button>
              <button type="button" data-t="delivery" onclick="setOrderType('delivery')">Delivery</button>
            </div>
            <div class="ot-row">
              <div class="fg" id="ot-table-wrap"><label>Table</label><input type="text" id="ot-table" maxlength="12" placeholder="e.g. 4"></div>
              <div class="fg" style="flex:2;"><label>Note for the kitchen</label><input type="text" id="ot-note" maxlength="140" placeholder="e.g. no pepper"></div>
            </div>
          </div>
          <div class="fg"><label>Payment Method</label>""")


def fin_sale(t):
    n = t.count("  const cartSnap=JSON.parse(JSON.stringify(cart));\n")
    assert n == 1, n
    t = t.replace("  const cartSnap=JSON.parse(JSON.stringify(cart));\n",
                  "  const cartSnap=JSON.parse(JSON.stringify(cart));\n  const order=orderFields(); // eat in / takeaway / delivery, table, note; starts the kitchen ticket at 'new'\n")
    assert t.count("items:cartSnap,smsMessage\n") == 1
    t = t.replace("items:cartSnap,smsMessage\n", "items:cartSnap,smsMessage,order\n")
    old = "      change_due:method==='Cash'?ten-tot:null\n    }).select().single();"
    assert t.count(old) == 1
    t = t.replace(old, "      change_due:method==='Cash'?ten-tot:null,\n      ...order\n    }).select().single();")
    old = "printIF(buildRcpt(invId,method,tot,ten,cartSnap,'RECEIPT','','','',cashierName));"
    assert t.count(old) == 2
    t = t.replace(old, "rcptOrder=order;printIF(buildRcpt(invId,method,tot,ten,cartSnap,'RECEIPT','','','',cashierName));rcptOrder=null;")
    old = "cart=[];document.getElementById('ten').value='';"
    assert t.count(old) == 2
    t = t.replace(old, old + "resetOrderFields();")
    assert "alert('Sale recorded. Invoice: '+invId);" in t
    t = t.replace("alert('Sale recorded. Invoice: '+invId);", "alert('Order sent to the kitchen. Invoice: '+invId);")
    return t


region('async function finSale(mode,phone){', '// Credit invoice from cashier cart', fin_sale)

# offline sales carry the order details too
sub("""      total:p.total,amount_tendered:p.amount_tendered,change_due:p.change_due,
      client_ref:rec.clientRef,created_offline:true
    }).select().single();""", """      total:p.total,amount_tendered:p.amount_tendered,change_due:p.change_due,
      client_ref:rec.clientRef,created_offline:true,
      ...(p.order||{})
    }).select().single();""")
# receipt shows the order type and table
sub("""  <div class="mr"><span>Payment Method:</span><span><b>${E(method)}</b></span></div>
""", """  <div class="mr"><span>Payment Method:</span><span><b>${E(method)}</b></span></div>
  ${rcptOrderRows()}
""")

# ------------------------------------------------------------------ menu items: section, made to order, sold out
sub('<h2>Inventory Management</h2>', '<h2>Menu</h2>', count=s.count('<h2>Inventory Management</h2>'))
sub("""              <div class="fg"><label>Product Name</label><input type="text" id="an" required></div>
""", """              <div class="fg"><label>Dish or item name</label><input type="text" id="an" required></div>
              <div class="fg"><label>Menu section</label><input type="text" id="acat" list="menu-sections" placeholder="e.g. Rice dishes, Soups, Drinks"><datalist id="menu-sections"></datalist></div>
""")
sub("""              <div class="fg"><label>Initial Stock</label><input type="number" id="astk" min="0" required></div>
              <div class="fg"><label>Note</label><input type="text" id="anote" placeholder="e.g. Opening stock"></div>
              <button type="submit" class="btn bf">Save Product</button>""",
    """              <label class="os-chk"><input type="checkbox" id="amto" checked onchange="syncMtoCreate()"> <span>Made to order (no stock to count)<br><span class="hint">Leave ticked for dishes you cook. Untick for bottled or packaged items you count.</span></span></label>
              <div id="astk-wrap" style="display:none;">
                <div class="fg"><label>Stock you have now</label><input type="number" id="astk" min="0"></div>
                <div class="fg"><label>Note</label><input type="text" id="anote" placeholder="e.g. Opening stock"></div>
              </div>
              <button type="submit" class="btn bf">Save item</button>""")
sub("""              <div class="fg"><label>Product Name</label><input type="text" id="ed-name"></div>
""", """              <div class="fg"><label>Dish or item name</label><input type="text" id="ed-name"></div>
              <div class="fg"><label>Menu section</label><input type="text" id="ed-cat" list="menu-sections" placeholder="e.g. Rice dishes, Soups, Drinks"></div>
""")
sub("""              <div class="fg"><label>Quantity</label><input type="number" id="ed-qty" min="0"></div>
""", """              <label class="os-chk"><input type="checkbox" id="ed-mto" onchange="syncMtoEdit()"> <span>Made to order (no stock to count)</span></label>
              <label class="os-chk" id="ed-avail-wrap" style="display:none;"><input type="checkbox" id="ed-avail"> <span>Available today (untick when it is sold out)</span></label>
              <div class="fg" id="ed-qty-wrap"><label>Quantity</label><input type="number" id="ed-qty" min="0"></div>
""")


def create_handler(t):
    old = "  const stk=parseInt(document.getElementById('astk').value)||0;\n"
    assert t.count(old) == 1
    t = t.replace(old, "  const mto=document.getElementById('amto').checked;\n  const cat=document.getElementById('acat').value.trim()||null;\n  const stk=mto?MTO_STOCK:(parseInt(document.getElementById('astk').value)||0);\n")
    old = "name:nm,price:sp,cost_price:cp,stock:stk"
    assert t.count(old) == 5, t.count(old)
    t = t.replace(old, old + ",category:cat,made_to_order:mto")
    old = "    await sb.from('inventory_log').insert({org_id:prof.org_id,product_id:prod.id,"
    assert t.count(old) == 1
    t = t.replace(old, "    if(!mto)await sb.from('inventory_log').insert({org_id:prof.org_id,product_id:prod.id,")
    assert t.count("alert('Product saved!');") == 1
    t = t.replace("alert('Product saved!');", "alert('Saved to your menu.');")
    return t


region("document.getElementById('apf').addEventListener('submit',async e=>{", "\n});", create_handler)
sub("        {org_id:p.org_id,barcode:p.barcode,name:p.name,price:p.price,cost_price:p.cost_price,stock:p.stock},\n        {onConflict:'org_id,barcode'}",
    "        {org_id:p.org_id,barcode:p.barcode,name:p.name,price:p.price,cost_price:p.cost_price,stock:p.stock,category:p.category||null,made_to_order:!!p.made_to_order},\n        {onConflict:'org_id,barcode'}")
sub("      if(!rec.logApplied){\n        await sb.from('inventory_log').insert({org_id:p.org_id,product_id:data.id,",
    "      if(!rec.logApplied&&!p.made_to_order){\n        await sb.from('inventory_log').insert({org_id:p.org_id,product_id:data.id,")

sub("      document.getElementById(pfx+'qty').value=p.stock;\n      if(ctx!=='m')fillProductExtras(p);",
    "      document.getElementById(pfx+'qty').value=p.stock;\n      if(ctx!=='m'){\n        document.getElementById('ed-cat').value=p.category||'';\n        document.getElementById('ed-mto').checked=!!p.made_to_order;\n        document.getElementById('ed-avail').checked=p.stock>0;\n        if(p.made_to_order)document.getElementById('ed-qty').value=0;\n        syncMtoEdit();\n        fillProductExtras(p);\n      }")
sub("    d.innerText=`${p.name} | ${GH(p.price)} | Stock: ${p.stock}`;\n    d.onclick=()=>{\n      editProdId=p.id;",
    "    d.innerText=`${p.name} | ${GH(p.price)} | ${p.made_to_order?stockLabel(p):'Stock: '+p.stock}`;\n    d.onclick=()=>{\n      editProdId=p.id;")
sub("  const fields={name,barcode:barcode||null,price,cost_price,stock};\n",
    "  const fields={name,barcode:barcode||null,price,cost_price,stock};\n  if(ctx!=='m'){\n    fields.category=document.getElementById('ed-cat').value.trim()||null;\n    fields.made_to_order=document.getElementById('ed-mto').checked;\n    if(fields.made_to_order)fields.stock=document.getElementById('ed-avail').checked?MTO_STOCK:0;\n  }\n")
sub("  if(!name){alert('Product name is required.');return;}\n  const fields=", "  if(!name){alert('A name is required.');return;}\n  const fields=")
sub("      <td style=\"text-align:center;\">${sbadge(it.stock)}</td>`;\n    tr.querySelectorAll('.ip')", "      <td style=\"text-align:center;\">${mtoBadge(it)}</td>`;\n    tr.querySelectorAll('.ip')")
sub("tb.innerHTML='<tr><td colspan=\"6\" style=\"text-align:center;color:var(--g);padding:20px;\">No products yet.</td></tr>';return;}\n  inv.forEach(it=>{\n    const profit=",
    "tb.innerHTML='<tr><td colspan=\"6\" style=\"text-align:center;color:var(--g);padding:20px;\">Your menu is empty.</td></tr>';return;}\n  inv.forEach(it=>{\n    const profit=")
sub("  renderPG();\n  renderInvTable(prof.role==='master'?'mit':'ait');\n  updateOfflineUI();\n}",
    "  renderPG();\n  renderInvTable(prof.role==='master'?'mit':'ait');\n  { // menu sections already in use, offered as suggestions when adding a dish\n    const dl=document.getElementById('menu-sections');\n    if(dl)dl.innerHTML=[...new Set(inv.map(p=>p.category).filter(Boolean))].sort().map(c=>`<option value=\"${E(c)}\">`).join('');\n  }\n  updateOfflineUI();\n}")

# ------------------------------------------------------------------ online: nyansatek.food and the restaurant's own menu page
sub("const{data:cats}=await sb.from('market_categories').select('id,name,parent_id,sort').eq('active',true).eq('vertical','shop').order('sort').order('name');",
    "const{data:cats}=await sb.from('market_categories').select('id,name,parent_id,sort').eq('active',true).eq('vertical','food').order('sort').order('name');")
sub("function storeUrl(){return onlineCfg?.store_slug?location.origin+'/shop/?s='+onlineCfg.store_slug:'';}",
    "function storeUrl(){return onlineCfg?.store_slug?location.origin+'/menu/?s='+onlineCfg.store_slug:'';}")
sub('<span class="hint">${E(location.origin)}/shop/?s=</span>', '<span class="hint">${E(location.origin)}/menu/?s=</span>')
sub_any('nyansatek.store', 'nyansatek.food')
for old, new in [
    ('Show in my online shop', 'Show on my online menu'), ('View my online shop', 'View my online menu'),
    ('Save online shop', 'Save online menu'), ('Online shop saved.', 'Online menu saved.'),
    ('Online Shop &amp; nyansatek.food', 'Online Menu &amp; nyansatek.food'),
    ("'nyansatek.food':'Online shop'", "'nyansatek.food':'Online menu'"),
    ('Orders from your online shop and nyansatek.food.', 'Orders from your online menu and nyansatek.food.'),
    ('<label>Marketplace category</label>', '<label>Food category on nyansatek.food</label>'),
    ('NYANSATEK will review your shop.', 'NYANSATEK will review your restaurant.'),
    ('Your shop is approved.', 'Your restaurant is approved.'),
    ('Sell online with your own shop page: your products with photos and prices,', 'Take orders online with your own menu page: your dishes with photos and prices,'),
]:
    sub(old, new)

for old, new in [
    ('Online Shop add-on', 'Online Menu add-on'), ('<h2>Online Shop</h2>', '<h2>Online Menu</h2>'),
    ('Your shop page', 'Your menu page'), ("'Shop with us online: '", "'Order from us online: '"),
    ('<label>Shop name online</label>', '<label>Restaurant name online</label>'),
    ('My shop page is open for orders', 'My menu page is open for orders'),
    ('Choose a web address for your shop.', 'Choose a web address for your menu page.'),
    ("'Copy your shop link:'", "'Copy your menu link:'"),
    ('is not switched on for your shop yet', 'is not switched on for your restaurant yet'),
    ('<label>Shop address (where', '<label>Restaurant address (where'), ('<label>Shop phone for riders</label>', '<label>Restaurant phone for riders</label>'),
    ('once your shop is', 'once your restaurant is'),
]:
    sub_any(old, new)


# ------------------------------------------------------------------ how to use
def guide(t):
    def r(old, new, count=1):
        nonlocal t
        assert t.count(old) == count, (old[:80], t.count(old), count)
        t = t.replace(old, new)

    r("      `Open <b>Cashier</b>. ${btn(\"swV('cv')\")}`,\n      'Find the product: type in <b>Search products</b> or scan its barcode into <b>Scan barcode</b>. Tap a product to add it to the cart.',\n      'Change quantities with <b>+</b> and <b>−</b> in the cart; tap the red <b>×</b> to remove an item, or <b>Clear</b> to start over.',",
      "      `Open <b>Till</b>. ${btn(\"swV('cv')\")}`,\n      'Tap each dish to add it to the order. The menu is shown by section; type in <b>Search the menu</b> to find a dish quickly, or scan the barcode of a bottled item.',\n      'Change quantities with <b>+</b> and <b>−</b> in the order; tap the red <b>×</b> to remove an item, or <b>Clear</b> to start over.',\n      'Choose <b>Eat in</b>, <b>Takeaway</b> or <b>Delivery</b>. For eat in, type the <b>Table</b>. Use <b>Note for the kitchen</b> for anything special, such as “no pepper”.',")
    r("'Finish with one of the buttons: <b>Complete</b>,", "'Finish with one of the buttons; the order then appears on the <b>Kitchen</b> screen: <b>Complete</b>,")
    r("<p class=\"hint\">Sign in once while online on each device first, so the product list is saved for offline use.</p>",
      "<p class=\"hint\">Sign in once while online on each device first, so the menu is saved for offline use. Orders taken offline reach the Kitchen screen once they upload.</p>")
    r("Selling with cash or MoMo, low-stock alerts, daily sales and profit, and a login for every cashier.",
      "Taking an order for a table, the kitchen screen, switching a dish to sold out, and orders from nyansatek.food.", 2)
    r("Everything you need to sell at the till. Tap a heading to open it.", "Everything you need to take orders at the till and work the kitchen screen. Tap a heading to open it.")
    kitchen = """sec('kitchen','The kitchen screen',`${ol([
        `Open <b>Kitchen</b> on the screen the kitchen can see. ${btn("swV('kv')")}`,
        'Every order completed at the till appears under <b>New</b> with its table or order type, the dishes and any note.',
        'Tap <b>Start cooking</b> to move it to <b>Preparing</b>, then <b>Mark ready</b> when it can go out.',
        'Tap <b>Served</b> once it has been handed over. The ticket then leaves the board.',
        'The board refreshes by itself every few seconds; <b>Refresh</b> updates it at once.',
        ...(role==='admin'?['Give the kitchen its own login under <b>Staff</b> by choosing <b>Kitchen</b>. That login opens straight onto this screen and can do nothing else.']:[])])}`)"""
    r("      ${sale(true)}\n", "      ${sale(true)}\n      ${" + kitchen + "}\n")
    r("  ${sale(false)}\n", "  ${sale(false)}\n  ${" + kitchen + "}\n")
    r("['Cashier',\"swV('cv')\",'The till. Ring up sales, print or text receipts, issue credit invoices and reprint recent receipts.'],",
      "['Till',\"swV('cv')\",'Take orders for eat in, takeaway or delivery, print or text receipts, issue credit invoices and reprint recent receipts.'],\n    ['Kitchen',\"swV('kv')\",'Open orders as tickets under New, Preparing and Ready. Tap a ticket’s button to move it on.'],")
    r("['Admin Inventory → Create',\"gdInv('cr')\",'Add a new product with its selling price, cost price, barcode and opening stock.'],",
      "['Menu → Create',\"gdInv('cr')\",'Add a dish or item with its menu section, selling price and cost price.'],")
    r("['Admin Inventory → Add Stock',\"gdInv('as')\",'Top up stock for a product you already sell.'],",
      "['Menu → Add Stock',\"gdInv('as')\",'Top up stock for a counted item, such as bottled drinks.'],")
    r("['Admin Inventory → Edit',\"gdInv('ed')\",'Change a product’s name, barcode, prices or quantity.'],",
      "['Menu → Edit',\"gdInv('ed')\",'Change a dish’s name, section, prices or photo, and switch it between available and sold out.'],")
    r("'Today at a glance: sales, number of transactions, products in stock, low-stock alerts and a 7-day sales chart.'",
      "'Today at a glance: sales, number of orders, items on the menu, low-stock alerts and a 7-day sales chart.'")
    r("Everything you need to set up your shop and run it day to day.", "Everything you need to set up your restaurant and run it day to day.")
    r("['products','Products & stock']", "['products','Menu & sold out']")
    r("['sale','Making a sale']", "['sale','Taking an order'],['kitchen','Kitchen']")
    r("sec('setup','Setting up your shop (do these in order)'", "sec('setup','Setting up your restaurant (do these in order)'")
    r("`Add your products: name, selling price, cost price, barcode if it has one, and the stock you have now. ${btn(\"gdInv('cr')\")}`,",
      "`Add your menu: each dish with its menu section, selling price and cost price. Leave <b>Made to order</b> ticked for dishes you cook; untick it for bottled or packaged items you count. ${btn(\"gdInv('cr')\")}`,")
    r("`Check the <b>Current Inventory</b> table on the right of Admin Inventory — fix any price by typing in it and pressing Enter. ${btn(\"swV('av')\")}`,",
      "`Check the table on the right of Menu — fix any price by typing in it and pressing Enter. ${btn(\"swV('av')\")}`,")
    r("`Make a test sale in <b>Cashier</b>, then void it under SME Ledger → Void / Return Sale. ${btn(\"swV('cv')\")}`,",
      "`Take a test order in <b>Till</b>, watch it arrive on <b>Kitchen</b>, then void it under SME Ledger → Void / Return Sale. ${btn(\"swV('cv')\")}`,")
    a = t.index("  ${sec('products','Adding products and managing stock',`")
    b = t.index("  ${sec('cashiers',", a)
    t = t[:a] + """  ${sec('products','Your menu: dishes, prices and sold out',`
    ${ol([
      `<b>New dish:</b> Menu → <b>+ Create</b>. Enter the name, the <b>Menu section</b> it belongs under (for example Rice dishes or Drinks), the selling price and the cost price, then <b>Save item</b>. ${btn("gdInv('cr')")}`,
      'Leave <b>Made to order</b> ticked for anything you cook. There is no stock to count; the dish is simply <b>Available</b> or <b>Sold out</b>.',
      `<b>Sold out for today:</b> in the table on the right of Menu, tap the green <b>Available</b> beside the dish. It turns to <b>Sold out</b> and can no longer be added to an order. Tap it again when it is back. ${btn("swV('av')")}`,
      `<b>Bottled or packaged items:</b> untick <b>Made to order</b> and enter the stock you have. Top it up later with <b>+ Add Stock</b>. ${btn("gdInv('as')")}`,
      `<b>Fix a mistake or add a photo:</b> <b>✎ Edit</b> → search → change the details → <b>Save Changes</b>. ${btn("gdInv('ed')")}`,
      'Counted items with 5 or fewer left show up under <b>Low Stock</b> on the Overview.'
    ])}`)}
""" + t[b:]
    r("only see the till.'", "only see the Till and the Kitchen screen.'")
    r("'During the day: sell from <b>Cashier</b>; record supplier deliveries and credit payments as they happen.',",
      "'During the day: take orders at <b>Till</b> and keep <b>Kitchen</b> open where the cooks can see it; switch a dish to <b>Sold out</b> as soon as it finishes.',")
    r("'Open: cashiers sign in on the till device.',", "'Open: cashiers sign in on the till device; switch back on any dish that was sold out yesterday.',")
    t = t.replace('Admin Inventory', 'Menu')
    return t


region('function renderGuide(', 'async function loadOverview(){', guide)

# ------------------------------------------------------------------ kitchen logins
# A 'kitchen' login sees only the Kitchen screen. The database enforces the same limits
# (nyansatek-pos: supabase/migrations/20261115040000_kitchen_logins.sql).
sub("    :[['cv','Till'],['kv','Kitchen'],['hv','How to use']];",
    "    :role==='kitchen'\n    ?[['kv','Kitchen'],['hv','How to use']]\n    :[['cv','Till'],['kv','Kitchen'],['hv','How to use']];")
sub("['chv','Cashiers'],['lv','SME Ledger']", "['chv','Staff'],['lv','SME Ledger']")
sub("  await loadInv(prof.org_id);await refSales();await loadBranding();\n  loadOnlineCfg();\n  swV(prof.role==='admin'?'ov':'cv');toggleTen();",
    "  // the kitchen login has no till: it skips the menu, today's sales and the online settings\n"
    "  if(prof.role==='kitchen'){document.getElementById('sb').style.display='none';await loadBranding();swV('kv');updateOfflineUI();return;}\n"
    "  await loadInv(prof.org_id);await refSales();await loadBranding();\n  loadOnlineCfg();\n  swV(prof.role==='admin'?'ov':'cv');toggleTen();")

# the Cashiers screen becomes Staff logins: a cashier or a kitchen login
sub('<h2>Manage Cashiers</h2>', '<h2>Staff logins</h2>')
sub("<p class=\"hint\">Create login credentials for your cashiers. They'll sign in with the Staff Username + password you set below (instead of the business name).</p>",
    "<p class=\"hint\">Create a login for each person at the till, and one for the screen in the kitchen. They sign in with the Staff Username and password you set below (instead of the business name).</p>")
sub('color:var(--p);">+ New Cashier</h3>\n            <form id="chf">\n              <div class="fg"><label>Cashier Full Name</label>',
    'color:var(--p);">+ New staff login</h3>\n            <form id="chf">\n'
    '              <div class="fg"><label>This login is for</label><select id="ch-role"><option value="cashier">Cashier: the till and the kitchen screen</option><option value="kitchen">Kitchen: the kitchen screen only</option></select></div>\n'
    '              <div class="fg"><label>Full name (or a name for the screen, e.g. Kitchen)</label>')
sub('<button type="submit" class="btn bf ba">Create Cashier</button>', '<button type="submit" class="btn bf ba">Create login</button>')
sub('color:var(--p);">Current Cashiers</h3>', 'color:var(--p);">Current logins</h3>')
sub('<table id="cht"><thead><tr><th>Name</th><th>Username</th><th>Status</th><th>Screening</th><th></th></tr></thead>',
    '<table id="cht"><thead><tr><th>Name</th><th>Username</th><th>For</th><th>Status</th><th>Screening</th><th></th></tr></thead>')
sub('No cashiers yet — create one on the left.', 'No staff logins yet — create one on the left.')


def staff_js(_old):
    return r"""async function loadCashiers(){
  const tb=document.querySelector('#cht tbody'),em=document.getElementById('ch-em');
  if(!tb)return;
  L(true);
  const{data,error}=await sb.from('profiles').select('id,full_name,login_username,is_active,created_at,role')
    .eq('org_id',prof.org_id).in('role',['cashier','kitchen']).order('full_name');
  await loadScreening();
  L(false);
  tb.innerHTML='';
  if(error){em.style.display='block';em.innerText='Could not load staff logins: '+error.message;return;}
  if(!data||!data.length){em.style.display='block';return;}
  em.style.display='none';
  data.forEach(c=>{
    const tr=document.createElement('tr');
    tr.innerHTML=`<td><strong>${E(c.full_name||'—')}</strong></td>
      <td style="font-family:monospace;">${E(c.login_username||'—')}</td>
      <td>${c.role==='kitchen'?'Kitchen':'Cashier'}</td>
      <td><span class="badge ${c.is_active?'bg':'br'}">${c.is_active?'Active':'Inactive'}</span></td>
      ${screenCell(c)}
      <td><button class="btn bsm bd del">Delete</button></td>`;
    tr.querySelector('.scr').onclick=()=>openScreening(c);
    tr.querySelector('.del').onclick=()=>deleteCashier(c.id,c.full_name,c.role);
    tb.appendChild(tr);
  });
}

document.getElementById('chf').addEventListener('submit',async e=>{
  e.preventDefault();
  const role=document.getElementById('ch-role').value;
  const name=document.getElementById('ch-name').value.trim();
  const username=document.getElementById('ch-user').value.trim().toLowerCase();
  const password=document.getElementById('ch-pass').value;
  if(!name||!username||password.length<8){alert('Fill in all fields — password must be at least 8 characters.');return;}
  L(true);
  const{data,error}=await sb.functions.invoke('create-cashier',{body:{
    full_name:name,login_username:username,password,org_id:prof.org_id,
    business_display_name:prof.display_name
  }});
  if(error||data?.error){L(false);alert('Error creating the login: '+(data?.error||error.message));return;}
  // Every login starts as a cashier; a kitchen login is then limited to the kitchen screen.
  let kitchenErr=null;
  if(role==='kitchen'){const r=await sb.rpc('set_staff_role',{p_staff:data.cashier_id,p_role:'kitchen'});kitchenErr=r.error;}
  L(false);
  document.getElementById('chf').reset();
  await loadCashiers();
  if(kitchenErr){alert(`The login "${username}" was created, but it could not be limited to the kitchen screen (${kitchenErr.message}). For now it is a cashier login: delete it and try again.`);return;}
  alert(role==='kitchen'
    ?`Kitchen login "${username}" created. Sign in with it on the screen in the kitchen: it opens straight onto the Kitchen board and shows nothing else.`
    :`Cashier "${name}" created. They can log in with Staff Username "${username}" and the password you set.`);
});

async function deleteCashier(id,name,role){
  if(!confirm(`Delete the login for "${name||''}"? It will no longer be able to sign in. Past sales stay on record with the name attached.`))return;
  L(true);
  // the delete function only removes cashier logins, so a kitchen login is switched back first
  if(role==='kitchen'){
    const r=await sb.rpc('set_staff_role',{p_staff:id,p_role:'cashier'});
    if(r.error){L(false);alert('Error deleting the login: '+r.error.message);return;}
  }
  const{data,error}=await sb.functions.invoke('delete-cashier',{body:{cashier_id:id,org_id:prof.org_id}});
  L(false);
  if(error||data?.error){alert('Error deleting the login: '+(data?.error||error.message));return;}
  await loadCashiers();
}

"""


region("async function loadCashiers(){", "function sbadge(s){", staff_js)

# the guide: a kitchen login reads only about signing in and the kitchen screen
sub("      ${sale(true)}\n      ${sec('kitchen','The kitchen screen',", "      ${role==='kitchen'?'':sale(true)}\n      ${sec('kitchen','The kitchen screen',")
sub("      ${sec('credit-c','Selling on credit',`${ol([", "      ${role==='kitchen'?'':sec('credit-c','Selling on credit',`${ol([")
sub("Your manager records the payment when they pay.'])}`)}\n      ${offline}\n", "Your manager records the payment when they pay.'])}`)}\n      ${role==='kitchen'?'':offline}\n")
sub("Everything you need to take orders at the till and work the kitchen screen. Tap a heading to open it.</p></div>",
    "${role==='kitchen'?'Everything you need to work the kitchen screen.':'Everything you need to take orders at the till and work the kitchen screen.'} Tap a heading to open it.</p></div>")
sub("['Cashiers',\"swV('chv')\",'Create and delete cashier logins.'],", "['Staff',\"swV('chv')\",'Create and delete logins for your cashiers and for the kitchen screen.'],")
sub("['cashiers','Cashiers'],", "['cashiers','Staff logins'],")
sub("${sec('cashiers','Giving cashiers their own logins',`", "${sec('cashiers','Giving cashiers and the kitchen their own logins',`")
sub("`Open <b>Cashiers</b> and fill in <b>+ New Cashier</b>: their full name, a staff username and a password of at least 8 characters. ${btn(\"swV('chv')\")}`,",
    "`Open <b>Staff</b> and fill in <b>+ New staff login</b>: choose <b>Cashier</b> or <b>Kitchen</b>, then a full name, a staff username and a password of at least 8 characters. ${btn(\"swV('chv')\")}`,")
sub("and only see the Till and the Kitchen screen.',", "and only see the Till and the Kitchen screen.',\n      'A <b>Kitchen</b> login is for the screen in the kitchen. It opens straight onto the Kitchen board and cannot take orders, see prices or change anything else.',")

# ------------------------------------------------------------------ styles + the restaurant layer
css = open(f'{P}/rest-layer.css', encoding='utf-8').read()
i = s.index('</style>')
s = s[:i] + css + s[i:]
layer = open(f'{P}/rest-layer.js', encoding='utf-8').read()
# goes at the end of the main script, so it can use everything defined there
marker = "\n</script>\n<script>"
main_end = [m.start() for m in re.finditer(re.escape(marker), s)]
assert len(main_end) >= 1
k = main_end[-2] if len(main_end) >= 2 else main_end[-1]
s = s[:k] + "\n" + layer + s[k:]
assert 'function loadKitchen' in s

open(f'{OUT}/index.html', 'w', encoding='utf-8').write(s)

# ------------------------------------------------------------------ manifest + service worker
m = json.load(open(f'{SRC}/manifest.json'))
m.update({'name': 'NYANSATEK Restaurant', 'short_name': 'Restaurant',
          'description': 'Orders, kitchen, menu and sales for restaurants and eateries.',
          'background_color': '#6b1e2e', 'theme_color': '#6b1e2e'})
m['icons'] = [
    {'src': 'icon-192.png', 'sizes': '192x192', 'type': 'image/png', 'purpose': 'any'},
    {'src': 'icon-512.png', 'sizes': '512x512', 'type': 'image/png', 'purpose': 'any'},
    {'src': 'icon-maskable-512.png', 'sizes': '512x512', 'type': 'image/png', 'purpose': 'maskable'}]
json.dump(m, open(f'{OUT}/manifest.json', 'w'), indent=2)
open(f'{OUT}/manifest.json', 'a').write('\n')

w = open(f'{SRC}/sw.js', encoding='utf-8').read()
w, n = re.subn(r"const CACHE_NAME = 'nyansatek-pos-v\d+';[^\n]*", "const CACHE_NAME = 'nyansatek-rest-v1';", w)
assert n == 1
open(f'{OUT}/sw.js', 'w', encoding='utf-8').write(w)
if not os.path.exists(f'{OUT}/CNAME'):
    open(f'{OUT}/CNAME', 'w').write('nyansatek.rest\n')
print('rest built:', len(s), 'bytes')

# ------------------------------------------------------------------ menu/: the restaurant's own online menu page
# (Shop's customer-facing page at /shop/, reworded. It talks to the same database functions.)
m = open(f'{SRC}/shop/index.html', encoding='utf-8').read()


def msub(old, new, at_least=1):
    global m
    assert m.count(old) >= at_least, (old[:80], m.count(old))
    m = m.replace(old, new)


for old, new in [
    ('#17264a', '#6b1e2e'), ('/shop/?', '/menu/?'), ('https://nyansatek.store', 'https://nyansatek.food'),
    ('Also on nyansatek.store', 'Also on nyansatek.food'),
    ('<title>Online shop · NYANSATEK</title>', '<title>Online menu · NYANSATEK</title>'),
    ("'<div class=\"empty\">Shop not found.</div>'", "'<div class=\"empty\">Menu not found.</div>'"),
    ('This shop is not open online right now.', 'This restaurant is not taking online orders right now.'),
    ("' · Shop online'", "' · Order online'"), ('Online shop by', 'Online menu by'),
    ('No products found.', 'No dishes found.'), ("the shop's", "the restaurant's"), ('the shop', 'the restaurant'),
    ("'Shop confirmed'", "'Restaurant confirmed'"), ("'Packed and ready'", "'Cooked and packed'"),
    ("'Returned to shop'", "'Returned to restaurant'"),
]:
    msub(old, new)
os.makedirs(f'{OUT}/menu', exist_ok=True)
open(f'{OUT}/menu/index.html', 'w', encoding='utf-8').write(m)
print('menu page built')
