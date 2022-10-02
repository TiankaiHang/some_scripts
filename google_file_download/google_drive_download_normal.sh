ID=$1
FILENAME=$2

wget --no-check-certificate "https://docs.google.com/uc?export=download&id=$ID" -O $FILENAME
