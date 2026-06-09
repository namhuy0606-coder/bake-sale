import streamlit as st
import base64
from pathlib import Path
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Bake Sale Order", layout="wide")

IMAGE_DIR = Path(__file__).parent / "images"
IMAGE_DIR.mkdir(exist_ok=True)

SHEET_ID    = "1HZzW8sFN0AeBa2FhNEpqFyuX6p308Wsip4UFIGCapNA"
MENU_TAB    = "Menu"
ORDERS_TAB  = "Orders"
SCOPES      = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# ── Google Sheets connection ───────────────────────────────────────────────────
@st.cache_resource
def get_workbook():
    creds  = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=SCOPES)
    client = gspread.authorize(creds)
    return client.open_by_key(SHEET_ID)

def get_menu_sheet():
    wb = get_workbook()
    try:
        return wb.worksheet(MENU_TAB)
    except gspread.WorksheetNotFound:
        ws = wb.add_worksheet(title=MENU_TAB, rows=200, cols=6)
        ws.append_row(["name", "price", "set_size", "set_price", "note", "image"])
        return ws

def get_orders_sheet():
    wb = get_workbook()
    try:
        return wb.worksheet(ORDERS_TAB)
    except gspread.WorksheetNotFound:
        ws = wb.add_worksheet(title=ORDERS_TAB, rows=2000, cols=8)
        ws.append_row(["Order #", "Time", "Customer", "Item", "Qty", "Breakdown", "Subtotal (d)", "Order Total (d)"])
        return ws

def load_menu():
    try:
        ws      = get_menu_sheet()
        records = ws.get_all_records()
        menu = []
        for r in records:
            menu.append({
                "name":      str(r.get("name", "")),
                "price":     int(r.get("price", 0) or 0),
                "set_size":  int(r.get("set_size", 0) or 0),
                "set_price": int(r.get("set_price", 0) or 0),
                "note":      str(r.get("note", "")),
                "image":     str(r.get("image", "")),
            })
        return menu
    except Exception as e:
        st.error(f"Could not load menu from Google Sheets: {e}")
        return []

def save_menu(menu):
    try:
        ws = get_menu_sheet()
        ws.clear()
        ws.append_row(["name", "price", "set_size", "set_price", "note", "image"])
        if menu:
            ws.append_rows([
                [item["name"], item["price"], item["set_size"], item["set_price"], item["note"], item["image"]]
                for item in menu
            ])
        return True
    except Exception as e:
        st.error(f"Could not save menu: {e}")
        return False

def save_order(order, order_num):
    try:
        ws = get_orders_sheet()
        for row in order["items"]:
            ws.append_row([
                order_num,
                order["time"],
                order["customer"],
                row["name"],
                row["qty"],
                row["breakdown"],
                row["subtotal"],
                order["total"],
            ])
        return True
    except Exception as e:
        return str(e)

# ── Price helpers ──────────────────────────────────────────────────────────────
def calc_price(unit_price, set_size, set_price, qty):
    if set_size and set_price and qty >= set_size:
        sets = qty // set_size
        rem  = qty  % set_size
        return min(sets * set_price + rem * unit_price, qty * unit_price)
    return qty * unit_price

def price_breakdown(unit_price, set_size, set_price, qty):
    if not (set_size and set_price and qty >= set_size):
        return f"{qty} x {unit_price:,}d = {qty * unit_price:,}d"
    sets  = qty // set_size
    rem   = qty  % set_size
    total = sets * set_price + rem * unit_price
    parts = [f"{sets} set x {set_price:,}d"]
    if rem:
        parts.append(f"{rem} x {unit_price:,}d")
    return " + ".join(parts) + f" = {total:,}d"

def image_tag(url, height=120):
    if not url:
        return ""
    if str(url).startswith("http"):
        return f'<img src="{url}" style="width:100%;height:{height}px;object-fit:cover;border-radius:6px;margin-bottom:6px;">'
    return ""

