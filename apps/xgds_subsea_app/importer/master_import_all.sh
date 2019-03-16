
# This script does all the steps to preprocess and then do an import
# you must be in

# configure directories
BASE_DIR=/root/xgds_subsea
DATA_DIR=$BASE_DIR/data
CRUISE_ID=NA100
IMPORT_CONFIG=$BASE_DIR/apps/xgds_subsea_app/importer/ImportHandlerConfig.yaml

source $BASE_DIR/sourceme.sh

# preprocess nav data
echo "*** PREPROCESSING NAV DATA FROM $DATA_DIR/$CRUISE_ID"
$BASE_DIR/apps/xgds_subsea_app/importer/preprocess_nav_data.py $DATA_DIR/$CRUISE_ID
echo "*** DONE PREPROCESSING NAV DATA FROM $DATA_DIR/$CRUISE_ID"

# preprocess video episodes
echo "*** PREPROCESSING VIDEO EPISODES FROM $DATA_DIR/$CRUISE_ID"
$BASE_DIR/apps/xgds_subsea_app/scripts/computeEpisodeLengths.py --dataDir $DATA_DIR
echo "*** DONE PREPROCESSING VIDEO EPISODES FROM $DATA_DIR/$CRUISE_ID"

# preprocess temperature probe data
echo "*** PREPROCESSING VIDEO EPISODES FROM $DATA_DIR/$CRUISE_ID"
$BASE_DIR/apps/xgds_subsea_app/importer/preprocess_temp_probe_data.py $DATA_DIR/$CRUISE_ID
echo "*** DONE PREPROCESSING VIDEO EPISODES FROM $DATA_DIR/$CRUISE_ID"

# do the actual import
echo "*** CALLING IMPORTER FROM $IMPORT_CONFIG"
$BASE_DIR/apps/xgds_core/importer/importHandler.py --user xgds --password TODO_CHANGEME $IMPORT_CONFIG
echo "*** DONE CALLING IMPORTER FROM $IMPORT_CONFIG"

