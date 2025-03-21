import json
import boto3
import requests
import logging
import traceback

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def lambda_handler(event, context):
    logger.info("Lambda function started.")
    logger.debug(f"Event received: {json.dumps(event)}")

    # IMDb dataset file names
    imdb_files = [
        "name.basics.tsv.gz",
        "title.akas.tsv.gz",
        "title.basics.tsv.gz",
        "title.crew.tsv.gz",
        "title.episode.tsv.gz",
        "title.principals.tsv.gz",
        "title.ratings.tsv.gz",
    ]

    base_url = "https://datasets.imdbws.com/"
    s3_bucket = "lambda-move-fetch-dir"  # Replace with your S3 bucket name
    s3_prefix = "imdb/"

    # Initialize Boto3 client for S3 (only region needed for download step)
    try:
        logger.info("Initializing S3 client...")
        s3_client = boto3.client("s3", region_name="us-east-1")
    except Exception as e:
        logger.error("Error initializing AWS clients.")
        logger.error(traceback.format_exc())
        return {"statusCode": 500, "body": str(e)}

    downloaded_files = []

    # Download and upload each IMDb file
    for file_name in imdb_files:
        file_url = base_url + file_name
        s3_key = s3_prefix + file_name
        logger.info(f"Downloading file: {file_url}")

        try:
            response = requests.get(file_url, timeout=30)
            if response.status_code == 200:
                file_size = len(response.content)
                logger.info(f"Downloaded {file_name} successfully ({file_size} bytes).")

                logger.info(f"Uploading {file_name} to S3 at s3://{s3_bucket}/{s3_key}")
                s3_client.put_object(
                    Bucket=s3_bucket, Key=s3_key, Body=response.content
                )
                downloaded_files.append(f"s3://{s3_bucket}/{s3_key}")
                logger.info(f"Uploaded {file_name} to S3 successfully.")
            else:
                logger.warning(
                    f"Failed to download {file_name}: HTTP {response.status_code}"
                )
        except Exception as e:
            logger.error(f"Error downloading {file_name}: {str(e)}")
            logger.error(traceback.format_exc())

    if not downloaded_files:
        logger.error("No files were downloaded. Exiting function.")
        return {"statusCode": 500, "body": "No files were downloaded."}

    logger.info("Download and upload process completed.")
    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": "IMDb data downloaded and uploaded to S3 successfully.",
                "downloadedFiles": downloaded_files,
                "s3Prefix": s3_prefix,
            }
        ),
    }