# ── Session state ──────────────────────────────────────────────────────────────
if "menu"           not in st.session_state: st.session_state.menu           = load_menu()
if "quantities"     not in st.session_state: st.session_state.quantities     = {}
if "edit_mode"      not in st.session_state: st.session_state.edit_mode      = False
if "customer_name"  not in st.session_state: st.session_state.customer_name  = ""
if "order_ver"      not in st.session_state: st.session_state.order_ver      = 0
if "last_order"     not in st.session_state: st.session_state.last_order     = None
if "order_counter"  not in st.session_state: st.session_state.order_counter  = 1

menu = st.session_state.menu

def get_qty(i):
    return st.session_state.quantities.get(i, 0)

def reset_order():
    st.session_state.quantities   = {}
    st.session_state.customer_name = ""
    st.session_state.last_order   = None
    st.session_state.order_ver   += 1

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Running Total")
    running  = 0
    any_item = False
    for i in range(len(menu)):
        qty = get_qty(i)
        if qty > 0:
            any_item = True
            item  = menu[i]
            total = calc_price(item["price"], item["set_size"], item["set_price"], qty)
            running += total
            st.write(f"**{item['name']}** x{qty}  =  {total:,}d")
    if any_item:
        st.divider()
        st.metric("Total", f"{running:,}d")
    else:
        st.caption("No items selected yet.")

# ── Header ─────────────────────────────────────────────────────────────────────
st.title("Bake Sale Order")

col_new, col_edit, col_reload = st.columns(3)
with col_new:
    if st.button("New Order", use_container_width=True):
        reset_order()
        st.rerun()
with col_edit:
    if st.button("Done Editing" if st.session_state.edit_mode else "Edit Menu", use_container_width=True):
        st.session_state.edit_mode = not st.session_state.edit_mode
        st.rerun()
with col_reload:
    if st.button("Reload Menu", use_container_width=True):
        st.session_state.menu = load_menu()
        st.rerun()

st.divider()

# ── Edit mode ──────────────────────────────────────────────────────────────────
if st.session_state.edit_mode:
    st.subheader("Edit Menu Items")
    st.caption("Name  |  Unit price  |  Set size  |  Set price  |  Note  |  Image file")

    IMAGE_EXTS  = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
    folder_imgs = sorted(f.name for f in IMAGE_DIR.iterdir() if f.is_file() and f.suffix.lower() in IMAGE_EXTS)
    img_options = ["(none)"] + folder_imgs

    for i, item in enumerate(menu):
        with st.container(border=True):
            c1, c2, c3, c4, c5, c6 = st.columns([3, 2, 1, 2, 2, 1])
            with c1: menu[i]["name"]      = st.text_input("Name",       value=item["name"],       key=f"name_{i}",  label_visibility="collapsed")
            with c2: menu[i]["price"]     = st.number_input("Unit price",value=item["price"],     step=1000, key=f"price_{i}", label_visibility="collapsed")
            with c3: menu[i]["set_size"]  = st.number_input("Set size",  value=item["set_size"],  step=1, min_value=0, key=f"ss_{i}", label_visibility="collapsed")
            with c4: menu[i]["set_price"] = st.number_input("Set price", value=item["set_price"], step=1000, min_value=0, key=f"sp_{i}", label_visibility="collapsed")
            with c5: menu[i]["note"]      = st.text_input("Note",        value=item["note"],       key=f"note_{i}", label_visibility="collapsed")
            with c6:
                st.write("")
                if st.button("Del", key=f"del_{i}"):
                    del st.session_state.menu[i]
                    st.session_state.quantities.pop(i, None)
                    st.rerun()

            ic1, ic2 = st.columns([2, 1])
            with ic1:
                # Đổi thành ô nhập văn bản để dán/sửa link URL ảnh
                menu[i]["image"] = st.text_input("Image URL", value=item.get("image", ""), key=f"img_{i}", label_visibility="collapsed")
            with ic2:
                # Hiển thị ảnh xem trước nếu đó là link hợp lệ
                if str(menu[i]["image"]).startswith("http"):
                    st.image(menu[i]["image"], width=100)

    st.divider()
    st.subheader("Add New Item")
    na, nb, nc, nd, ne = st.columns([3, 2, 1, 2, 2])
    with na: new_name      = st.text_input("Name",        key="new_name")
    with nb: new_price     = st.number_input("Unit price", value=0, step=1000, key="new_price")
    with nc: new_set_size  = st.number_input("Set size",   value=0, step=1, min_value=0, key="new_ss")
    with nd: new_set_price = st.number_input("Set price",  value=0, step=1000, min_value=0, key="new_sp")
    with ne: new_note      = st.text_input("Note",         key="new_note")
    if st.button("Add item"):
        if new_name.strip():
            st.session_state.menu.append({
                "name": new_name.strip(), "price": new_price,
                "set_size": new_set_size, "set_price": new_set_price,
                "note": new_note.strip(), "image": ""
            })
            st.rerun()
        else:
            st.warning("Please enter a name.")

    st.divider()
    if st.button("Save Menu to Google Sheets", type="primary", use_container_width=True):
        with st.spinner("Saving to Google Sheets..."):
            if save_menu(st.session_state.menu):
                st.success("Menu saved! All users will see the updated menu on next Reload.")
    st.stop()

