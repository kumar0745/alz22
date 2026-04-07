"""
Shared ResNet50 classifier head for training and inference.

Keeping architecture in one place avoids train/serve skew when loading state_dict.
"""

from __future__ import annotations

import torch.nn as nn
from torchvision import models

try:
    _DEFAULT_RESNET_WEIGHTS = models.ResNet50_Weights.IMAGENET1K_V1
except AttributeError:
    _DEFAULT_RESNET_WEIGHTS = True  # type: ignore[assignment]


def build_resnet50_classifier(
    num_classes: int,
    *,
    dropout_p: float = 0.4,
    weights=None,
) -> nn.Module:
    """
    ImageNet-pretrained ResNet50 with a small regularized head (dropout + linear).

    Args:
        num_classes: Number of output classes (dataset folder count).
        dropout_p: Dropout before the final linear layer (reduces overfitting).
        weights: Pretrained weights enum or None for random init (tests only).
    """
    w = _DEFAULT_RESNET_WEIGHTS if weights is None else weights
    m = models.resnet50(weights=w)
    in_f = m.fc.in_features
    m.fc = nn.Sequential(
        nn.Dropout(p=dropout_p),
        nn.Linear(in_f, num_classes),
    )
    return m


def set_backbone_requires_grad(model: nn.Module, requires: bool) -> None:
    """Freeze or unfreeze all parameters except the final `fc` head."""
    for name, p in model.named_parameters():
        if name.startswith("fc."):
            p.requires_grad = True
        else:
            p.requires_grad = requires
