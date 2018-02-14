#!/bin/bash

DIR=$(dirname $0)
FROM=xgds_app
TO=${1:-$(basename $DIR)}
APPS_DIR=$DIR/apps
TEMPLATES_DIR=$DIR/management/templates

if [ -d "$APPS_DIR/$TO" ]
then
    echo "$APPS_DIR/$TO already exists; aborting."
    exit 0
fi

cp -r $TEMPLATES_DIR/$FROM $APPS_DIR/$TO
mv $APPS_DIR/$TO/static/$FROM $APPS_DIR/$TO/static/$TO
mv $APPS_DIR/$TO/templates/$FROM $APPS_DIR/$TO/templates/$TO
grep -l -r $FROM $APPS_DIR/$TO | xargs sed -i '' -e "s/$FROM/$TO/g"
rm $0

