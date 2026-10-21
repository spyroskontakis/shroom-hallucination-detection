"""Read-only Modal 1.5.5 checkpoint downloader with per-block timeouts.

Used only when `modal volume get` stalls while downloading 1.7 GB files.
No Modal function, training job, or GPU is started.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path

import aiohttp
from modal.volume import BLOCK_SIZE, _Volume
from modal._utils.async_utils import TaskContext
from modal_proto import api_pb2

ROOT = Path(__file__).resolve().parent
VOLUME = "shroom-e11a-training-results"


async def download(fold: int) -> None:
    assert fold in range(1, 6)
    folder = ROOT / f"fold_{fold}" / f"e11a-fold-{fold:03d}"
    status = json.loads((folder / "FOLD_PASS.json").read_text(encoding="utf-8"))
    assert status["status"] == "PASS" and status["fold_id"] == fold
    expected = status["checkpoint_sha256"]
    target = folder / "final_checkpoint" / "model.safetensors"
    partial = target.with_suffix(".download")
    remote = (f"e11a/folds/fold_{fold}/e11a-fold-{fold:03d}/"
              "final_checkpoint/model.safetensors")

    async with TaskContext():
        volume = _Volume.from_name(VOLUME)
        await volume.hydrate()
        response = await asyncio.wait_for(
            volume.client.stub.VolumeGetFile2(api_pb2.VolumeGetFile2Request(
                volume_id=volume.object_id, path=remote)), timeout=60)
        urls = list(response.get_urls)
        size = int(response.size)
        assert len(urls) == (size + BLOCK_SIZE - 1) // BLOCK_SIZE
        assert size > 1_000_000_000
        print(f"fold={fold} blocks={len(urls)} bytes={size}", flush=True)
        partial.parent.mkdir(parents=True, exist_ok=True)
        semaphore = asyncio.Semaphore(6)
        write_lock = asyncio.Lock()
        timeout = aiohttp.ClientTimeout(total=90, connect=20, sock_read=60)
        completed = 0
        async with aiohttp.ClientSession(timeout=timeout) as session:
            with partial.open("wb+") as handle:
                async def one_block(index: int, url: str) -> None:
                    nonlocal completed
                    expected_size = min(BLOCK_SIZE, size - index * BLOCK_SIZE)
                    for attempt in range(6):
                        try:
                            async with semaphore:
                                async with session.get(url) as reply:
                                    reply.raise_for_status()
                                    data = await reply.read()
                            assert len(data) == expected_size
                            async with write_lock:
                                handle.seek(index * BLOCK_SIZE)
                                handle.write(data)
                                completed += 1
                                if completed % 20 == 0 or completed == len(urls):
                                    print(f"fold={fold} blocks_done={completed}/{len(urls)}",
                                          flush=True)
                            return
                        except (aiohttp.ClientError, asyncio.TimeoutError,
                                AssertionError) as exc:
                            if attempt == 5:
                                raise RuntimeError(
                                    f"fold {fold} block {index} failed after 6 tries") from exc
                            await asyncio.sleep(min(2 ** attempt, 10))

                await asyncio.gather(*(one_block(i, url) for i, url in enumerate(urls)))
                handle.truncate(size)
                handle.flush()
                os.fsync(handle.fileno())

    digest = hashlib.sha256()
    with partial.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    actual = digest.hexdigest()
    assert actual == expected, f"fold {fold} checkpoint SHA mismatch {actual} != {expected}"
    os.replace(partial, target)
    print(f"fold={fold} checkpoint_sha256={actual} PASS", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("fold", type=int, choices=range(1, 6))
    args = parser.parse_args()
    asyncio.run(download(args.fold))
