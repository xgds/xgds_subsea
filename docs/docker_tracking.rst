Instructions for running xGDS in docker and simulating EVA tracks.

1. Check if docker is running:
::
  docker ps

2. If basalt-container is not in the list, start it:
::
  docker run -t -d --volumes-from basalt-data-store --name basalt-container -p 80:80 -p 3306:3306 -p 7500:7500  -p 222:22  xgds-basalt

3. Access xGDS server
- `<http://localhost>`_
- username and password are both xgds

4. Log into the docker container
- password is xgds
::
  ssh -p 222 xgds@localhost

5. Get SEXTANT DEM:
- Download SEXTANT DEM from BASALT server (there are several, choose at least Hawaii_Lava_Flows.tif) :
`<https://basalt.xgds.org/data/dem/>`_
- Copy from your computer to the data directory in the docker container:
::
  scp -P 222 <local-path-to-DEM> xgds@localhost:xgds_basalt/data/dem

6. Start the track generator
::
  cd xgds_basalt/apps/basaltApp/scripts
  ./evaTrackGenerator.py -i 1 -p 10001 -t /home/xgds/xgds_basalt/apps/basaltApp/scripts/test_data/20161114A_EV2_trunc.csv

7. Create an EVA in xGDS and start it.
- `<http://localhost/xgds_planner2/addGroupFlight/>`_
- Uncheck EV2 and SA
- click Create
- For the newly created EVA, click the green 'start' button on this page: http://localhost/xgds_planner2/manage/
  - Once started that row should turn light green.
  - In the terminal running the evaTrackGenerator you should see position data

8. View the generated track in Google Earth
- `<http://localhost/xgds_map_server/feedPage/>`_
- Click on “Open in Google Earth” button  (note you only have to do this once; next time just open Google Earth)
- Expand xGDS Maps on the left sidebar
- Check and expand Live Position tracks
- You should see a Today folder, expand that and turn on the flight that is running
  - Note that this is rerunning that 20161114A_EV2_trunc.csv file.  If you want to work with other data you can create analogous csv files as pass them as parameters to the track generator
 