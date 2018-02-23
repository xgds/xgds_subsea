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

# Initializing an installed site

```bash
./manage.py prepnpm
./manage.py prep
```
