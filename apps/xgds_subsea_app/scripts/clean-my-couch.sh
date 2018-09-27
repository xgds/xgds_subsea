#!/bin/bash

read -p "About to DELETE the subsea-file-store DB on $1 and create an empty one. Are you sure (yes or no)? " -r
if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]
then
    # delete current database
    curl -X DELETE http://$1:5984/subsea-file-store
    # create new empty one
    curl -X PUT http://$1:5984/subsea-file-store
    # install design (query) documents
    curl -X PUT http://$1:5984/braille-file-store/"_design/deepzoom" -d @./couchViews.js
fi
