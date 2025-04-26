# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "google-cloud-storage",
#     "tqdm",
# ]
# ///

import os
import argparse
import concurrent.futures
from google.cloud import storage
from tqdm import tqdm


def download_blob(blob, destination, pbar=None):
    try:
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        
        if not os.path.exists(destination) or os.path.getsize(destination) == 0:
            blob.download_to_filename(destination)
            if pbar:
                pbar.update(1)
            return True
        else:
            if pbar:
                pbar.update(1)
            return False
    except Exception as e:
        print(f"\nError downloading {blob.name}: {e}")
        if pbar:
            pbar.update(1)
        return False


def download_sen1floods11(output_dir, max_workers=16):
    print(f"Downloading sen1floods11 dataset to {output_dir}")
    
    client = storage.Client.create_anonymous_client()
    bucket = client.bucket("sen1floods11")
    
    os.makedirs(output_dir, exist_ok=True)
    
    print("Listing available files...")
    blobs = list(bucket.list_blobs())
    total_files = len(blobs)
    print(f"Found {total_files} files to download")
    
    # Pre-create directories to avoid race conditions
    directories = set()
    for blob in blobs:
        destination = os.path.join(output_dir, blob.name)
        directories.add(os.path.dirname(destination))
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    downloaded = 0
    skipped = 0
    
    # Setup progress bar
    pbar = tqdm(total=total_files, unit='file', desc="Downloading")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        for blob in blobs:
            destination = os.path.join(output_dir, blob.name)
            future = executor.submit(download_blob, blob, destination, pbar)
            futures[future] = blob.name
        
        for future in concurrent.futures.as_completed(futures):
            if future.result():
                downloaded += 1
                pbar.set_postfix(downloaded=downloaded, skipped=skipped)
            else:
                skipped += 1
                pbar.set_postfix(downloaded=downloaded, skipped=skipped)
    
    pbar.close()
    print(f"sen1floods11 dataset download complete. Downloaded {downloaded} new files, skipped {skipped} existing files.")


def main():
    parser = argparse.ArgumentParser(description="Download sen1floods11 dataset")
    parser.add_argument(
        "--output",
        type=str,
        default="./data/sen1floods11",
        help="Output directory (default: ./data/sen1floods11)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=16,
        help="Number of concurrent download workers (default: 16)",
    )
    
    args = parser.parse_args()
    download_sen1floods11(args.output, args.workers)
    print(f"Successfully downloaded sen1floods11 to {args.output}")


if __name__ == "__main__":
    main()
