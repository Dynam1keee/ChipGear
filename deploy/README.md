# Deployment

The site runs on an Oracle Cloud VM (Ubuntu 22.04): Nginx on port 80 serves the React app, static and media files and passes `/api/` and `/admin/` to Gunicorn (`chipgear.service`, 127.0.0.1:8000).

GitHub Actions deploys it: `.github/workflows/deploy.yml`. It runs after every push to `main` (only if the tests pass) or by hand (Actions → Deploy → Run workflow).

What a deploy does:

1. Runs the CI checks (backend tests and the frontend build).
2. Builds the frontend and uploads it with `rsync` over SSH.
3. Uploads the Django code and the product photos.
4. On the server: `pip install`, `migrate`, `collectstatic`, restart the service.
5. Checks that `/api/categories/` and the home page answer.

The server database `db.sqlite3` is **never** overwritten by a normal deploy, because real orders and users live there. The only way to replace it is the checkbox *Replace the database* in the manual run. The old database is saved first as `db.backup-<date>.sqlite3` in the project folder.

## One-time server setup

Run on the server (`APP_DIR` is `/home/ubuntu/apps/ChipGear`).

**1. Folders for Nginx**

```bash
sudo mkdir -p /var/www/chipgear/{frontend,static,media}
sudo chown -R ubuntu:ubuntu /var/www/chipgear
```

**2. Folders in `.env`** (next to `manage.py`). Add these two lines, keep the others:

```env
DJANGO_STATIC_ROOT=/var/www/chipgear/static
DJANGO_MEDIA_ROOT=/var/www/chipgear/media
```

**3. Nginx.** Copy `deploy/nginx.conf` to `/etc/nginx/sites-available/chipgear` (replace the old site config), then:

```bash
sudo ln -sf /etc/nginx/sites-available/chipgear /etc/nginx/sites-enabled/chipgear
sudo nginx -t && sudo systemctl reload nginx
```

**4. Restart without a password.** The `ubuntu` user on Oracle images usually already has passwordless `sudo`. If not, run `sudo visudo -f /etc/sudoers.d/chipgear` and add:

```
ubuntu ALL=(root) NOPASSWD: /usr/bin/systemctl stop chipgear, /usr/bin/systemctl restart chipgear, /usr/bin/systemctl is-active chipgear
```

**5. Virtual environment.** The workflow uses `/home/ubuntu/apps/ChipGear/.venv/bin/python`. If your environment has another name, change `PYTHON` in `deploy.yml`.

**6. Deploy key.** On your computer:

```bash
ssh-keygen -t ed25519 -f chipgear_deploy -N "" -C github-actions
ssh-keyscan -t ed25519 <server-ip>      # output = DEPLOY_KNOWN_HOSTS
```

Add the content of `chipgear_deploy.pub` as a new line to `~/.ssh/authorized_keys` on the server. Do not commit the key files; delete them from your computer after the next step.

## GitHub secrets

Repository → Settings → Secrets and variables → Actions → New repository secret:

| Secret | Value |
| --- | --- |
| `DEPLOY_HOST` | server IP address |
| `DEPLOY_USER` | `ubuntu` |
| `DEPLOY_SSH_KEY` | the whole content of the private file `chipgear_deploy` |
| `DEPLOY_KNOWN_HOSTS` | the output of `ssh-keyscan` from above |

Port 22 must be open in the Oracle security list for GitHub's runners (it usually is open to `0.0.0.0/0`).

## First deploy

1. Run the workflow by hand on the branch you want to publish, with *Replace the database* checked. The old database is backed up on the server.
2. Open the site and check the home page, a product, login and the admin panel (`/admin/`). Create an administrator on the server with `manage.py createsuperuser`, because the repository database has no users.
3. After that, every push to `main` deploys by itself and keeps the server database.

## Rollback

- Code: push the previous commit to `main` again (or run the workflow on an older branch or tag).
- Database: stop the service, copy a `db.backup-*.sqlite3` file back to `db.sqlite3`, start the service.
- The first (server-rendered) version of the site is kept in the branch `legacy-django`.
