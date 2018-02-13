#!/bin/bash

DIR=$(dirname $0)
FROM=basaltApp
TO=${1:-xgds_app}
APPS_DIR=$DIR/../apps
TEMPLATES_DIR=$DIR/templates

cp -r $TEMPLATES_DIR/$FROM $APPS_DIR/$TO
mv $APPS_DIR/$TO/static/$FROM $APPS_DIR/$TO/static/$TO
mv $APPS_DIR/$TO/templates/$FROM $APPS_DIR/$TO/templates/$TO
grep -l -r $FROM $APPS_DIR/$TO | xargs echo
