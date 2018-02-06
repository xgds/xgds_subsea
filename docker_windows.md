Use -v to share local volumes:

```
docker run -t -d --volumes-from basalt-data-store --name basalt-container -p 80:80 -p 3306:3306 -p 7500:7500  -p 222:22 -p 443:443 -p 3001:3001 -p 5000:5000 -p 5984:5984 -p 8080:8080 -p 8181:8181 -p 9090:9090 -p 9191:9191 -v *localpath*:/home/xgds/sextantwebapp -v *localpath*:/home/xgds/xgds_basalt/submodules/pextant xgds-basalt-sse:20171019
```

It does not work to share the file from within the docker to your local windows folder, and then share it back to the docker with the -v. 

Instead share each source code file needed. This will break the symlink in the docker. Fix it from within the docker:

```
cd xgds_basalt/apps/
ls -al  # you will see your broken symbolic link, in this example pextant
rm pextant # don't worry it's just the symbolic link
ln -s ../submodules/pextant pextant  # normally we nest things and you have not
```

If you get a 500 error or 502 error:

```
sudo apachectl restart
```

If you still have the error:
Sometimes apache does not play nicely with django.  We have it set up to autostart right now. 
To get apache to fully stop, in docker:

```
cd /etc/services
sudo mv apache2 /tmp
sudo apachectl stop #now it is really stopped
sudo mv /tmp/apache2 .
#now it is autostarted and will work perfectly
```

If you are missing javascript files like jquery bootstrap etc (look in the debug console in your browser) this configuration of docker probably doesn't have its bower components linked to the build directory.  Verify in docker:

```
cd xgds_basalt/build
ls static
#if static does not exist or is empty
cd .. #back to xgds_basalt
./manage.py prep
```
