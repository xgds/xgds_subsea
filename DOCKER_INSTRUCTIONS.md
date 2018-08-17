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

1. Download xGDS SUBSEA Docker Container and Load it
   * download https://xgds.org/downloads/xgds_subsea_20180817.tar.bz2, don't unzip it, and

1. Load container data into Docker

	```
	docker load -i xgds_subsea_20180817.tar.bz2
	```
	Or just load from stdin:

	```
	docker load < xgds_subsea_20180817.tar.bz2
	```

	Once you have loaded it into Docker, it is safe to delete the zipped file

1. Create Docker data storage container/volume

   ```
   docker create -v /var -v /home/xgds -v /etc -v /usr/local --name subsea-data-store subsea:20180817 /bin/true
   ```

   *Note:* This creates a persistent docker container for the xGDS home directory and database storage.  You generally do *not* want to delete this container unless things are so messed up that you need to start over.

1. Check out the source code on your local computer:
   * cd \<path to xgds_subsea source container directory on your host>\
   * git clone https://github.com/xgds/xgds_subsea
   * cd xgds_subsea
   * git submodule init
   * git submodule update

##### Running and using your Docker container
1. Check if your Docker container is running:

   ```
   docker ps -a
   ```

1. If xgds-subsea is not already in the list, and you *do* have source code checked out on your host, do the following:
   * cd \<path to xgds_subsea source on your host>\
   * ./run-new-container.sh xgds-subsea subsea:20180817 subsea-data-store /<path to xgds_subsea source on your host>/xgds_subsea:/home/xgds/xgds_subsea

1. If xgds-subsea is not already in the list, and you do *not* have source code checked out on your host, just run it (PROBABLY SKIP THIS STEP):

   ```
   docker run -t -d --volumes-from subsea-data-store --name xgds-subsea -p 80:80 -p 3306:3306 -p 7500:7500  -p 222:22 -p 443:443 -p 3001:3001 -p 5000:5000 -p 5984:5984 -p 8080:8080 -p 8181:8181 -p 9090:9090 -p 9191:9191 subsea:20180817
   ```

1. If it is there, but *status* shows "exited" or "created" rather than "Up..." , start it:

   ```
   docker start xgds-subsea
   ```

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

1. Patch missing files from within the docker container (do this only once)
   * There are 2 files within the docker container that should be copied to your xgds_subsea directory.  They are in ~/saveme.
   * then restart web server (see next step)

1. Restarting web server (from within docker container):
   * sudo apachectl restart
     * sudo password will be xgds

1. Access xGDS server
   * http://localhost
   * username and password are both xgds

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
   docker stop xgds-subsea
   ```

   * If you need to change the parameters the container is running with, you'll want to delete it (to save space) and run again per step #2:

   ```
   docker rm xgds-subsea
   ```
   ```
   docker run...
   ```

1. Bing Maps Key
    We use Bing Maps for our xGDS map base layers.  If you want to enable the maps for testing traverse plans, you need to get a Bing Map API key from Microsoft:

    * Go to: https://www.bingmapsportal.com
    * Log in with (or create) a Microsoft Account and generate a map API key.
    * ssh into your running SUBSEA Docker container.
    * Edit ~/xgds_subsea/settings.py (both emacs and vi are available in the container)
    * Insert your API key between the empty quotes in the line setting the XGDS\_MAP\_SERVER\_MAP\_API\_KEY.
    * Also edit ~/sextantwebapp/config/xgds_config.js and replace the key in there with your key.


##### Updating source code
If you already have your docker container set up but need to pull new source code, follow these steps:

1. Change to the main git directory
   ```
   cd xgds_subsea
   ```

1. Pull the latest changes from the top level repository
   ```
   git pull origin master
   ```

1. Update the submodules
   ```
   git submodule update --rebase
   ```

1. Optionally update javascript libraries (only if you are told you need to), from within the docker container
   ```
   cd xgds_subsea
   ./manage.py prepnpm
   ```

1. Prepare any changes from within the docker container
   ```
   cd xgds_subsea
   ./manage.py prep
   ```

1. Restart apache from within the docker container
   ```
   sudo apachectl restart
   ```

##### Updating docker container
1. If you have anything you want to save in the xgds home directory in the docker container, be sure to back it up!  It will be erased as part of this process. You can scp or rsync to a different system and copy back after the new container is running.

1. Stop current container:
   ```
   docker stop xgds-subsea
   ```

1. Delete existing containers and storage to save space:
   ```
   docker rm xgds-subsea
   docker rm subsea-data-store
   docker rmi <imagename>
   docker volume prune
   ```
   Confirm that you *do* want to prune unused volumes

1. Follow instructions on how to load new container from step 3 onwards.


##### Troubleshooting
1. If you can't get to xGDS, the problem is nginx.  Follow the steps above to restart nginx.

1. Or maybe the problem is apache.  Follow the steps above to restart apache.


