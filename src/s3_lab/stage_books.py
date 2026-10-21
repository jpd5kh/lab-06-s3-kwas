#!/usr/bin/env python3

import logging
import os
import sys
import boto3
from botocore.exceptions import ClientError
import time
import requests
import json

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

s3 = boto3.client("s3", region_name="us-east-1")

def parse_args():
	"""Reads three arguments from sys.argv."""
	try:
		list_file = sys.argv[1]
		index_path = sys.argv[2]
		bucket = sys.argv[3] 
		return (list_file, index_path, bucket)
		log.info(f"Arguments read successfully")
	except IndexError as e:
		log.error(f"Fewer than three arguments: {e}")
		sys.exit(1)
		
def download_books(list_file, dest_dir):
	"""Downloads books from file and saves to folder."""
	downloaded = []
	os.makedirs(dest_dir, exist_ok=True)
	with open(list_file, "r") as file:
		for line in file:
			url = line.strip()
			if not url:
				continue
			filename = os.path.basename(url)
			path = os.path.join(dest_dir, filename)
			if os.path.exists(path):
				downloaded.append(path)
				continue
			try:
				response = requests.get(url, timeout=30)
				response.raise_for_status()
				with open(path, "wb") as file:
   	            			file.write(response.content)
				downloaded.append(path)
				log.info(f"Books downloaded successfully")
			except requests.RequestException as e:
				log.error(f"Error downloading {url}: {e}")
			finally:
				time.sleep(1)
	return downloaded
	
def create_bucket(bucket):
	"""Creates bucket to store data."""
	try:
		s3.head_bucket(Bucket=bucket)
		log.info(f"Bucket already created")
		return True
		
	except ClientError as e:
		log.error(f"Error: {bucket} check failed")
		try:
			s3.create_bucket(Bucket=bucket)
			log.info(f"Created bucket: {bucket}")
			return True
		except ClientError as e:
			log.error(f"Error creating bucket {bucket}: {e}")
			return False		

def make_public(bucket):
	"""Makes bucket public."""
	try:
		s3.put_public_access_block(
   	            Bucket=bucket,
   		    PublicAccessBlockConfiguration={
       		        "BlockPublicAcls": False,
       		        "IgnorePublicAcls": False,
       		        "BlockPublicPolicy": False,
                        "RestrictPublicBuckets": False,
   		    },
                ) 
		policy = {
 				 "Version": "2012-10-17",
 				 "Statement": [
   				   {
     					 "Effect": "Allow",
     					 "Principal": "*",
     					 "Action": "s3:GetObject",
     					 "Resource": f"arn:aws:s3:::{bucket}/*"
   				   }
 				 ]			
			 }
		s3.put_bucket_policy(Bucket=bucket, Policy=json.dumps(policy))
		log.info(f"Bucket successfully made public")
		return True
	except ClientError as e:
		log.error(f"Error making {bucket} public: {e}")
		return False
	
def upload_files(bucket, file_paths):
	"""Uploads files to bucket."""
	uploaded = 0
	for local_file in file_paths:
		key = os.path.basename(local_file)
		try:
			with open(local_file, "rb") as f:
				s3.put_object(
					Bucket=bucket,
					Key=key,
					Body=f,
					ContentType="text/plain; charset=utf-8"
				)
			uploaded += 1
			log.info(f"Uploaded {local_file} to s3://{bucket}/{key}")
		except FileNotFoundError:
			log.error(f"Local file not found: {local_file}")
		except ClientError as e:
			log.error(f"Error uploading object: {e}")
	return uploaded
		

def upload_index(bucket, index_path):
	"Uploads index file to bucket."""
	try:
		s3.upload_file(
			Filename=index_path,
			Bucket=bucket,
			Key="index.html",
			ExtraArgs={"ContentType": "text/html"}
		)
		log.info(f"Index successfully uploaded.")
		return True
	except FileNotFoundError:
                log.error(f"Local file not found: {index_path}")
                return False
	except ClientError as e:
                log.error(f"Error uploading object: {e}")
                return False
def main():
	"""Runs the full bucket pipeline."""
	try:
		list_file, index_path, bucket = parse_args()
		books = download_books(list_file, "books")
		if not books:
			log.error("Books not downloaded")
			sys.exit(1)
		if not create_bucket(bucket):
			log.error("Bucket creation failed")
			sys.exit(1)
		if not make_public(bucket):
			log.error("Make bucket public failed")
			sys.exit(1)
		files = upload_files(bucket, books)
		if not upload_index(bucket, index_path):
			log.error("Failed to upload index.html")
			sys.exit(1)
		log.info("Main function finished successfully")
		url = f"https://{bucket}.s3.amazonaws.com/index.html"
		log.info(f"Public URL: {url}")
	except Exception as e:
		log.error(f"Main function failed: {e}")
		sys.exit(1)
		
if __name__ == "__main__":
	main()
