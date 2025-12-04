"""
WHO:
  Antigravity
  (Context: Audio Ingestion System)

WHAT:
  Centralized definition of safe globals for torch.load.

WHEN:
  2025-12-04

WHERE:
  apps/speaker-diarization-benchmark/ingestion/safe_globals.py

WHY:
  To prevent WeightsUnpickler errors when loading Pyannote models with newer PyTorch versions.
"""

def get_safe_globals():
    import torch
    import omegaconf
    import pytorch_lightning
    import typing
    import collections
    from pyannote.audio.core.task import Specifications, Problem, Resolution
    import pyannote.audio.core.model

    return [
        torch.torch_version.TorchVersion,
        omegaconf.listconfig.ListConfig,
        omegaconf.dictconfig.DictConfig,
        Specifications,
        Problem,
        Resolution,
        pyannote.audio.core.model.Introspection,
        pytorch_lightning.callbacks.early_stopping.EarlyStopping,
        pytorch_lightning.callbacks.model_checkpoint.ModelCheckpoint,
        omegaconf.base.ContainerMetadata,
        omegaconf.base.Metadata,
        omegaconf.nodes.AnyNode,
        omegaconf.nodes.StringNode,
        omegaconf.nodes.IntegerNode,
        omegaconf.nodes.FloatNode,
        omegaconf.nodes.BooleanNode,
        typing.Any,
        list,
        dict,
        collections.defaultdict,
        int,
        float,
        str,
        tuple,
        set,
    ]
