"""Grad-CAM for inference (ResNet50 last conv in layer4)."""

from __future__ import annotations

import base64
import io

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image


def _target_layer(model: torch.nn.Module) -> torch.nn.Module:
    if hasattr(model, "layer4"):
        block = model.layer4[-1]
        if hasattr(block, "conv3"):
            return block.conv3
        return block
    raise ValueError("Expected a ResNet-style model with layer4")


def compute_gradcam(
    model: torch.nn.Module,
    x: torch.Tensor,
    class_idx: int,
) -> np.ndarray:
    model.eval()
    activations: list[torch.Tensor] = []
    gradients: list[torch.Tensor] = []
    layer = _target_layer(model)

    def fwd_hook(_m, _inp, out):
        activations.append(out.detach())

    def bwd_hook(_m, _gin, gout):
        if gout[0] is not None:
            gradients.append(gout[0].detach())

    h1 = layer.register_forward_hook(fwd_hook)
    h2 = layer.register_full_backward_hook(bwd_hook)
    try:
        out = model(x)
        model.zero_grad(set_to_none=True)
        score = out[0, class_idx]
        score.backward()
    finally:
        h1.remove()
        h2.remove()

    if not activations or not gradients:
        raise RuntimeError("Grad-CAM failed")

    a = activations[0][0]
    g = gradients[0][0]
    w = g.mean(dim=(1, 2))
    cam = (w[:, None, None] * a).sum(dim=0)
    cam = F.relu(cam)
    cmin, cmax = cam.min(), cam.max()
    cam = (cam - cmin) / (cmax - cmin + 1e-8)
    return cam.cpu().numpy()


def overlay_cam_base64(pil_image: Image.Image, cam: np.ndarray, alpha: float = 0.45) -> str:
    """Jet colormap overlay → base64 PNG string."""
    from matplotlib import colormaps

    h, w = cam.shape
    img = pil_image.convert("RGB").resize((w, h))
    arr = np.asarray(img).astype(np.float32) / 255.0
    heat = colormaps["jet"](cam)[:, :, :3].astype(np.float32)
    blended = np.clip((1 - alpha) * arr + alpha * heat, 0, 1)
    out = Image.fromarray((blended * 255).astype(np.uint8))
    buf = io.BytesIO()
    out.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")
