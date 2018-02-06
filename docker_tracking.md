## Instructions for running xGDS in docker and simulating EVA tracks.

##### Initial Installation
1. Install Docker
   * Docker for Mac is here: https://docs.docker.com/docker-for-mac/install/
   * Docker for Windows is here: https://docs.docker.com/docker-for-windows/install/

    *System Requirements*  
    
      * Mac: OSX 10.11 or newer.
      * Windows: Windows 10.
      * Linux: Not tested, but current versions should work.
      * **Note**: We tested with the "stable" release of Docker
      
   Strongly recommend installing and using kitematic to allow easy management of docker containers, ports and volumes.

1. Download xGDS BASALT Docker Container and Load it
   * download https://xgds.org/downloads/xgds-basalt-sse-20171019.tbz, don't unzip it, and

1. Load container data into Docker  

	```
	docker load -i xgds-basalt-sse-20171019.tbz
	```  
	Or just load from stdin:
	
	```
	docker load < xgds-basalt-sse-20171019.tbz
	```  
	
	Once you have loaded it into Docker, it is safe to delete the zipped file
	
1. Create Docker data storage container/volume

   ```
   docker create -v /var -v /home/xgds -v /etc -v /usr/local --name basalt-data-store xgds-basalt-sse:TAG /bin/true
   ```  
   
   Where you replace *TAG* by the docker tag associated with the current distribution(e.g. 20171019 for current version)
   *Note:* This creates a persistent docker container for the xGDS home directory and database storage.  You generally do *not* want to delete this container unless things are so messed up that you need to start over.
   
##### Running and using your Docker container 
1. Check if your Docker container is running:  

   ```
   docker ps -a
   ```

1. If basalt-container is not already in the list, and you do *not* have source code checked out on your host, just run it:  

   ```
   docker run -t -d --volumes-from basalt-data-store --name basalt-container -p 80:80 -p 3306:3306 -p 7500:7500  -p 222:22 -p 443:443 -p 3001:3001 -p 5000:5000 -p 5984:5984 -p 8080:8080 -p 8181:8181 -p 9090:9090 -p 9191:9191 xgds-basalt-wristapp:20170802
   ```

1. If basalt-container is not already in the list, and you *do* have source code checked out on your host, do the following:
   * cd \<path to xgds_basalt source on your host\
   * ./run-new-container.sh \<path to xgds_basalt on your host\> \<path to sextantwebapp source on your host\>
   
1. If it is there, but *status* shows "exited" or "created" rather than "Up..." , start it:  

   ```
   docker start basalt-container
   ```
   
1. Access xGDS server
   * http://localhost
   * username and password are both xgds

1. Log into the docker container
   * password is xgds

   ```
   ssh -p 222 xgds@localhost
   ```
   Windows with PUTTY installed (make sure it is on your PATH):
  
   ```
   putty -ssh -P 222 xgds@localhost
   ```
   
   This should open a new terminal where you are successfully ssh-ed in
   
