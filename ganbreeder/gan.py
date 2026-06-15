import random
import threading

import numpy as np

from . import config

_model = None
_lock = threading.Lock()
_rng = np.random.default_rng()


def _get_model():
    global _model
    with _lock:
        if _model is None:
            from pytorch_pretrained_biggan import BigGAN

            path = config.WEIGHTS_DIR / config.MODEL_NAME
            _model = BigGAN.from_pretrained(str(path))
            _model.eval()
        return _model


def truncated_z_sample(batch_size):
    values = _rng.standard_normal((batch_size, config.DIM_Z))
    mask = np.abs(values) > 2
    while mask.any():
        values[mask] = _rng.standard_normal(int(mask.sum()))
        mask = np.abs(values) > 2
    return config.TRUNCATION * values


def create_labels(num, max_classes):
    label = np.zeros((num, config.VOCAB_SIZE))
    for i in range(len(label)):
        for _ in range(random.randint(1, max_classes)):
            j = random.randint(0, config.VOCAB_SIZE - 1)
            label[i, j] = random.random()
        label[i] /= label[i].sum()
    return label


def sample(vectors, labels, batch_size=8):
    import torch

    model = _get_model()
    num = vectors.shape[0]
    ims = []
    with torch.no_grad():
        for start in range(0, num, batch_size):
            s = slice(start, min(num, start + batch_size))
            z = torch.from_numpy(vectors[s]).float()
            y = torch.from_numpy(labels[s]).float()
            out = model(z, y, config.TRUNCATION)
            ims.append(out.cpu().numpy())
    ims = np.concatenate(ims, axis=0).transpose(0, 2, 3, 1)
    ims = np.clip(((ims + 1) / 2.0) * 256, 0, 255)
    return np.uint8(ims)


def create_variations(num, vector, label):
    new_vectors = np.zeros((num, vector.shape[0]))
    new_labels = np.zeros((num, label.shape[0]))

    vector_mutation_rate = vector.std() * 4

    for i in range(num):
        new_labels[i][:] = label
        dv = (np.random.rand(*vector.shape) - 0.5) * vector_mutation_rate
        new_vectors[i] = vector + dv
        new_vectors[i] /= max(-new_vectors.min(), new_vectors.max())

        if random.random() < 0.2:
            opts = np.nonzero(new_labels[i])[0]
            if len(opts) == 1:
                continue
            new_labels[i][random.choice(opts)] *= 0.2 + random.random() * 0.6

        if random.random() < 0.3:
            new_labels[i][random.randint(0, label.shape[0] - 1)] += random.random() * 0.5

        new_labels[new_labels < 0.02] = 0
        new_labels[i] /= new_labels[i].sum()

    return new_vectors, new_labels


def interpolate(num, vector1, vector2, label1, label2):
    x = np.linspace(0, 1, num + 2)
    new_vectors = np.zeros((num, vector1.shape[0]))
    new_labels = np.zeros((num, label1.shape[0]))

    for i, v in enumerate(x[1:-1]):
        new_labels[i] = v * label1 + (1 - v) * label2
        new_vectors[i] = v * vector1 + (1 - v) * vector2

    return new_vectors, new_labels


def create_random_images(num_images, max_classes=3):
    vectors = truncated_z_sample(num_images)
    labels = create_labels(num_images, max_classes)
    ims = sample(vectors, labels)
    return ims, vectors, labels
