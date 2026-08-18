# Dropbox setup (one-time)

The phone loop uses Dropbox as a file channel: you upload mixes (and hook
clips) from the Dropbox app; the agent pulls them, renders, and pushes the
finished video back with a share link. There is no Dropbox MCP in this
environment — credentials go in Cursor cloud agent secrets.

## 1. Create a Dropbox app

1. Open the [Dropbox App Console](https://www.dropbox.com/developers/apps).
2. Create an app with **scoped access**.
3. Permission type: **Full Dropbox** (or App folder if you prefer a sandboxed
   root — then set `DROPBOX_BASE_FOLDER` to that app folder path).
4. Under Permissions, enable at least:
   - `files.content.read`
   - `files.content.write`
   - `sharing.write`
   - `account_info.read`
5. Submit the permission changes if the console asks you to.

## 2. Get a refresh token (once)

Dropbox access tokens expire; a refresh token does not. From a machine with
curl (or use Dropbox's OAuth guide):

1. Note the app **App key** and **App secret**.
2. In a browser, open (replace `APP_KEY`):

```
https://www.dropbox.com/oauth2/authorize?client_id=APP_KEY&response_type=code&token_access_type=offline
```

3. Approve access; copy the `code` from the redirect URL.
4. Exchange it:

```bash
curl https://api.dropboxapi.com/oauth2/token \
  -d code=THE_CODE \
  -d grant_type=authorization_code \
  -d client_id=APP_KEY \
  -d client_secret=APP_SECRET
```

5. Save the `refresh_token` from the JSON response. You will not see it again
   easily — treat it like a password.

## 3. Put secrets in Cursor

Cursor Dashboard → **Cloud Agents** → **Secrets** (for this environment), add:

| Name | Value |
| --- | --- |
| `DROPBOX_APP_KEY` | app key |
| `DROPBOX_APP_SECRET` | app secret |
| `DROPBOX_REFRESH_TOKEN` | refresh token from step 2 |
| `DROPBOX_BASE_FOLDER` | optional; default `/spotify-mix-videos` |

Do not commit these anywhere. Start a **new** cloud agent run after saving so
the secrets are injected.

## 4. Verify

In the agent conversation:

```text
Run ./process-job dropbox status
```

You should see your Dropbox account name and the `incoming` / `renders`
paths. First `dropbox pull` creates the folders if they are missing.

## 5. Daily use

1. In the Dropbox app, put a Spotify recording in
   `/spotify-mix-videos/incoming/` — or a **subfolder** with the recording +
   the Higgsfield hook clip together (name the capture with `spotify` /
   `mix` / `screen-recording` in the filename so the agent picks it correctly).
2. Tell the agent to process it. It runs `./process-job dropbox pull --run`,
   which imports each upload into a job folder, processes it, and uploads the
   preview, final and thumbnail to `/spotify-mix-videos/renders/<video-id>/`
   with shared links printed for each file.
3. Open the link (or the folder in the Dropbox app) and save the final to the
   camera roll for posting.

For unattended / always-checking behaviour, see
[`always-on-dropbox.md`](always-on-dropbox.md). For pasting hook/retention
tutorial videos, see [`education-hooks.md`](education-hooks.md).

## Hook bank folder

`/spotify-mix-videos/hooks/library/` holds renamed Higgsfield hooks.
`hooks/incoming/` is for new clips to analyse.