1. Start the track generator
   * Log into Docker container per step #4.  

   ```
   cd xgds_basalt/apps/basaltApp/scripts
   ```
   ```
   ./evaTrackGenerator.py -i 1 -p 10001 -t /home/xgds/xgds_basalt/apps/basaltApp/scripts/test_data/20160526G_EV2_Ames.csv
   ```
   ```
   ctrl-c to stop track generation
   ```
   
   
   * Note this will read in a csv file with lat, lon as the positions so if you have your own file you can load that too.
   * Note that by default xGDS is currently centered on Ames (but this will change)
   * -i is the interval (in seconds) for updates
   * If you want to generate 2 tracks, do this for EV2 (same track slower interval:
   
   ```
   ./evaTrackGenerator.py -i 2 -p 10002 -t /home/xgds/xgds_basalt/apps/basaltApp/scripts/test_data/20160526G_EV2_Ames.csv
   ```
   
   * If you want to simulate tracking with heading, have heading as the 3rd column in the csv.  There is an example here. In this case you 
   can also pass in -r 1 or -r 2 for EV1 or EV2.  It defaults to 1.
   
   ```
   ./evaTrackGenerator.py -i 1 -p 10001 -t /home/xgds/xgds_basalt/apps/basaltApp/scripts/test_data/20171105A_EV2_Kilauea.csv
   ```
   

1. Create an EVA in xGDS and start it.
   * http://localhost/xgds_planner2/addGroupFlight
   * Uncheck EV2 and SA
   * Click Create
   * For the newly created EVA, click the green 'start' button on this page: http://localhost/xgds_planner2/manage/
     * Once started that row should turn light green.
     * In the terminal running the evaTrackGenerator you should see position data

1. View the generated track in Google Earth
   * http://localhost/xgds_map_server/feedPage/
   * Click on “Open in Google Earth” button to download the KML network link file with tracking data (note you only have to do this once; next time just open Google Earth).
   * Double-click the downloaded KML file to open it in Google Earth.
     * Expand xGDS Maps on the left sidebar
     * Check and expand Live Position tracks
     * You should see a Today folder, expand that and turn on the flight that is running
       * Note that this is rerunning that 20161114A_EV2_trunc.csv file.  If you want to work with other data you can create analogous csv files as pass them as parameters to the track generator
    
1. Stop the EVA:
   * For active EVA, click the red 'stop' button on this page: http://localhost/xgds_planner2/manage/
     * Once stopped that row should no longer be light green.
     * In the terminal running the evaTrackGenerator you should stop seeing position data

1. Schedule a plan
   * In order to see the plan in the sextant web app, it has to be the last plan scheduled for today.  To do that, go to the planned traverses page:
     * https://localhost/xgds_planner2/index/
     * Check on the planned traverse you want to schedule (if you don't have any planned traverses, create one in the region you are working in)
     * IMPORTANT -- you need to have your BING map key in place in order for any map pages including the planner to work.
     * Select a crew (you have to have set up the crew with mass on the crew mass tab)
     * Select the EVA (it will be one of the last ones)
     * Click the 'when' and just click now
     * Click schedule.

1. Get SEXTANT DEM:
   * Ames.tif is already in place, you only have to do this if you are testing for a different area)
   * Download SEXTANT DEM from BASALT server (there are several) :
     https://basalt.xgds.org/data/dem
   * Copy from your computer to the data directory in the docker container:

   ```
   scp -P 222 <local-path-to-DEM> xgds@localhost:xgds_basalt/data/dem
   ```
   
   Windows with PUTTY installed (make sure it is on your PATH):
   
   ```
   pscp -P 222 local-path-to-DEM.tim xgds@localhost:xgds_basalt/data/dem
   ```

1. Run Sextantwebapp
   * Log into Docker container per step #4.
   * Determine what configuration you want to run.  Inside of sextantwebapp, there is a config directory.  
      * By default, sextantwebapp runs iphone_xgds_config.js
      * This can be overridden in the terminal by typing
         * export CONFIG_PATH='./name_of_config_in_config_directory.js'
         * ie export CONFIG_PATH='./xgds_config.js'
         * the latter is what we have set up for you in this docker instance
         * therefore to run with the iphone you will have to remove CONFIG_PATH from .bashrc in the home directory 
      * If you want to run from iphone with no problems you need an ssl certificate with the hostname of the machine running your xGDS & sextantwebapp
      * Once you have this set up, you can put that everywhere there is an ip address inside of iphone_xgds_config.js
      * You must ideally update iphone_xgds_config.js to have a hostname that matches your development
   
   ```
   cd sextantwebapp
   babel-node server.js babel-node index.js --presets es2015,stage-2
   ```
   
   Hit the sextantweb app in a browser:  https://localhost/wristApp/mobile.html
   
   See more instructions here: https://github.com/xgds/sextantwebapp/blob/master/tutorial.md

1. Restarting web server (from within docker container):
   * sudo apachectl restart
     * sudo password will be xgds

1. Seeing apache log (from within docker container):
   * sudo tail -f -n 100 /var/log/apache2/error.log
     * ctrl-c to stop

1. Restart nginx server (from within docker container):
   * sudo /etc/init.d/nginx stop
   * sudo /etc/init.d/nginx start
     * sudo password will be xgds

1. Stop Docker container:
   * Docker containers are fairly lightweight but if you need to stop it, just:

   ```
   docker stop basalt-container
   ```

   * If you need to change the parameters the container is running with, you'll want to delete it (to save space) and run again per step #2:   

   ```
   docker rm basalt-container
   ```  
   ```
   docker run...
   ```

1. Bing Maps Key  
    We use Bing Maps for our xGDS map base layers.  If you want to enable the maps for testing traverse plans, you need to get a Bing Map API key from Microsoft:
    
    * Go to: https://www.bingmapsportal.com
    * Log in with (or create) a Microsoft Account and generate a map API key.
    * ssh into your running BASALT Docker container.
    * Edit ~/xgds_basalt/settings.py (both emacs and vi are available in the container)
    * Insert your API key between the empty quotes in the line setting the XGDS\_MAP\_SERVER\_MAP\_API\_KEY.
    * Also edit ~/sextantwebapp/config/xgds_config.js and replace the key in there with your key. 

##### Storing xGDS code on your host system
If you are doing intensive developemnt connected to the xGDS codebase (e.g. for SEXTANT) you may want to store the xGDS source directory on your host machine's file system instead of inside the docker container. This might help to make changes and debugging easier, depending on your development environment.
Do the analagous step for the sextantwebapp project as well.

Here is the procedure:

   1. ssh into your docker container (ssh -p 222 xgds@localhost)
   
   1. create a tar file of the xgds_basalt directory:  
     ```
     tar cvfz ./xgds_basalt.tgz ./xgds_basalt
     ```
      * *note:* on windows you can use 7Zip to manage tar files.
   
   1. Log out of docker and copy the tar file to your host system:
     ```
     scp -P 222 xgds@localhost:xgds_basalt.tgz .
     ```
      * Uncompress the tar file in the location of your choice.
   
   1. Stop the docker container:  
     ```
     docker stop basalt-container
     ```
   
   1. Delete it:  
     ```
     docker rm basalt-container
     ```
   
   1. Run the docker image like this:
     ```
     docker run -t -d -v <path to xgds_basalt on host>:/home/xgds/xgds_basalt --volumes-from basalt-data-store --name basalt-container -p 80:80 -p 3306:3306 -p 7500:7500  -p 222:22 -p 443:443 -p 3001:3001 -p 5000:5000 -p 5984:5984 -p 8080:8080 -p 8181:8181 -p 9090:9090 -p 9191:9191 xgds-basalt
     ```
     
     This will hide the xgds_basalt directory in the docker data volume and use the copy on your host system instead.  Any changes you make to the code on the host side will be reflected in the docker container.
     
     **Note:** If you do make changes to xGDS code you will need to follow the same procedure as when you update from git to prepare the new code and restart Apache.
     
     If you are also editing sextant web app, you'll want a command like this:
     ```
     docker run -t -d -v <path to xgds_basalt on host>:/home/xgds/xgds_basalt -v <path to sextantwebapp on host>:/home/xgds/sextantwebapp --volumes-from basalt-data-store --name basalt-container -p 80:80 -p 3306:3306 -p 7500:7500  -p 222:22 -p 443:443 -p 3001:3001 -p 5000:5000 -p 5984:5984 -p 8080:8080 -p 8181:8181 -p 9090:9090 -p 9191:9191 xgds-basalt
     ```

##### Updating source code
If you already have your docker container set up but need to pull new source code, follow these steps:

1. Log into the docker container (see above)

1. Change to the main git directory
   ```
   cd xgds_basalt
   ```
 
1. Pull the latest changes from the top level repository
   ```
   git pull origin master
   ```
   
1. Update the submodules
   ```
   git submodule update --rebase
   ```
    
1. Optionally update javascript libraries (only if you are told you need to)
   ```
   ./manage.py bower update
   ```

1. Prepare any changes
   ```
   ./manage.py prep
   ```
 
1. Restart apache
   ```
   sudo apachectl restart
   ```  

##### Updating docker container
1. If you have anything you want to save in the xgds home directory in the docker container, be sure to back it up!  It will be erased as part of this process. You can scp or rsync to a different system and copy back after the new container is running. 

1. Stop current container:
   ```
   docker stop basalt-container
   ```
   
1. Delete existing containers and storage to save space:
   ```
   docker rm basalt-container
   docker rm basalt-data-store
   docker rmi xgds-basalt
   docker volume prune
   ```
   Confirm that you *do* want to prune unused volumes 
   
1. Follow instructions on how to load new container from step 3 onwards. 


##### Troubleshooting
1. If you can't get to the wrist app or xGDS, the problem is nginx.  Follow the steps above to restart nginx.

1. If you can't get to just xGDS, the problem is apache.  Follow the steps above to restart apache.

1. If you've made a change to some node code in the wrist app, it will automatically compile.  If the compilation fails, you will see the output in the terminal where you are running babel-node.
 
