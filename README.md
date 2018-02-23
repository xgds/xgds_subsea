# Initializing a repository for a new site

For purposes of example, `xgds_site` will be used in place of the site-specific
application name (e.g. `xgds_rp` or `xgds_basalt`).

To initialize a new site-specific repository `xgds_site`:

```bash
git clone https://github.com/xgds/xgds_baseline.git xgds_site
cd xgds_site
./init.sh
```

(Ignore warnings from `sed`.)

The `./init.sh` script will detect your directory name and create a 
skeleton for site-specific content under `apps/xgds_site_app`. If you want 
to provide a name explicitly, run as `./init.sh xgds_some_name`.

Next, edit `siteSettings.py`. In particular, uncomment any `INSTALLED_APPS`
that will be needed for the new site. Many apps will also have related 
configuration variables to uncomment and supply below. Variable names are
generally prefixed with the name of the app to which they pertain.

Subsequently, edit `urls.py` and uncomment any paths associated with 
installed applications.

Finally, replace or fill in `apps/xgds_site_app` with site-specific content.

# Managing a site installation

## Bootstrap

A site must be bootstrapped once per installation:

```bash
./manage.py bootstrap
```

You may see errors after bootstrapping completes due to the incomplete 
configuration of the environment.

This will create local files `settings.py` and `sourceme.sh`.
These are ignored from `.gitignore` as they will contain information
specific to the installation which should not be committed back to 
the repository.

## Create Database

The installation will need a database. For example, to create a 
mysql database:

```bash
mysql -u root -p -e "create database xgds_site"
```

## Configure

At minimum, `settings.py` must be edited with database information.
For example:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.mysql',
        'NAME': 'xgds_site',
        'USER': 'root',
        'PASSWORD': '****',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```


## Source sourceme.sh

Whenever managing this installation, ensure you have the correct 
environment variables:

```bash
source sourceme.sh
```

## Create Administrator

After bootstrapping, an administrator account should be created
(after applying migrations to ensure tables are up-to-date):

```bash
./manage.py migrate
./manage.py createsuperuser
```

## Install Front-end Dependencies

After installation and whenever front-end dependencies are updated:

```bash
./manage.py prepnpm
```

## Prepare

Whenever static files (including front-end dependencies) change:

```bash
./manage.py prep
```

## Configure Apache

When using Apache to serve static files and interface with WSGI,
create a configuration `/etc/apache2/sites-available/xgds_site.conf`
and enable it:

```bash
sudo a2ensite xgds_site
sudo service apache2 reload
```

## Restart Apache

When using Apache to serve static files, restart after each prep:

```bash
sudo apachectl restart
```

## Access Site

With all of the above complete, you should now be able to navigate to
your installation in a browser (at https://localhost, for a local 
installation), log in using the administrator account you created, 
and see xGDS as you configured it.
