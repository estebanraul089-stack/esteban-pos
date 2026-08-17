from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Carta inicial precargada
carta = [
    {"id": 1, "nombre": "Sopa verde", "precio": 8.00, "tipo": "normal"},
    {"id": 2, "nombre": "Chupe de olluco", "precio": 8.00, "tipo": "normal"},
    {"id": 3, "nombre": "Patasca", "precio": 13.00, "tipo": "normal"},
    {"id": 4, "nombre": "Segundo o platillo", "precio": 9.50, "tipo": "normal"},
    {"id": 5, "nombre": "Chaufa", "precio": 13.00, "tipo": "normal"},
    {"id": 6, "nombre": "Agua de hierba o mate", "precio": 2.00, "tipo": "normal"},
    {"id": 7, "nombre": "Café", "precio": 2.00, "tipo": "normal"},
    {"id": 8, "nombre": "Panqueque", "precio": 1.50, "tipo": "normal"},
    {"id": 9, "nombre": "Pan con huevo o queso", "precio": 2.50, "tipo": "normal"},
    {"id": 10, "nombre": "Extra / Especial", "precio": 0.00, "tipo": "extra"}
]

boleta_actual = []
total_pagar = 0.0
vuelto = None

# Variables para métricas del día
ganancias_dia = 0.0
ventas_contadas = 0

@app.route("/")
def inicio():
    return render_template(
        "index.html", 
        carta=carta, 
        boleta=boleta_actual, 
        total=total_pagar, 
        vuelto=vuelto,
        ganancias=ganancias_dia,
        ventas_num=ventas_contadas
    )

# Agregar producto estándar a la boleta
@app.route("/agregar/<int:item_id>", methods=["POST"])
def agregar(item_id):
    global total_pagar
    producto = next((p for p in carta if p["id"] == item_id), None)
    if producto and producto["tipo"] == "normal":
        boleta_actual.append({"nombre": producto["nombre"], "precio": producto["precio"]})
        total_pagar += producto["precio"]
    return redirect(url_for("inicio"))

# Agregar monto Extra / Especial directo
@app.route("/agregar_extra", methods=["POST"])
def agregar_extra():
    global total_pagar
    try:
        monto = float(request.form.get("monto_extra", 0))
        if monto > 0:
            boleta_actual.append({"nombre": "Extra / Especial", "precio": monto})
            total_pagar += monto
    except ValueError:
        pass
    return redirect(url_for("inicio"))

# Cobrar y registrar la venta en las ganancias del día
@app.route("/cobrar", methods=["POST"])
def cobrar():
    global vuelto, ganancias_dia, ventas_contadas
    try:
        pago = float(request.form.get("pago", 0))
        if pago >= total_pagar and total_pagar > 0:
            vuelto = round(pago - total_pagar, 2)
            
            # Si el cobro es válido, sumamos la venta al total del día
            ganancias_dia += total_pagar
            ventas_contadas += 1
        else:
            vuelto = "Monto insuficiente"
    except ValueError:
        vuelto = "Monto inválido"
    return redirect(url_for("inicio"))

# Siguiente Cliente
@app.route("/nueva_boleta", methods=["POST"])
def nueva_boleta():
    global boleta_actual, total_pagar, vuelto
    boleta_actual = []
    total_pagar = 0.0
    vuelto = None
    return redirect(url_for("inicio"))

# Reiniciar caja para un nuevo día
@app.route("/reiniciar_caja", methods=["POST"])
def reiniciar_caja():
    global ganancias_dia, ventas_contadas, boleta_actual, total_pagar, vuelto
    ganancias_dia = 0.0
    ventas_contadas = 0
    boleta_actual = []
    total_pagar = 0.0
    vuelto = None
    return redirect(url_for("inicio"))

# --- ADMINISTRACIÓN DE LA CARTA ---

@app.route("/admin/agregar_producto", methods=["POST"])
def admin_agregar():
    nombre = request.form.get("nombre", "").strip()
    try:
        precio = float(request.form.get("precio", 0))
        if nombre and precio >= 0:
            nuevo_id = max([p["id"] for p in carta], default=0) + 1
            carta.append({"id": nuevo_id, "nombre": nombre, "precio": precio, "tipo": "normal"})
    except ValueError:
        pass
    return redirect(url_for("inicio"))

@app.route("/admin/editar_producto", methods=["POST"])
def admin_editar():
    try:
        item_id = int(request.form.get("item_id"))
        nuevo_nombre = request.form.get("nuevo_nombre", "").strip()
        nuevo_precio = float(request.form.get("nuevo_precio", 0))
        
        for p in carta:
            if p["id"] == item_id:
                if nuevo_nombre:
                    p["nombre"] = nuevo_nombre
                if nuevo_precio >= 0:
                    p["precio"] = nuevo_precio
                break
    except ValueError:
        pass
    return redirect(url_for("inicio"))

@app.route("/admin/eliminar_producto/<int:item_id>", methods=["POST"])
def admin_eliminar(item_id):
    global carta
    carta = [p for p in carta if p["id"] != item_id]
    return redirect(url_for("inicio"))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)