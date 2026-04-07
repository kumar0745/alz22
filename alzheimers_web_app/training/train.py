"""
Production-style training: stratified train / validation / test splits, transfer learning
with a short head-only phase then full fine-tune, early stopping on validation macro-F1,
and checkpointing `weights.pt` (state_dict) for safe deployment.

Dataset: ../dataset/<ClassName>/*.jpg|*.png
Outputs: ../backend/model/weights.pt, model_metadata.json, training_metrics.json
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader, Dataset
from torchvision import datasets, transforms

# Shared architecture with inference server (backend/)
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "backend"))
from model_factory import build_resnet50_classifier, set_backbone_requires_grad  # noqa: E402

DATASET_DIR = _ROOT / "dataset"
OUT_DIR = _ROOT / "backend" / "model"

EPOCHS = 32
BATCH = 16
LR = 2e-4
WEIGHT_DECAY = 1e-4
DROPOUT_P = 0.4
SEED = 42
TEST_RATIO = 0.15
VAL_RATIO_WITHIN_TRAINVAL = 0.15 / (1.0 - TEST_RATIO)
HEAD_ONLY_EPOCHS = 3
EARLY_STOP_PATIENCE = 8
IMG_SIZE = 224


def set_seed() -> None:
    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(SEED)
        torch.backends.cudnn.benchmark = True


class ImageFolderSubset(Dataset):
    """Indexed subset of ImageFolder with transforms applied after loading."""

    def __init__(self, root: str, indices: list[int], transform):
        self.base = datasets.ImageFolder(root, transform=None)
        self.indices = indices
        self.transform = transform

    def __len__(self) -> int:
        return len(self.indices)

    def __getitem__(self, i: int):
        from torchvision.datasets.folder import default_loader

        real_idx = self.indices[i]
        path, target = self.base.samples[real_idx]
        img = default_loader(path)
        if self.transform is not None:
            img = self.transform(img)
        return img, target


def build_optimizer(model: nn.Module, lr: float, wd: float, *, head_only: bool) -> torch.optim.Optimizer:
    if head_only:
        return torch.optim.AdamW(model.fc.parameters(), lr=lr, weight_decay=wd)
    backbone_params: list[nn.Parameter] = []
    head_params: list[nn.Parameter] = []
    for name, p in model.named_parameters():
        if not p.requires_grad:
            continue
        if name.startswith("fc."):
            head_params.append(p)
        else:
            backbone_params.append(p)
    return torch.optim.AdamW(
        [
            {"params": backbone_params, "lr": lr * 0.12},
            {"params": head_params, "lr": lr},
        ],
        weight_decay=wd,
    )


def evaluate_loader(
    model: nn.Module,
    loader: DataLoader,
    device: torch.device,
    crit: nn.Module,
) -> tuple[float, float, list[int], list[int]]:
    """Returns (loss, acc, y_true, y_pred)."""
    model.eval()
    loss_sum = 0.0
    correct = 0
    total = 0
    all_y: list[int] = []
    all_p: list[int] = []
    with torch.no_grad():
        for x, y in loader:
            x, y = x.to(device), y.to(device)
            logits = model(x)
            loss_sum += crit(logits, y).item() * x.size(0)
            pred = logits.argmax(dim=1)
            correct += (pred == y).sum().item()
            total += y.size(0)
            all_y.extend(y.cpu().tolist())
            all_p.extend(pred.cpu().tolist())
    n = len(all_y)
    return loss_sum / max(n, 1), correct / max(total, 1), all_y, all_p


def macro_f1(y_true: list[int], y_pred: list[int], num_classes: int) -> float:
    return float(
        f1_score(y_true, y_pred, average="macro", labels=list(range(num_classes)), zero_division=0)
    )


def run_epoch_train(
    model: nn.Module,
    loader: DataLoader,
    device: torch.device,
    opt: torch.optim.Optimizer,
    crit: nn.Module,
) -> float:
    model.train()
    total_loss = 0.0
    n = 0
    for x, y in loader:
        x, y = x.to(device), y.to(device)
        opt.zero_grad(set_to_none=True)
        logits = model(x)
        loss = crit(logits, y)
        loss.backward()
        opt.step()
        total_loss += loss.item() * x.size(0)
        n += x.size(0)
    return total_loss / max(n, 1)


def main() -> None:
    set_seed()
    if not DATASET_DIR.is_dir():
        raise SystemExit(f"Dataset not found: {DATASET_DIR}")

    probe = datasets.ImageFolder(str(DATASET_DIR))
    n = len(probe)
    if n < 12:
        raise SystemExit(
            f"Need at least ~12 images across classes under {DATASET_DIR} (found {n}). "
            "Add more MRI slices per class for stable splits."
        )

    indices = np.arange(n)
    try:
        targets = np.array(probe.targets)
    except AttributeError:
        targets = np.array([s[1] for s in probe.samples])

    try:
        train_val_idx, test_idx = train_test_split(
            indices,
            test_size=TEST_RATIO,
            stratify=targets,
            random_state=SEED,
        )
        targets_tv = targets[train_val_idx]
        train_idx, val_idx = train_test_split(
            train_val_idx,
            test_size=VAL_RATIO_WITHIN_TRAINVAL,
            stratify=targets_tv,
            random_state=SEED,
        )
    except ValueError:
        train_val_idx, test_idx = train_test_split(
            indices, test_size=TEST_RATIO, random_state=SEED
        )
        train_idx, val_idx = train_test_split(
            train_val_idx,
            test_size=VAL_RATIO_WITHIN_TRAINVAL,
            random_state=SEED,
        )

    train_idx = np.asarray(train_idx).tolist()
    val_idx = np.asarray(val_idx).tolist()
    test_idx = np.asarray(test_idx).tolist()
    class_names = probe.classes
    num_classes = len(class_names)

    train_tf = transforms.Compose(
        [
            transforms.Resize((IMG_SIZE + 32, IMG_SIZE + 32)),
            transforms.RandomCrop(IMG_SIZE),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomRotation(degrees=10),
            transforms.RandomAffine(degrees=0, translate=(0.04, 0.04)),
            transforms.ColorJitter(brightness=0.1, contrast=0.1),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            transforms.RandomErasing(p=0.06, scale=(0.02, 0.07)),
        ]
    )
    eval_tf = transforms.Compose(
        [
            transforms.Resize((IMG_SIZE, IMG_SIZE)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )

    train_ds = ImageFolderSubset(str(DATASET_DIR), train_idx, train_tf)
    val_ds = ImageFolderSubset(str(DATASET_DIR), val_idx, eval_tf)
    test_ds = ImageFolderSubset(str(DATASET_DIR), test_idx, eval_tf)

    train_loader = DataLoader(
        train_ds,
        batch_size=BATCH,
        shuffle=True,
        num_workers=0,
        pin_memory=torch.cuda.is_available(),
    )
    val_loader = DataLoader(
        val_ds,
        batch_size=BATCH,
        shuffle=False,
        num_workers=0,
        pin_memory=torch.cuda.is_available(),
    )
    test_loader = DataLoader(
        test_ds,
        batch_size=BATCH,
        shuffle=False,
        num_workers=0,
        pin_memory=torch.cuda.is_available(),
    )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = build_resnet50_classifier(num_classes, dropout_p=DROPOUT_P).to(device)
    crit = nn.CrossEntropyLoss()

    best_f1 = 0.0
    best_state: dict | None = None
    epochs_no_gain = 0
    opt: torch.optim.Optimizer | None = None
    sched: torch.optim.lr_scheduler.ReduceLROnPlateau | None = None
    last_epoch = 0

    for epoch in range(EPOCHS):
        last_epoch = epoch + 1
        if epoch == 0:
            set_backbone_requires_grad(model, False)
            opt = build_optimizer(model, LR, WEIGHT_DECAY, head_only=True)
            sched = torch.optim.lr_scheduler.ReduceLROnPlateau(
                opt, mode="max", factor=0.45, patience=2
            )
        elif epoch == HEAD_ONLY_EPOCHS:
            set_backbone_requires_grad(model, True)
            opt = build_optimizer(model, LR, WEIGHT_DECAY, head_only=False)
            sched = torch.optim.lr_scheduler.ReduceLROnPlateau(
                opt, mode="max", factor=0.45, patience=2
            )

        assert opt is not None and sched is not None
        head_only = epoch < HEAD_ONLY_EPOCHS
        train_loss = run_epoch_train(model, train_loader, device, opt, crit)
        val_loss, val_acc, y_val, p_val = evaluate_loader(model, val_loader, device, crit)
        val_f1 = macro_f1(y_val, p_val, num_classes)
        sched.step(val_f1)

        print(
            f"epoch {epoch + 1}/{EPOCHS}  phase={'head' if head_only else 'full'}  "
            f"train_loss={train_loss:.4f}  val_loss={val_loss:.4f}  "
            f"val_acc={val_acc:.4f}  val_f1_macro={val_f1:.4f}"
        )

        if val_f1 > best_f1 + 1e-5:
            best_f1 = val_f1
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
            epochs_no_gain = 0
        else:
            epochs_no_gain += 1

        if epochs_no_gain >= EARLY_STOP_PATIENCE and epoch >= HEAD_ONLY_EPOCHS + 2:
            print(f"Early stopping at epoch {epoch + 1} (no val F1 gain for {EARLY_STOP_PATIENCE} epochs).")
            break

    if best_state is None:
        best_state = {k: v.detach().cpu() for k, v in model.state_dict().items()}

    model.load_state_dict(best_state)
    model.eval()

    def metrics_dict(y_true: list[int], y_pred: list[int]) -> dict:
        return {
            "accuracy": float(accuracy_score(y_true, y_pred)),
            "precision_macro": float(
                precision_score(y_true, y_pred, average="macro", zero_division=0)
            ),
            "recall_macro": float(recall_score(y_true, y_pred, average="macro", zero_division=0)),
            "f1_macro": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
            "classification_report": classification_report(
                y_true,
                y_pred,
                target_names=class_names,
                digits=4,
                zero_division=0,
            ),
            "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
        }

    _, _, y_val, p_val = evaluate_loader(model, val_loader, device, crit)
    _, _, y_test, p_test = evaluate_loader(model, test_loader, device, crit)

    val_metrics = metrics_dict(y_val, p_val)
    test_metrics = metrics_dict(y_test, p_test)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    torch.save(best_state, OUT_DIR / "weights.pt")
    meta = {
        "class_names": class_names,
        "num_classes": num_classes,
        "architecture": "resnet50_transfer_v2",
        "img_size": IMG_SIZE,
        "dropout": DROPOUT_P,
        "weights_file": "weights.pt",
        "train_config": {
            "epochs_ran": last_epoch,
            "head_only_epochs": HEAD_ONLY_EPOCHS,
            "best_val_f1_macro": best_f1,
            "splits": {"test_ratio": TEST_RATIO, "val_within_trainval": VAL_RATIO_WITHIN_TRAINVAL},
        },
    }
    (OUT_DIR / "model_metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    full_report = {
        "validation": {k: v for k, v in val_metrics.items() if k != "classification_report"},
        "validation_classification_report_text": val_metrics["classification_report"],
        "test": {k: v for k, v in test_metrics.items() if k != "classification_report"},
        "test_classification_report_text": test_metrics["classification_report"],
        "note": "Test metrics are on a held-out set never used for early stopping or checkpointing.",
    }
    (OUT_DIR / "training_metrics.json").write_text(json.dumps(full_report, indent=2), encoding="utf-8")

    print("\n=== Validation (model selection) ===")
    print(val_metrics["classification_report"])
    print("\n=== Test (held-out) — report this for demos / papers ===")
    print(test_metrics["classification_report"])
    print(f"\nSaved state_dict → {OUT_DIR / 'weights.pt'}")
    print(f"Saved metadata  → {OUT_DIR / 'model_metadata.json'}")


if __name__ == "__main__":
    main()
