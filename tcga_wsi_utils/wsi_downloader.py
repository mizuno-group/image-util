#!/usr/bin/env python3
"""
Created on 2025-12-18 (Thu) 13:58:58

This script retrieves and downloads TCGA whole-slide image (SVS) files from the GDC.

It first queries the GDC /files API to resolve given SVS filenames (optionally adding the .svs suffix) to file UUIDs and metadata within a specified TCGA project, batching requests to avoid oversized queries.
It then downloads each file from the GDC /data endpoint using streamed requests with progress bars, retry logic, and optional authentication tokens, saving files safely via temporary .part files.

@author: I.Azuma
"""
import time
from pathlib import Path

import requests
from tqdm import tqdm

GDC_API = "https://api.gdc.cancer.gov"
FILES_ENDPT = f"{GDC_API}/files"
DATA_ENDPT  = f"{GDC_API}/data"


def chunked(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i+n]

def fetch_file_records(file_names, project_id="TCGA-BRCA", chunk_size=200, sleep=0.1):
    """
    file_names: list of *.svs
    return: dict {file_name: {"id":..., "file_size":..., "md5sum":..., "access":...}}
    """
    fields = ["id", "file_name", "file_size", "md5sum", "access", "cases.project.project_id"]
    results = {}

    # check the format (.svs)
    if all(fn.lower().endswith(".svs") for fn in file_names):
        pass
    else:
        file_names = [
            fn if fn.lower().endswith(".svs") else f"{fn}.svs"
            for fn in file_names
    ]

    for block in tqdm(list(chunked(file_names, chunk_size)), desc="Query GDC /files"):
        # filters: (file_name in block) AND (cases.project.project_id == TCGA-BRCA)
        filters = {
            "op": "and",
            "content": [
                {"op": "in", "content": {"field": "file_name", "value": block}},
                {"op": "=",  "content": {"field": "cases.project.project_id", "value": project_id}},
            ],
        }

        payload = {
            "filters": filters,
            "fields": ",".join(fields),
            "format": "JSON",
            "size": str(len(block) * 5),
        }

        r = requests.post(FILES_ENDPT, json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()

        hits = data.get("data", {}).get("hits", [])
        for h in hits:
            fn = h["file_name"]
            results[fn] = {
                "id": h["id"],
                "file_size": h.get("file_size"),
                "md5sum": h.get("md5sum"),
                "access": h.get("access"),
                "project_id": (
                    h.get("cases", [{}])[0]
                     .get("project", {})
                     .get("project_id", None)
                ) if h.get("cases") else None,
            }

        time.sleep(sleep)

    return results

def download_gdc_file(file_uuid, save_path: Path, token: str | None = None,
                      chunk_bytes=1024*1024*8, max_retries=5):
    headers = {}
    if token:
        headers["X-Auth-Token"] = token

    url = f"{DATA_ENDPT}/{file_uuid}"  # /data/{uuid} :contentReference[oaicite:4]{index=4}

    if save_path.exists() and save_path.stat().st_size > 0:
        return

    for attempt in range(1, max_retries + 1):
        try:
            with requests.get(url, headers=headers, stream=True, timeout=300) as r:
                r.raise_for_status()
                total = int(r.headers.get("Content-Length", 0))

                tmp_path = save_path.with_suffix(save_path.suffix + ".part")
                with open(tmp_path, "wb") as f, tqdm(
                    total=total, unit="B", unit_scale=True, desc=save_path.name, leave=False
                ) as pbar:
                    for chunk in r.iter_content(chunk_size=chunk_bytes):
                        if not chunk:
                            continue
                        f.write(chunk)
                        pbar.update(len(chunk))

                tmp_path.replace(save_path)
            return

        except Exception as e:
            if attempt == max_retries:
                raise
            time.sleep(2 * attempt)

if __name__ == "__main__":
    # Example usage
    target_ids = ["TCGA-78-7220-01Z-00-DX1.3df84ce0-4395-4c9e-ba62-76b55676a440",
                  "TCGA-80-5611-01Z-00-DX1.31920706-8AF4-46D2-B1D4-7DD5AF4AAC77"]
    records = fetch_file_records(target_ids, project_id="TCGA-LUAD")

    out_dir = Path("./TCGA_LUAD_SVS")
    out_dir.mkdir(parents=True, exist_ok=True)

    GDC_TOKEN = None  # open("gdc-token.txt").read().strip()

    for fn, meta in tqdm(records.items(), desc="Download SVS"):
        uuid = meta["id"]
        save_path = out_dir / fn
        download_gdc_file(uuid, save_path, token=GDC_TOKEN)

    print("done")
