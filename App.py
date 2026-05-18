from flask import Flask, render_template, request, redirect, session
import mysql.connector

app = Flask(__name__)

app.secret_key = "joel_secret"

# ================= DB =================
conexion = mysql.connector.connect(
    host="localhost",
    user="root",
    password="320083747",
    database="cafeteria_db"
)

cursor = conexion.cursor(dictionary=True)

# ================= LOGIN =================
@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        usuario = request.form["usuario"]
        password = request.form["password"]

        cursor.execute(
            "SELECT * FROM usuarios WHERE usuario=%s AND password=%s",
            (usuario, password)
        )

        user = cursor.fetchone()

        if user:

            session["usuario"] = user["usuario"]
            session["rol"] = user["rol"]

            return redirect("/menu")

    return render_template("login.html")


# ================= MENU =================
@app.route("/menu")
def menu():

    if "usuario" not in session:
        return redirect("/")

    return render_template(
        "menu.html",
        usuario=session["usuario"],
        rol=session["rol"]
    )


# ================= TABLAS DINÁMICAS =================
@app.route("/tabla/<nombre>")
def tabla(nombre):

    if "usuario" not in session:
        return redirect("/")

    cursor.execute(f"SHOW COLUMNS FROM {nombre}")

    columnas_db = cursor.fetchall()

    columnas = []

    for col in columnas_db:
        columnas.append(col["Field"])

    cursor.execute(f"SELECT * FROM {nombre}")

    datos = cursor.fetchall()

    columnas_form = []

    # ================= NUEVO =================
    id_principal = columnas[0]

    for col in columnas:

        if col != id_principal:
            columnas_form.append(col)

    return render_template(
        "tabla.html",
        tabla=nombre,
        datos=datos,
        columnas=columnas,
        columnas_form=columnas_form
    )


# ================= AGREGAR DINÁMICO =================
@app.route("/agregar/<tabla>", methods=["POST"])
def agregar(tabla):

    datos = request.form.to_dict()

    columnas = []
    valores = []

    for key, value in datos.items():

        columnas.append(key)
        valores.append(value)

    sql = f"""
    INSERT INTO {tabla}
    ({",".join(columnas)})
    VALUES
    ({",".join(["%s"] * len(valores))})
    """

    cursor.execute(sql, valores)

    conexion.commit()

    return redirect(f"/tabla/{tabla}")


# ================= ELIMINAR DINÁMICO =================
@app.route("/eliminar/<tabla>/<int:id>")
def eliminar(tabla, id):

    cursor.execute(f"SHOW COLUMNS FROM {tabla}")

    columnas = cursor.fetchall()

    id_columna = columnas[0]["Field"]

    sql = f"""
    DELETE FROM {tabla}
    WHERE {id_columna}=%s
    """

    cursor.execute(sql, (id,))

    conexion.commit()

    return redirect(f"/tabla/{tabla}")


# ================= EDITAR DINÁMICO =================
@app.route("/editar/<tabla>/<int:id>", methods=["GET", "POST"])
def editar(tabla, id):

    cursor.execute(f"SHOW COLUMNS FROM {tabla}")

    columnas_db = cursor.fetchall()

    columnas = []

    for col in columnas_db:
        columnas.append(col["Field"])

    id_columna = columnas[0]

    columnas_form = []

    # ================= NUEVO =================
    for col in columnas:

        if col != id_columna:
            columnas_form.append(col)

    if request.method == "POST":

        datos = request.form.to_dict()

        updates = []
        valores = []

        for key, value in datos.items():

            updates.append(f"{key}=%s")
            valores.append(value)

        valores.append(id)

        sql = f"""
        UPDATE {tabla}
        SET {",".join(updates)}
        WHERE {id_columna}=%s
        """

        cursor.execute(sql, valores)

        conexion.commit()

        return redirect(f"/tabla/{tabla}")

    cursor.execute(
        f"SELECT * FROM {tabla} WHERE {id_columna}=%s",
        (id,)
    )

    fila = cursor.fetchone()

    return render_template(
        "editar.html",
        tabla=tabla,
        fila=fila,
        columnas_form=columnas_form,
        id_columna=id_columna
    )


# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():

    if "usuario" not in session:
        return redirect("/")

    # ================= VENTAS HOY =================
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM ventas
        WHERE DATE(fecha)=CURDATE()
    """)

    ventas_hoy = cursor.fetchone()["total"]

    # ================= VENTAS MES =================
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM ventas
        WHERE MONTH(fecha)=MONTH(CURDATE())
    """)

    ventas_mes = cursor.fetchone()["total"]

    # ================= GASTOS HOY =================
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM gastos
        WHERE DATE(fecha)=CURDATE()
    """)

    gastos_hoy = cursor.fetchone()["total"]

    return render_template(
        "dashboard.html",
        ventas_hoy=ventas_hoy,
        ventas_mes=ventas_mes,
        gastos_hoy=gastos_hoy
    )


# ================= LOGOUT =================
@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)