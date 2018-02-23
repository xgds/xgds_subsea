# Initializing a repository for a new site

For purposes of example, `xgds_site` will be used in place of the site-specific
application name (e.g. `xgds_rp` or `xgds_basalt`).

To initialize a new site-specific repository `xgds_site`:

```bash
git clone https://github.com/xgds/xgds_baseline.git xgds_site
cd xgds_site
./init.sh
```

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

This will create local files `settings.py` and `sourceme.sh`.
These are ignored from `.gitignore` as they will contain information
specific to the installation which should not be committed back to 
the repository.

## Configure

At minimum, `settings.py` must be edited with database information.
The database will also need to be created.

## Source sourceme.sh

Whenever managing this installation, ensure you have the correct 
environment variables:

```bash
source sourceme.sh
```

## Create Administrator

After bootstrapping, an administrator account should be created:

```bash
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

## Restart Apache

When using Apache to serve static files, restart after each prep:

```bash
sudo apachectl restart
```
