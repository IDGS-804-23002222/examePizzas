from . import pedidos
from flask import render_template, request, redirect, url_for, flash, session
from models import db, Cliente, Pedido, DetallePedido, Pizza, Carrito
import forms
from datetime import date


@pedidos.route("/pedidos", methods=['GET', 'POST'])
def index():

    form_cliente = forms.PedidoFinalForm()
    form_pizza = forms.PizzaForm()
    hoy = date.today()

    if request.method == 'GET':
        if 'cliente_datos' in session:

            form_cliente.nombre.data = session['cliente_datos'].get('nombre')
            form_cliente.direccion.data = session['cliente_datos'].get('direccion')
            form_cliente.telefono.data = session['cliente_datos'].get('telefono')

            fecha_str = session['cliente_datos'].get('fecha')

            if fecha_str:
                form_cliente.fecha.data = date.fromisoformat(fecha_str)
            else:
                form_cliente.fecha.data = hoy
        else:
            form_cliente.fecha.data = hoy

    if request.method == 'POST':

        if 'submit' in request.form:

            p_valida = form_pizza.validate()
            c_valida = form_cliente.validate()

            if p_valida and c_valida:

                session['cliente_datos'] = {
                    'nombre': form_cliente.nombre.data,
                    'direccion': form_cliente.direccion.data,
                    'telefono': form_cliente.telefono.data,
                    'fecha': form_cliente.fecha.data.isoformat()
                }

                precios = {'Chica': 40, 'Mediana': 80, 'Grande': 120}

                subtotal_base = precios.get(form_pizza.tamano.data, 0)

                ingredientes = []
                extras = 0

                if form_pizza.jamon.data:
                    ingredientes.append("Jamón")
                    extras += 10

                if form_pizza.pina.data:
                    ingredientes.append("Piña")
                    extras += 10

                if form_pizza.champinones.data:
                    ingredientes.append("Champiñones")
                    extras += 10

                precio_u = subtotal_base + extras

                subtotal = precio_u * form_pizza.num_pizzas.data

                pizza_temp = Carrito(
                    tamano=form_pizza.tamano.data,
                    ingredientes=", ".join(ingredientes),
                    cantidad=form_pizza.num_pizzas.data,
                    precio_u=precio_u,
                    subtotal=subtotal
                )

                db.session.add(pizza_temp)
                db.session.commit()

                flash(f"Pizza {form_pizza.tamano.data} añadida al carrito")

                return redirect(url_for('.index'))

        if 'confirmar' in request.form:

            if form_cliente.validate():

                carrito = Carrito.query.all()

                if not carrito:
                    flash("Carrito vacío")
                    return redirect(url_for('.index'))

                total_p = sum(item.subtotal for item in carrito)

                try:

                    cliente = Cliente(
                        nombre=form_cliente.nombre.data,
                        direccion=form_cliente.direccion.data,
                        telefono=form_cliente.telefono.data
                    )

                    db.session.add(cliente)
                    db.session.flush()

                    ped = Pedido(
                        id_cliente=cliente.id_cliente,
                        fecha=form_cliente.fecha.data,
                        total=total_p
                    )

                    db.session.add(ped)
                    db.session.flush()

                    for item in carrito:

                        pizza = Pizza(
                            tamano=item.tamano,
                            ingredientes=item.ingredientes,
                            precio=item.precio_u
                        )

                        db.session.add(pizza)
                        db.session.flush()

                        detalle = DetallePedido(
                            id_pedido=ped.id_pedido,
                            id_pizza=pizza.id_pizza,
                            cantidad=item.cantidad,
                            subtotal=item.subtotal
                        )

                        db.session.add(detalle)

                    db.session.commit()

                    Carrito.query.delete()
                    db.session.commit()

                    session.pop('cliente_datos', None)

                    flash("Compra terminada")

                    return redirect(url_for('.index'))

                except Exception as e:

                    db.session.rollback()
                    flash("Error al procesar pedido")

    carrito = Carrito.query.all()

    ventas_dia = Pedido.query.filter_by(fecha=hoy).all()

    total_hoy = sum(v.total for v in ventas_dia)

    return render_template(
        "pedidos/pedidos.html",
        form_cliente=form_cliente,
        form_pizza=form_pizza,
        carrito=carrito,
        ventas_dia=ventas_dia,
        total_ventas_hoy=total_hoy
    )


@pedidos.route("/quitar/<int:id>")
def quitar(id):

    print("ID recibido:", id)

    pizza = Carrito.query.filter_by(id_carrito=id).first()

    if pizza:
        db.session.delete(pizza)
        db.session.commit()
        flash(f"Se quitó la pizza {pizza.tamano} del carrito")
    else:
        print("No se encontró la pizza")

    return redirect(url_for('.index'))