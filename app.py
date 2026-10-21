
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
import sqlite3
import os

app = Flask(__name__, template_folder=".", static_folder=None)
app.secret_key = os.environ.get("SECRET_KEY", "localconnect-dev-key")

DATABASE = os.path.join(app.root_path, "localconnect.db")


def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db


def init_db():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS businesses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                address TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                image_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


@app.route("/style.css")
def style():
    return send_from_directory(app.root_path, "style.css")


@app.route("/")
def home():
    with get_db() as db:
        businesses = db.execute(
            "SELECT * FROM businesses ORDER BY id DESC"
        ).fetchall()

    return render_template("index.html", businesses=businesses)


@app.route("/add", methods=["POST"])
def add_business():
    name = request.form.get("name", "").strip()
    category = request.form.get("category", "").strip()
    description = request.form.get("description", "").strip()
    address = request.form.get("address", "").strip()
    image_url = request.form.get("image_url", "").strip()

    try:
        latitude = float(request.form.get("latitude", ""))
        longitude = float(request.form.get("longitude", ""))

        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            raise ValueError
    except (ValueError, TypeError):
        flash("Please select a valid location on the map.")
        return redirect(url_for("home") + "#add-shop")

    if not name or not category or not address:
        flash("Please fill in all required fields.")
        return redirect(url_for("home") + "#add-shop")

    if len(name) > 150 or len(category) > 100 or len(address) > 255:
        flash("Please shorten the name, category, or address.")
        return redirect(url_for("home") + "#add-shop")

    if image_url and not image_url.startswith(("https://", "http://")):
        flash("Please enter a valid image URL beginning with http:// or https://.")
        return redirect(url_for("home") + "#add-shop")

    with get_db() as db:
        db.execute("""
            INSERT INTO businesses
            (name, category, description, address,
             latitude, longitude, image_url)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            name, category, description, address,
            latitude, longitude, image_url or None
        ))

    flash("Shop added successfully!")
    return redirect(url_for("home") + "#shops")


@app.route("/delete/<int:business_id>", methods=["POST"])
def delete_business(business_id):
    # Demo only: add login, owner checks and CSRF protection
    # before allowing public access to deletion.
    with get_db() as db:
        cursor = db.execute(
            "DELETE FROM businesses WHERE id = ?",
            (business_id,)
        )

    if cursor.rowcount:
        flash("Shop deleted successfully.")
    else:
        flash("Shop not found.")

    return redirect(url_for("home") + "#shops")


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
