"""Value-level bindings for the actual tensors used by a correction call."""

import hashlib
import json


def tensor_digest(tensor):
    import torch

    header = json.dumps(dict(shape=list(tensor.shape), dtype=str(tensor.dtype)), sort_keys=True)
    digest = hashlib.sha256(header.encode())
    digest.update(tensor.detach().cpu().contiguous().view(torch.uint8).numpy().tobytes())
    return digest.hexdigest()
