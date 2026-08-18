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
2. Tell the agent to process the Dropbox upload (`dropbox pull --run`).
3. Open the printed link (or `/spotify-mix-videos/renders/<video-id>/`) and
   save the final to your camera roll.

Imported uploads move to `/spotify-mix-videos/imported/` inside Dropbox —
never deleted — so nothing imports twice.

## Hook bank folder (optional but recommended)

For the ten Higgsfield hooks, create:

`/spotify-mix-videos/hooks/incoming/`

Drop the ten clips there. Tell the agent to pull and analyse them; it will
rename to stable stems (`hook-01-…`) and draft hook profiles under
`production/config/hook-profiles/` for your approval. (Until that folder
convention is automated, you can also drop them in `incoming/` as a batch and
say they are hooks-only.)
