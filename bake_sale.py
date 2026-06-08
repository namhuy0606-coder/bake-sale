import streamlit as st
import base64
from pathlib import Path

st.set_page_config(page_title="Bake Sale Order", layout="wide")

IMAGE_DIR = Path(__file__).parent / "images"
IMAGE_DIR.mkdir(exist_ok=True)

DEFAULT_MENU = [
    {"name": "Garlic Chili Rice Cracker Ice Cream", "price": 60000, "note": "hop",           "image": "", "set_size": 0, "set_price": 0},
    {"name": "Ice Cream Mint Tea",                  "price": 0,     "note": "",               "image": "", "set_size": 0, "set_price": 0},
    {"name": "Mint Brookies",                       "price": 0,     "note": "",               "image": "", "set_size": 0, "set_price": 0},
    {"name": "Lychee",                              "price": 60000, "note": "",               "image": "", "set_size": 0, "set_price": 0},
    {"name": "Macaron Dau / Chanh",                 "price": 50000, "note": "4 mieng=180k",  "image": "", "set_size": 4, "set_price": 180000},
    {"name": "Dango",                               "price": 30000, "note": "xien",           "image": "", "set_size": 0, "set_price": 0},
    {"name": "Maleteet",                            "price": 25000, "note": "mieng",          "image": "", "set_size": 0, "set_price": 0},
    {"name": "Sholeh Zard",                         "price": 50000, "note": "",               "image": "", "set_size": 0, "set_price": 0},
    {"name": "Butter Tteok",                        "price": 65000, "note": "hop 5 cai",     "image": "", "set_size": 0, "set_price": 0},
    {"name": "Brookies",                            "price": 40000, "note": "",               "image": "", "set_size": 0, "set_price": 0},
    {"name": "Egg Tart - Vanilla",                  "price": 17000, "note": "cai / 45k x3",  "image": "", "set_size": 3, "set_price": 45000},
    {"name": "Egg Tart - Matcha",                   "price": 17000, "note": "cai / 45k x3",  "image": "", "set_size": 3, "set_price": 45000},
    {"name": "Egg Tart - Socola",                   "price": 17000, "note": "cai / 45k x3",  "image": "", "set_size": 3, "set_price": 45000},
    {"name": "Double Chocolate Muffin",             "price": 40000, "note": "",               "image": "", "set_size": 0, "set_price": 0},
    {"name": "Banana Chocochip Muffin",             "price": 40000, "note": "",               "image": "", "set_size": 0, "set_price": 0},
    {"name": "Tofu Pudding",                        "price": 60000, "note": "",               "image": "", "set_size": 0, "set_price": 0},
    {"name": "Carrot Cake",                         "price": 75000, "note": "",               "image": "", "set_size": 0, "set_price": 0},
    {"name": "Tiramisu Banana",                     "price": 80000, "note": "",               "image": "", "set_size": 0, "set_price": 0},
    {"name": "Tiramisu Matcha",                     "price": 90000, "note": "",               "image": "", "set_size": 0, "set_price": 0},
    {"name": "Mini Basque Burnt Cheesecake",        "price": 30000, "note": "",               "image": "", "set_size": 0, "set_price": 0},
    {"name": "Apple Pie",                           "price": 90000, "note": "",               "image": "", "set_size": 0, "set_price": 0},
    {"name": "Kheer",                               "price": 50000, "note": "",               "image": "", "set_size": 0, "set_price": 0},
    {"name": "Lazy Cake",                           "price": 25000, "note": "",               "image": "", "set_size": 0, "set_price": 0},
    {"name": "Qatayef",                             "price": 15000, "note": "",               "image": "", "set_size": 0, "set_price": 0},
    {"name": "Kek Batik",                           "price": 27000, "note": "",               "image": "", "set_size": 0, "set_price": 0},
    {"name": "Strawberry Brownie",                  "price": 40000, "note": "",               "image": "", "set_size": 0, "set_price": 0},
]

# ── Helpers ────────────────────────────────────────────────────────────────────
def calc_price(unit_price, set_size, set_price, qty):
    if set_size and set_price and qty >= set_size:
        sets = qty // set_size
        rem  = qty  % set_size
        return min(sets * set_price + rem * unit_price, qty * unit_price)
    return qty * unit_price

