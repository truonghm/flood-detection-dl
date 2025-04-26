# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "boto3",
#     "tqdm",
# ]
# ///

import os
import argparse
import boto3
import concurrent.futures
from botocore import UNSIGNED
from botocore.config import Config
from tqdm import tqdm


def download_file(s3, bucket, key, destination):
    try:
        if not os.path.exists(destination) or os.path.getsize(destination) == 0:
            print(f"Downloading {key}")
            s3.download_file(bucket, key, destination)
            return True
        else:
            print(f"Skipping {key} (already exists)")
            return False
    except Exception as e:
        print(f"\nError downloading {key}: {e}")
        return False


def download_sen12flood(output_dir, max_workers=16):
    print(f"Downloading sen12flood dataset to {output_dir}")

    # Configure anonymous access with larger multipart threshold and part size
    s3_config = Config(
        signature_version=UNSIGNED,
        max_pool_connections=max_workers,
        retries={"max_attempts": 10, "mode": "adaptive"},
        # Optimized for larger files
        s3={"use_accelerate_endpoint": False},
    )

    s3 = boto3.client("s3", endpoint_url="https://data.source.coop", config=s3_config)

    os.makedirs(output_dir, exist_ok=True)

    # Get all objects first
    print("Listing available files...")
    all_objects = []
    paginator = s3.get_paginator("list_objects_v2")
    pages = paginator.paginate(Bucket="esa", Prefix="sen12flood/")

    for page in pages:
        if "Contents" in page:
            all_objects.extend(page["Contents"])

    total_files = len(all_objects)
    print(f"Found {total_files} files to download")

    # Pre-create all directories to avoid race conditions
    directories = set()
    for obj in all_objects:
        key = obj["Key"]
        destination = os.path.join(output_dir, key)
        directories.add(os.path.dirname(destination))

    for directory in directories:
        os.makedirs(directory, exist_ok=True)

    # Download files in parallel with progress bar
    downloaded = 0
    skipped = 0
    
    # Setup progress bar
    pbar = tqdm(total=total_files, unit='file', desc="Downloading")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        for obj in all_objects:
            key = obj["Key"]
            destination = os.path.join(output_dir, key)
            future = executor.submit(download_file, s3, "esa", key, destination)
            futures[future] = key
        
        for future in concurrent.futures.as_completed(futures):
            key = futures[future]
            if future.result():
                downloaded += 1
                pbar.set_postfix(downloaded=downloaded, skipped=skipped)
            else:
                skipped += 1
                pbar.set_postfix(downloaded=downloaded, skipped=skipped)
            pbar.update(1)
    
    pbar.close()
    print(f"sen12flood dataset download complete. Downloaded {downloaded} new files, skipped {skipped} existing files.")


def main():
    parser = argparse.ArgumentParser(description="Download sen12flood dataset")
    parser.add_argument(
        "--output",
        type=str,
        default="./data/sen12flood",
        help="Output directory (default: ./data/sen12flood)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=16,
        help="Number of concurrent download workers (default: 16)",
    )

    args = parser.parse_args()
    download_sen12flood(args.output, args.workers)
    print(f"Successfully downloaded sen12flood to {args.output}")


if __name__ == "__main__":
    main()
