"""Image → tensor pipeline (ImageNet normalization, same as validation during training)."""

from __future__ import annotations

import io
from typing import TYPE_CHECKING

from PIL import Image
from torchvision import transforms

from config import IMG_SIZE

if TYPE_CHECKING:
    import torch

VAL_TRANSFORM = transforms.Compose(
    [
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ]
)


def load_image_from_bytes(data: bytes) -> Image.Image:
    return Image.open(io.BytesIO(data)).convert("RGB")


def image_to_tensor(pil_image: Image.Image) -> "torch.Tensor":
    import torch

    t = VAL_TRANSFORM(pil_image)
    return t.unsqueeze(0)
