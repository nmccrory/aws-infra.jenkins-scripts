#!/bin/bash -xe
env
if [ "$direction" = "UP" ]; then
   from="_default"
   to="production"
else
  from="production"
  to="_default"
fi

FOLDER="drud-"$sitename
S3ARGS="-k ${AWS_ACCESS_KEY_ID} -sk ${AWS_SECRET_ACCESS_KEY}"
LATEST=$(s3latest $S3ARGS nmdarchive $FOLDER/$from)
S3FROM="s3://nmdarchive/${LATEST}"
S3TO=`echo $S3FROM | sed s/$from/$to/`
STAGINGTO=`echo $S3FROM | sed s/$from/staging/`
s3copy $S3ARGS -n 8 -s 100 -f $S3FROM $S3TO
s3copy $S3ARGS -n 8 -s 100 -f $S3FROM $STAGINGTO
