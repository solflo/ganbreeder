import json

import numpy as np
from flask import Flask, abort, jsonify, render_template, request, send_from_directory

from . import config, db, gan, store
from .labels import LABELS

ROOT = "/img/"

app = Flask(
    __name__,
    template_folder=str(config.TEMPLATES_DIR),
    static_folder=str(config.STATIC_DIR),
    static_url_path="",
)


@app.get("/img/<path:filename>")
def image_file(filename):
    return send_from_directory(config.IMG_DIR, filename)


@app.get("/")
def index():
    return render_template("random.html", keys=db.homepage_keys(), root=ROOT)


@app.get("/i")
def image_page():
    key = request.args.get("k")
    row = key and db.get_by_key(key)
    if not row:
        abort(404)
    pkey = db.key_of_id(row["parent1"]) if row["parent1"] is not None else None
    label = json.loads(row["label"])
    return render_template(
        "image.html", key=key, pkey=pkey, label=label, label_names=LABELS, root=ROOT
    )


@app.get("/info")
def info():
    key = request.args.get("k")
    row = key and db.get_by_key(key)
    if not row:
        abort(404)
    return jsonify({"vector": json.loads(row["vector"]), "label": json.loads(row["label"])})


@app.get("/mix")
def mix_page():
    return render_template("mix.html", root=ROOT)


@app.get("/starred")
def starred_page():
    return render_template("starred.html", root=ROOT)


@app.get("/latest")
def latest_page():
    page = request.args.get("page", 0, type=int)
    return render_template("latest.html", images=db.latest(page), page=page, root=ROOT)


@app.get("/lineage")
def lineage_page():
    key = request.args.get("k")
    if not key:
        abort(404)
    return render_template("lineage.html", key=key, parents=db.lineage(key), root=ROOT)


@app.post("/image_children")
def image_children():
    key = request.get_json().get("key")
    row = key and db.get_by_key(key)
    if not row:
        abort(404)
    existing = db.children_keys(row["id"])
    if existing:
        return jsonify([{"key": k} for k in existing])
    vector = np.asarray(json.loads(row["vector"]), dtype="float64")
    label = np.asarray(json.loads(row["label"]), dtype="float64")
    new_vectors, new_labels = gan.create_variations(config.NUM_CHILDREN, vector, label)
    ims = gan.sample(new_vectors, new_labels)
    keys = store.store(ims, new_vectors, new_labels, parent1=row["id"])
    return jsonify([{"key": k} for k in keys])


@app.post("/mix_images")
def mix_images():
    body = request.get_json()
    img1, img2 = db.get_by_key(body.get("key1")), db.get_by_key(body.get("key2"))
    if not img1 or not img2:
        abort(400)
    v1 = np.asarray(json.loads(img1["vector"]), dtype="float64")
    v2 = np.asarray(json.loads(img2["vector"]), dtype="float64")
    l1 = np.asarray(json.loads(img1["label"]), dtype="float64")
    l2 = np.asarray(json.loads(img2["label"]), dtype="float64")
    new_vectors, new_labels = gan.interpolate(config.NUM_CHILDREN, v1, v2, l1, l2)
    ims = gan.sample(new_vectors, new_labels)
    keys = store.store(ims, new_vectors, new_labels,
                       parent1=img1["id"], parent2=img2["id"])
    return jsonify([{"key": k} for k in keys])


@app.post("/star")
def star():
    key = request.get_json().get("key")
    if not key:
        abort(400)
    db.add_star(key)
    return "", 200
