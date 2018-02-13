#!/bin/bash

DIR=$(dirname $0)
FROM=basaltApp
TO=${1:-xgds_app}
APPS_DIR=$DIR/../apps
TEMPLATES_DIR=$DIR/templates

echo "cp -r $TEMPLATES_DIR/$FROM $APPS_DIR/$TO"

# cp -r $TEMPLATES_DIR/$BASE_TEMPLATE $APPS_DIR