# ── Order grid ─────────────────────────────────────────────────────────────────
ver  = st.session_state.order_ver
COLS = 3
rows = [list(range(len(menu)))[i:i+COLS] for i in range(0, len(menu), COLS)]

for row_indices in rows:
    cols = st.columns(COLS)
    for col_pos, idx in enumerate(row_indices):
        item = menu[idx]
        with cols[col_pos]:
            with st.container(border=True):
                if item["image"]:
                    st.markdown(image_tag(item["image"]), unsafe_allow_html=True)
                st.markdown(f"**{item['name']}**")
                if item["price"] > 0:
                    cap = f"{item['price']:,}d"
                    if item["set_size"] and item["set_price"]:
                        cap += f"  ·  {item['set_size']} for {item['set_price']:,}d"
                    elif item["note"]:
                        cap += f"  ·  {item['note']}"
                    st.caption(cap)
                elif item["note"]:
                    st.caption(item["note"])
                else:
                    st.caption("Price: TBD")

                st.session_state.quantities[idx] = st.number_input(
                    "Quantity", min_value=0, value=0, step=1,
                    key=f"qty_{idx}_{ver}",
                    label_visibility="collapsed",
                )

st.divider()

if st.button("Confirm Order", type="primary", use_container_width=True):
    ordered = []
    order_total = 0
    for i in range(len(menu)):
        qty = get_qty(i)
        if qty > 0:
            item      = menu[i]
            subtotal  = calc_price(item["price"], item["set_size"], item["set_price"], qty)
            breakdown = price_breakdown(item["price"], item["set_size"], item["set_price"], qty)
            ordered.append({"name": item["name"], "price": item["price"], "qty": qty,
                            "subtotal": subtotal, "breakdown": breakdown})
            order_total += subtotal
    if not ordered:
        st.warning("No items selected.")
    else:
        order = {            
            "time":     datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "items":    ordered,
            "total":    order_total,
        }
        order_num = st.session_state.order_counter
        with st.spinner("Saving order to Google Sheets..."):
            result = save_order(order, order_num)
        if result is True:
            st.session_state.order_counter += 1
            st.session_state.last_order = order
            st.rerun()
        else:
            st.error(f"Could not save order: {result}")

if st.session_state.last_order:
    o = st.session_state.last_order
    st.success(f"### Order confirmed — {o['customer']}")
    st.caption(f"Time: {o['time']}")
    for row in o["items"]:
        if row["price"]:
            st.write(f"- **{row['name']}**  ·  {row['breakdown']}")
        else:
            st.write(f"- **{row['name']}** x{row['qty']}  =  (price TBD)")
    st.divider()
    st.markdown(f"## Total: **{o['total']:,}d**")