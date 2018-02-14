# Initializing a repository for a new site

For purposes of example, `xgds_app` will be used in place of the site-specific
application name (e.g. `xgds_rp` or `xgds_basalt`).

After creating the repository `xgds_app` in GitHub, initialize it locally:

```bash
git clone https://github.com/xgds/xgds_baseline.git xgds_app
cd xgds_app
./init.sh
```

The `./init.sh` script will detect your directory name and create a 
skeleton for site-specific content under `apps/xgds_app`. If you want 
to provide a name explicitly, run as `./init.sh xgds_some_name`.

Next, edit `siteSettings.py`. In particular, uncomment any `INSTALLED_APPS`
that will be needed for the new site. Many apps will also have related 
configuration variables to uncomment and supply below. Variable names are
generally prefixed with the name of the app to which they pertain. In 
some examples, `xgds_app` is used to stand-in name for a path or package 
expected to be provided by the site-specific application.

Subsequently, edit `urls.py` and uncomment any paths associated with 
installed applications. Examples are also present for including paths 
for the site-specific application, including the primary redirect, 
with `xgds_app` used again as a stand-in name.

Finally, replace or fill in `apps/xgds_app` with site-specific content.
