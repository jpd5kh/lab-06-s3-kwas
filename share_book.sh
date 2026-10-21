#!/bin/bash
# Exit if command fails or undefined variable is used
set -euo pipefail

#Check that all arguments are provided
if [ "$#" -lt 3 ]; then
	echo "Usage: $0 <URL> <BUCKET> <EXPIRE>"
	exit 1
fi

# Defines positional arguments
URL=$1
BUCKET=$2
EXPIRE=$3

# Creates variable FILENAME
FILENAME=$(basename "$URL")

# Checks if bucket exists and makes new one if not
mkdir -p books
curl -kfL "$URL" -o "books/$FILENAME"

if ! aws s3api head-bucket --bucket "$BUCKET"; then
	aws s3 mb s3://"$BUCKET"
fi 

# Uploads book and creates URL
aws s3 cp books/"$FILENAME" s3://"$BUCKET" --content-type "text/plain; charset=utf=8"
aws s3 presign s3://"$BUCKET"/"$FILENAME" --expires-in $EXPIRE
