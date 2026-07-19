import json
import math

import numpy as np
from flask import Flask, abort, jsonify, render_template, request, send_from_directory

from . import config, db, gan, store
from .labels import LABELS

ROOT = "/img/"
SORTED_LABELS = sorted(enumerate(LABELS), key=lambda p: p[1].lower())

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


@app.get("/randombatch")
def randombatch():
    ims, vectors, labels = gan.create_random_images(config.SEED_COUNT)
    store.store(ims, vectors, labels)
    return render_template("generator.html", keys=db.recent_keys(), root=ROOT)


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
    return jsonify(
        {"vector": json.loads(row["vector"]), "label": json.loads(row["label"])}
    )


@app.get("/create")
def create_page():
    return render_template("create.html", label_options=SORTED_LABELS, root=ROOT)


@app.get("/edit")
def edit_page():
    key = request.args.get("k")
    row = key and db.get_by_key(key)
    if not row:
        abort(404)
    label = json.loads(row["label"])
    genes = {i: v for i, v in enumerate(label) if v != 0}
    return render_template(
        "edit.html", key=key, genes=genes, label_options=SORTED_LABELS, root=ROOT
    )


def _dense_label(genes):
    if not isinstance(genes, dict) or not genes or len(genes) > 50:
        abort(400)
    label = np.zeros((1, config.VOCAB_SIZE))
    for index, weight in genes.items():
        try:
            i = int(index)
        except (TypeError, ValueError):
            abort(400)
        if not (0 <= i < config.VOCAB_SIZE):
            abort(400)
        if not isinstance(weight, (int, float)) or not math.isfinite(weight):
            abort(400)
        label[0, i] = min(max(float(weight), -1.0), 1.0)
    total = np.abs(label).sum()
    if total <= 0:
        abort(400)
    label /= total
    return label


@app.post("/generate_image")
def generate_image():
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        abort(400)
    label = _dense_label(body.get("label"))
    key = body.get("key")
    if key:
        row = db.get_by_key(key)
        if not row:
            abort(404)
        vector = np.asarray(json.loads(row["vector"]), dtype="float64")[None, :]
        parent1 = row["id"]
    else:
        vector = gan.truncated_z_sample(1)
        parent1 = None
    ims = gan.sample(vector, label)
    keys = store.store(ims, vector, label, parent1=parent1)
    return jsonify({"key": keys[0]})


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
    keys = store.store(
        ims, new_vectors, new_labels, parent1=img1["id"], parent2=img2["id"]
    )
    return jsonify([{"key": k} for k in keys])


@app.post("/star")
def star():
    key = request.get_json().get("key")
    if not key:
        abort(400)
    db.add_star(key)
    return "", 200
