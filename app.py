from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os

app = Flask(__name__)
app.secret_key = 'restaurante_secret_key_123'

# Carta inicial de productos
carta_inicial = [
    {'id': '1', 'nombre': 'Sopa Verde', 'precio': 8.00, 'tipo': 'normal'},
    {'id': '2', 'nombre': 'Chupe de Olluco', 'precio': 10.00, 'tipo': 'normal'},
    {'id': '3', 'nombre': 'Segundo de Pollo', 'precio': 12.00, 'tipo': 'normal'},
    {'id': '4', 'nombre': 'Chaufa Especial', 'precio': 15.00, 'tipo': 'normal'},
    {'id': '5', 'nombre': 'Agua Mineral', 'precio': 2.50, 'tipo': 'normal'},
    {'id': '6', 'nombre': 'Café Pasado', 'precio': 3.50, 'tipo': 'normal'},
    {'id': '7', 'nombre': 'Pan con Chicharrón', 'precio': 7.00, 'tipo': 'normal'}
]

def obtener_carta():
    if 'carta' not in session:
        session['carta'] = carta_inicial
    return session['carta']

def obtener_boleta_agrupada():
    boleta_raw = session.get('boleta', [])
    agrupada = {}
    total = 0.0
    for item in boleta_raw:
        nombre = item['nombre']
        precio = float(item['precio'])
        total += precio
        if nombre in agrupada:
            agrupada[nombre]['cantidad'] += 1
            agrupada[nombre]['subtotal'] += precio
        else:
            agrupada[nombre] = {
                'nombre': nombre,
                'precio_unitario': precio,
                'cantidad': 1,
                'subtotal': precio
            }
    return list(agrupada.values()), total

@app.route('/')
def index():
    carta = obtener_carta()
    boleta_agrupada, total = obtener_boleta_agrupada()
    ganancias = session.get('ganancias', 0.0)
    ventas_num = session.get('ventas_num', 0)
    vuelto = session.get('vuelto', None)
    
    return render_template('index.html', 
                           carta=carta, 
                           boleta=boleta_agrupada, 
                           total=total, 
                           ganancias=ganancias, 
                           ventas_num=ventas_num, 
                           vuelto=vuelto)

@app.route('/agregar/<item_id>', methods=['POST'])
def agregar(item_id):
    carta = obtener_carta()
    producto = next((item for item in carta if str(item['id']) == str(item_id)), None)
    if producto:
        if 'boleta' not in session:
            session['boleta'] = []
        boleta = session['boleta']
        boleta.append(producto)
        session['boleta'] = boleta
    
    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        boleta_agrupada, total = obtener_boleta_agrupada()
        return jsonify({'boleta': boleta_agrupada, 'total': total})
    return redirect(url_for('index'))

@app.route('/agregar_extra', methods=['POST'])
def agregar_extra():
    monto = request.form.get('monto_extra') or (request.json.get('monto_extra') if request.is_json else None)
    if monto:
        try:
            precio = float(monto)
            if 'boleta' not in session:
                session['boleta'] = []
            boleta = session['boleta']
            boleta.append({'nombre': 'Extra / Especial', 'precio': precio, 'tipo': 'extra'})
            session['boleta'] = boleta
        except ValueError:
            pass
            
    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        boleta_agrupada, total = obtener_boleta_agrupada()
        return jsonify({'boleta': boleta_agrupada, 'total': total})
    return redirect(url_for('index'))

@app.route('/cobrar', methods=['POST'])
def cobrar():
    data = request.get_json() if request.is_json else request.form
    pago_str = data.get('pago', 0)
    _, total = obtener_boleta_agrupada()
    
    try:
        pago = float(pago_str)
        if pago >= total and total > 0:
            vuelto = pago - total
            session['ganancias'] = session.get('ganancias', 0.0) + total
            session['ventas_num'] = session.get('ventas_num', 0) + 1
            session['vuelto'] = vuelto
            vuelto_res = f"S/ {vuelto:.2f}"
            error_res = None
        elif total == 0:
            vuelto_res = None
            error_res = "La boleta está vacía"
        else:
            vuelto_res = None
            error_res = "Monto insuficiente"
    except ValueError:
        vuelto_res = None
        error_res = "Ingrese un monto válido"

    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'vuelto': vuelto_res,
            'error': error_res,
            'ganancias': session.get('ganancias', 0.0),
            'ventas_num': session.get('ventas_num', 0)
        })
    
    return redirect(url_for('index'))

@app.route('/nueva_boleta', methods=['POST'])
def nueva_boleta():
    session['boleta'] = []
    session['vuelto'] = None
    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'status': 'ok'})
    return redirect(url_for('index'))

@app.route('/reiniciar_caja', methods=['POST'])
def reiniciar_caja():
    session['ganancias'] = 0.0
    session['ventas_num'] = 0
    session['boleta'] = []
    session['vuelto'] = None
    return redirect(url_for('index'))

@app.route('/admin/agregar_producto', methods=['POST'])
def admin_agregar():
    nombre = request.form.get('nombre')
    precio = float(request.form.get('precio', 0))
    carta = obtener_carta()
    nuevo_id = str(len(carta) + 1)
    carta.append({'id': nuevo_id, 'nombre': nombre, 'precio': precio, 'tipo': 'normal'})
    session['carta'] = carta
    return redirect(url_for('index'))

@app.route('/admin/editar_producto', methods=['POST'])
def admin_editar():
    item_id = request.form.get('item_id')
    nuevo_nombre = request.form.get('nuevo_nombre')
    nuevo_precio = request.form.get('nuevo_precio')
    carta = obtener_carta()
    for item in carta:
        if str(item['id']) == str(item_id):
            if nuevo_nombre:
                item['nombre'] = nuevo_nombre
            if nuevo_precio:
                item['precio'] = float(nuevo_precio)
            break
    session['carta'] = carta
    return redirect(url_for('index'))

@app.route('/admin/eliminar_producto/<item_id>', methods=['POST'])
def admin_eliminar(item_id):
    carta = obtener_carta()
    carta = [item for item in carta if str(item['id']) != str(item_id)]
    session['carta'] = carta
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