def price_breakdown(unit_price, set_size, set_price, qty):
    if not (set_size and set_price and qty >= set_size):
        return f"{qty} x {unit_price:,}d = {qty * unit_price:,}d"
    sets = qty // set_size
    rem  = qty  % set_size
    total = sets * set_price + rem * unit_price
    parts = [f"{sets} set x {set_price:,}d"]
    if rem:
        parts.append(f"{rem} x {unit_price:,}d")
    return " + ".join(parts) + f" = {total:,}d"

def image_tag(filename, height=120):
    if not filename:
        return ""
    p = IMAGE_DIR / filename
    if not p.exists():
        return ""
    ext  = p.suffix.lower().lstrip(".")
    mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "gif": "gif", "webp": "webp"}.get(ext, "jpeg")
    b64  = base64.b64encode(p.read_bytes()).decode()
    return (f'<img src="data:image/{mime};base64,{b64}" '
            f'style="width:100%;height:{height}px;object-fit:cover;border-radius:6px;margin-bottom:6px;">')

# ── Session state ──────────────────────────────────────────────────────────────
if "menu"          not in st.session_state: st.session_state.menu          = [dict(i) for i in DEFAULT_MENU]
if "quantities"    not in st.session_state: st.session_state.quantities    = {}
if "edit_mode"     not in st.session_state: st.session_state.edit_mode     = False
if "customer_name" not in st.session_state: st.session_state.customer_name = ""
if "order_ver"     not in st.session_state: st.session_state.order_ver     = 0
if "last_order"    not in st.session_state: st.session_state.last_order    = None

menu = st.session_state.menu

def get_qty(i):
    return st.session_state.quantities.get(i, 0)

def reset_order():
    st.session_state.quantities    = {}
    st.session_state.customer_name = ""
    st.session_state.last_order    = None
    st.session_state.order_ver    += 1

# ── Sidebar: running total ─────────────────────────────────────────────────────
with st.sidebar:
    st.header("Running Total")
    running = 0
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
    # (no revenue history shown)

# ── Header ─────────────────────────────────────────────────────────────────────
st.title("Bake Sale Order")
st.caption("Select items below, then press Confirm Order.")

col_new, col_edit = st.columns(2)
with col_new:
    if st.button("New Order", use_container_width=True):
        reset_order()
        st.rerun()
with col_edit:
    if st.button("Done Editing" if st.session_state.edit_mode else "Edit Menu", use_container_width=True):
        st.session_state.edit_mode = not st.session_state.edit_mode
        st.rerun()

st.divider()

# ── Edit mode ──────────────────────────────────────────────────────────────────
if st.session_state.edit_mode:
    st.subheader("Edit Menu Items")
    st.caption("Columns: Name  |  Unit price  |  Set size  |  Set price  |  Note  |  Image")

    IMAGE_EXTS   = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
    folder_imgs  = sorted(f.name for f in IMAGE_DIR.iterdir() if f.is_file() and f.suffix.lower() in IMAGE_EXTS)
    img_options  = ["(none)"] + folder_imgs

    if folder_imgs:
        st.caption(f"Images folder: {', '.join(folder_imgs)}")
    else:
        st.caption("No images found. Put image files in the `images/` folder next to `bake_sale.py`.")

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
                current = item["image"] if item["image"] in folder_imgs else "(none)"
                chosen  = st.selectbox("Image", options=img_options, index=img_options.index(current), key=f"img_{i}")
                menu[i]["image"] = "" if chosen == "(none)" else chosen
            with ic2:
                if menu[i]["image"] and (IMAGE_DIR / menu[i]["image"]).exists():
                    st.image(str(IMAGE_DIR / menu[i]["image"]), width=100)

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
            st.session_state.menu.append({"name": new_name.strip(), "price": new_price,
                "set_size": new_set_size, "set_price": new_set_price,
                "note": new_note.strip(), "image": ""})
            st.rerun()
        else:
            st.warning("Please enter a name.")
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

st.session_state.customer_name = st.text_input(
    "Customer name (optional)",
    value=st.session_state.customer_name,
    placeholder="e.g. Nguyen Van A",
    key=f"cname_{ver}",
)

if st.button("Confirm Order", type="primary", use_container_width=True):
    from datetime import datetime
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
        st.session_state.last_order = {
            "customer": st.session_state.customer_name.strip() or "Customer",
            "time":     datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "items":    ordered,
            "total":    order_total,
        }
        st.rerun()

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