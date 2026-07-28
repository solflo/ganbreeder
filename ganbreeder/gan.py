import contextlib
import math
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


@contextlib.contextmanager
def _circular_padding(model):
    """Make every padded conv wrap around, so the render tiles seamlessly."""
    import torch.nn as nn

    padded = [m for m in model.modules() if isinstance(m, nn.Conv2d) and any(m.padding)]
    for module in padded:
        module.padding_mode = "circular"
    try:
        yield
    finally:
        for module in padded:
            module.padding_mode = "zeros"


def _spatial_forward(module, cond_map):
    """
    Replacement batchnorm that modulates each region by its own vector.
    """
    import torch
    import torch.nn.functional as F

    stock = module.forward

    def forward(x, truncation, condition_vector=None):
        if x.numel() > config.SPATIAL_COND_BUDGET:
            return stock(x, truncation, cond_map.mean(dim=(1, 2)))

        def spread(values):
            return F.interpolate(
                values.permute(0, 3, 1, 2),
                size=x.shape[-2:],
                mode="bilinear",
                align_corners=False,
            )

        normed = stock(x, truncation, torch.zeros_like(cond_map[:, 0, 0]))
        return normed * spread(1 + module.scale(cond_map)) + spread(
            module.offset(cond_map)
        )

    return forward


@contextlib.contextmanager
def _spatial_conditioning(model, cond_map):
    from pytorch_pretrained_biggan.model import BigGANBatchNorm

    patched = []
    for module in model.modules():
        if isinstance(module, BigGANBatchNorm) and module.conditional:
            patched.append(module)
            module.forward = _spatial_forward(module, cond_map)
    try:
        yield
    finally:
        for module in patched:
            del module.forward


def _render_grid(model, z, y, grid, variation):
    """
    Generator forward pass over a seed grid larger than the usual 4x4.
    """
    import torch
    from pytorch_pretrained_biggan.model import GenBlock

    gen = model.generator
    cols, rows = grid
    embed = model.embeddings(y)

    def neighbor():
        drawn = truncated_z_sample(z.shape[0]) * config.NEIGHBOR_SPREAD
        return z * (1 - variation) + torch.from_numpy(drawn).float() * variation

    across, down = math.ceil(cols / 4), math.ceil(rows / 4)
    middle = ((down - 1) // 2, (across - 1) // 2)

    vectors = [
        [z if (row, col) == middle else neighbor() for col in range(across)]
        for row in range(down)
    ]
    conds = [[torch.cat((v, embed), dim=1) for v in band] for band in vectors]

    def seed_block(cond):
        block = gen.gen_z(cond).view(-1, 4, 4, 16 * gen.config.channel_width)
        return block.permute(0, 3, 1, 2)

    bands = [torch.cat([seed_block(c) for c in band], dim=3) for band in conds]
    seed = torch.cat(bands, dim=2)[:, :, :rows, :cols].contiguous()

    # [batch, blocks down, blocks across, cond] so a Linear maps the last axis.
    cond_map = torch.stack([torch.stack(band, dim=1) for band in conds], dim=1)

    x = seed
    average = cond_map.mean(dim=(1, 2))
    with contextlib.ExitStack() as stack:
        if variation > 0 and (len(conds) > 1 or len(conds[0]) > 1):
            stack.enter_context(_spatial_conditioning(model, cond_map))
        for layer in gen.layers:
            if isinstance(layer, GenBlock):
                x = layer(x, average, config.TRUNCATION)
            else:
                x = layer(x)
    x = gen.bn(x, config.TRUNCATION)
    x = gen.conv_to_rgb(gen.relu(x))
    return gen.tanh(x[:, :3])


def sample(vectors, labels, batch_size=8, tile=False, grid=(4, 4), variation=None):
    import torch

    if variation is None:
        variation = config.VARIATION
    model = _get_model()
    num = vectors.shape[0]
    ims = []
    with _lock, torch.no_grad(), contextlib.ExitStack() as stack:
        if tile:
            stack.enter_context(_circular_padding(model))
        for start in range(0, num, batch_size):
            s = slice(start, min(num, start + batch_size))
            z = torch.from_numpy(vectors[s]).float()
            y = torch.from_numpy(labels[s]).float()
            if grid == (4, 4):
                out = model(z, y, config.TRUNCATION)
            else:
                out = _render_grid(model, z, y, grid, variation)
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
            new_labels[i][random.randint(0, label.shape[0] - 1)] += (
                random.random() * 0.5
            )

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
