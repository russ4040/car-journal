import flet as ft
import json
import os
import sys
from datetime import datetime
from fpdf import FPDF

def get_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    for k in ("FLET_APP_STORAGE_DATA", "ANDROID_PRIVATE"):
        p = os.environ.get(k)
        if p and os.path.isdir(p):
            return p
    return os.path.dirname(os.path.abspath(__file__))

DATA_FILE = os.path.join(get_dir(), "car_data.json")

def get_export_dir():
    for path in ("/storage/emulated/0/Download", os.path.join(os.path.expanduser("~"), "Desktop"), os.path.join(os.path.expanduser("~"), "Downloads")):
        if os.path.isdir(path):
            return path
    return get_dir()

CATEGORIES = ("Типуль (ТО / масло)", "Тест (Ришуй)", "Резина (Цмигим)", "Аккумулятор (Мацбер)", "Тормоза", "Электрика / Свечи", "Ремонт / Запчасти")
PLACES = ("Официальный мусах", "Частный мусах", "Знакомый мастер", "Панчерия", "Магазин запчастей", "Сам")

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "car1": {"name": "Авто 1", "plate": "00-000-00", "km": "", "test": "", "t_date": "", "t_km": "", "year": "", "vin": "", "tires": "", "oil": "", "tow": "", "records": []},
        "car2": {"name": "Авто 2", "plate": "11-111-11", "km": "", "test": "", "t_date": "", "t_km": "", "year": "", "vin": "", "tires": "", "oil": "", "tow": "", "records": []},
        "masters": []
    }

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main(page: ft.Page):
    page.title = "Авто-журнал (Израиль)"
    page.theme_mode = ft.ThemeMode.DARK
    page.window.width = 960
    page.window.height = 880
    page.padding = 14
    page.scroll = ft.ScrollMode.AUTO

    data = load_data()
    state = {"tab": "car1", "passport": False, "cat": 0, "place": 0, "master": -1}
    status = ft.Text("", size=13, color=ft.Colors.GREEN_300, weight=ft.FontWeight.BOLD)
    tabs = ft.Row(alignment=ft.MainAxisAlignment.CENTER, wrap=True)
    content = ft.Column(spacing=10)

    def msg(text, err=False):
        status.value = text
        status.color = ft.Colors.RED_300 if err else ft.Colors.GREEN_300
        page.update()

    def export_json(e):
        p = os.path.join(get_export_dir(), "car_backup.json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        msg(f"Сохранено: {p}")

    def import_json(e):
        for folder in (get_export_dir(), os.path.join(os.path.expanduser("~"), "Downloads"), get_dir()):
            p = os.path.join(folder, "car_backup.json")
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8") as f:
                    data.clear()
                    data.update(json.load(f))
                save_data(data)
                render()
                msg(f"Загружено: {p}")
                return
        msg("Файл car_backup.json не найден.", True)

    def make_pdf(e):
        if state["tab"] not in ("car1", "car2"):
            msg("Выберите вкладку машины.", True)
            return
        car = data[state["tab"]]
        out = os.path.join(get_export_dir(), f"Service_{state['tab']}.pdf")
        pdf = FPDF()
        pdf.add_page()
        font = next((f for f in (r"C:\Windows\Fonts\arial.ttf", "/system/fonts/Roboto-Regular.ttf") if os.path.exists(f)), None)
        if font:
            pdf.add_font("F", "", font)
            pdf.set_font("F", size=14)
        else:
            pdf.set_font("Helvetica", size=14)
        pdf.cell(0, 10, f"Сервисная книжка: {car['name']} ({car['plate']})", new_x="LMARGIN", new_y="NEXT", align="C")
        if font:
            pdf.set_font("F", size=10)
        pdf.cell(0, 7, f"Год: {car['year']} | VIN: {car['vin']} | Резина: {car['tires']} | Пробег: {car['km']} км", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)
        for r in car["records"]:
            pdf.cell(0, 7, f"{r['date']} | {r['km']} км | {r['cat']}: {r['desc']} | {r['place']} | {r['amount']} NIS (Гар: {r['warr']})"[:95], border=1, new_x="LMARGIN", new_y="NEXT")
        pdf.output(out)
        msg(f"PDF сохранен: {out}")
        if sys.platform.startswith("win"):
            os.startfile(out)
    def render():
        tabs.controls = [
            ft.Button(content=f"🚗 {data['car1']['name'][:16]}", bgcolor=ft.Colors.BLUE_800 if state["tab"] == "car1" else None, on_click=lambda _: (state.update({"tab": "car1"}), render())),
            ft.Button(content=f"🚙 {data['car2']['name'][:16]}", bgcolor=ft.Colors.BLUE_800 if state["tab"] == "car2" else None, on_click=lambda _: (state.update({"tab": "car2"}), render())),
            ft.Button(content="🔧 Мастера", bgcolor=ft.Colors.TEAL_800 if state["tab"] == "masters" else None, on_click=lambda _: (state.update({"tab": "masters"}), render())),
        ]
        content.controls.clear()

        if state["tab"] in ("car1", "car2"):
            car = data[state["tab"]]
            p_btn = ft.OutlinedButton(content=ft.Text("Скрыть техпаспорт ▲" if state["passport"] else "Техпаспорт (VIN, резина, масло, грар) ▼", size=12), on_click=lambda _: (state.update({"passport": not state["passport"]}), render()))
            card = [
                ft.Row([
                    ft.TextField(label="Марка / модель", value=car["name"], width=220, dense=True, on_change=lambda e: (car.update({"name": e.control.value}), save_data(data))),
                    ft.TextField(label="Госномер", value=car["plate"], width=130, dense=True, on_change=lambda e: (car.update({"plate": e.control.value}), save_data(data))),
                    ft.TextField(label="Пробег (км)", value=car["km"], width=140, dense=True, on_change=lambda e: (car.update({"km": e.control.value}), save_data(data))),
                ], wrap=True),
                ft.Row([
                    ft.TextField(label="След. Тест", value=car["test"], width=160, dense=True, on_change=lambda e: (car.update({"test": e.control.value}), save_data(data))),
                    ft.TextField(label="След. Типуль (дата)", value=car["t_date"], width=170, dense=True, on_change=lambda e: (car.update({"t_date": e.control.value}), save_data(data))),
                    ft.TextField(label="След. Типуль (км)", value=car["t_km"], width=160, dense=True, on_change=lambda e: (car.update({"t_km": e.control.value}), save_data(data))),
                ], wrap=True),
                p_btn
            ]
            if state["passport"]:
                card.append(ft.Row([
                    ft.TextField(label="Год", value=car["year"], width=100, dense=True, on_change=lambda e: (car.update({"year": e.control.value}), save_data(data))),
                    ft.TextField(label="VIN (Шильда)", value=car["vin"], width=220, dense=True, on_change=lambda e: (car.update({"vin": e.control.value}), save_data(data))),
                    ft.TextField(label="Резина", value=car["tires"], width=160, dense=True, on_change=lambda e: (car.update({"tires": e.control.value}), save_data(data))),
                    ft.TextField(label="Масло / Аккум", value=car["oil"], width=220, dense=True, on_change=lambda e: (car.update({"oil": e.control.value}), save_data(data))),
                    ft.TextField(label="Эвакуатор (Грар)", value=car["tow"], width=180, dense=True, on_change=lambda e: (car.update({"tow": e.control.value}), save_data(data))),
                ], wrap=True))
            content.controls.append(ft.Container(content=ft.Column(card, spacing=8), bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH, padding=10, border_radius=10))

            n_date = ft.TextField(label="Дата", value=datetime.now().strftime("%d.%m.%Y"), width=115, dense=True)
            n_km = ft.TextField(label="Пробег", value=car["km"], width=115, dense=True)
            cat_btn = ft.OutlinedButton(content=ft.Text(f"Категория: {CATEGORIES[state['cat']]}", size=12, color=ft.Colors.CYAN_300), on_click=lambda _: (state.update({"cat": (state["cat"] + 1) % len(CATEGORIES)}), render()))
            place_btn = ft.OutlinedButton(content=ft.Text(f"Место: {PLACES[state['place']]}", size=12, color=ft.Colors.ORANGE_300), on_click=lambda _: (state.update({"place": (state["place"] + 1) % len(PLACES)}), render()))
            n_desc = ft.TextField(label="Что делали / детали", width=320, dense=True)
            n_place = ft.TextField(label="Гараж / Мастер / Тел.", width=260, dense=True)
            def pick_m(e):
                if not data["masters"]:
                    msg("Сначала добавьте мастера во вкладке Мастера.", True)
                    return
                state["master"] = (state["master"] + 1) % len(data["masters"])
                m = data["masters"][state["master"]]
                n_place.value = f"{m['name']} ({m['phone']})"
                page.update()
            n_sum = ft.TextField(label="Сумма (₪)", width=110, dense=True)
            n_warr = ft.TextField(label="Гарантия", width=130, dense=True)

            def add_rec(e):
                if not (n_desc.value or "").strip():
                    msg("Напишите, что делали!", True)
                    return
                car["records"].insert(0, {"date": n_date.value, "km": n_km.value, "cat": CATEGORIES[state["cat"]], "desc": n_desc.value, "place": f"{PLACES[state['place']]}: {n_place.value}", "amount": n_sum.value, "warr": n_warr.value})
                if n_km.value:
                    car["km"] = n_km.value
                save_data(data)
                msg("Запись добавлена!")
                render()

            content.controls.append(ft.Container(content=ft.Column([
                ft.Text("Новая запись (нажимайте на Категорию/Место для переключения):", weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_300),
                ft.Row([n_date, n_km, cat_btn, n_desc], wrap=True),
                ft.Row([place_btn, n_place, ft.OutlinedButton(content=ft.Text("Из справочника", size=12), on_click=pick_m)], wrap=True),
                ft.Row([n_sum, n_warr, ft.Button(content="+ Записать", on_click=add_rec)], wrap=True),
            ], spacing=8), bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST, padding=10, border_radius=10))
            for idx, r in enumerate(car["records"]):
                content.controls.append(ft.Container(content=ft.Row([
                    ft.Column([
                        ft.Text(f"{r['date']} • {r['km']} км • {r['cat']}", size=12, color=ft.Colors.CYAN_300),
                        ft.Text(r["desc"], size=15, weight=ft.FontWeight.BOLD),
                        ft.Text(f"{r['place']} | Гарантия: {r['warr'] or '-'}", size=12, color=ft.Colors.GREY_300),
                    ], expand=True, spacing=2),
                    ft.Text(f"{r['amount'] or '0'} ₪", size=15, color=ft.Colors.AMBER_300, weight=ft.FontWeight.BOLD),
                    ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_color=ft.Colors.RED_400, on_click=lambda _, i=idx: (car["records"].pop(i), save_data(data), render())),
                ]), bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH, padding=8, border_radius=8))
        else:
            mn = ft.TextField(label="Имя мастера / Гараж", width=230, dense=True)
            ms = ft.TextField(label="Специализация", width=210, dense=True)
            mp = ft.TextField(label="Телефон и город", width=230, dense=True)
            def add_m(e):
                if (mn.value or "").strip():
                    data["masters"].append({"name": mn.value.strip(), "spec": (ms.value or "").strip(), "phone": (mp.value or "").strip()})
                    save_data(data)
                    msg("Мастер добавлен!")
                    render()
            content.controls.append(ft.Container(content=ft.Row([mn, ms, mp, ft.Button(content="+ Добавить", on_click=add_m)], wrap=True), bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST, padding=10, border_radius=10))
            for idx, m in enumerate(data["masters"]):
                content.controls.append(ft.Container(content=ft.Row([
                    ft.Text(f"{m['name']} — {m['spec']} ({m['phone']})", expand=True, size=14),
                    ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_color=ft.Colors.RED_400, on_click=lambda _, i=idx: (data["masters"].pop(i), save_data(data), render())),
                ]), bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH, padding=8, border_radius=8))

        page.update()

    tools = ft.Row([
        ft.OutlinedButton(content=ft.Text("Сервисная книжка PDF", size=12, color=ft.Colors.RED_300), on_click=make_pdf),
        ft.OutlinedButton(content=ft.Text("Сохранить в файл", size=12), on_click=export_json),
        ft.OutlinedButton(content=ft.Text("Загрузить из файла", size=12), on_click=import_json),
    ], alignment=ft.MainAxisAlignment.CENTER, wrap=True)

    page.add(tabs, tools, status, content)
    render()

ft.run(main)
