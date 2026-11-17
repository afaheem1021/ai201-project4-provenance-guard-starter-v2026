"""Download the pinned model, without scoring text, and print its actual file sizes."""
import argparse
import json
from pathlib import Path

import config

MODEL_FILES = ['config.json', 'generation_config.json', 'merges.txt', 'model.safetensors',
               'tokenizer_config.json', 'tokenizer.json', 'vocab.json']


def manifest(local_only=False):
    from huggingface_hub import snapshot_download
    folder = Path(snapshot_download(repo_id=config.DETECTOR_MODEL, revision=config.DETECTOR_REVISION,
                                   allow_patterns=MODEL_FILES, local_files_only=local_only))
    files = [{'name': name, 'bytes': (folder / name).stat().st_size} for name in MODEL_FILES]
    return {'model': config.DETECTOR_MODEL, 'revision': config.DETECTOR_REVISION,
            'files': files, 'total_bytes': sum(item['bytes'] for item in files)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--local-only', action='store_true')
    args = parser.parse_args()
    print(json.dumps(manifest(args.local_only), indent=2))
