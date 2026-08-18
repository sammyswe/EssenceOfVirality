/**
 * Tiny relay: Dropbox webhook → Cursor Automation webhook.
 *
 * Dropbox cannot send Cursor's required Authorization header, so this Worker
 * sits in the middle. Deploy with Wrangler; set secrets (never commit them):
 *   CURSOR_WEBHOOK_URL  - automation webhook URL from cursor.com/automations
 *   CURSOR_API_KEY      - crsr_… API key from the same automation
 *   DROPBOX_APP_SECRET  - Dropbox app secret (signature check)
 *
 * See docs/guides/dropbox-wake-agent.md
 */

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // Dropbox verification: echo the challenge query param as plain text.
    if (request.method === "GET") {
      const challenge = url.searchParams.get("challenge");
      if (challenge) {
        return new Response(challenge, {
          status: 200,
          headers: { "Content-Type": "text/plain", "X-Content-Type-Options": "nosniff" },
        });
      }
      return new Response("dropbox-cursor-relay ok", { status: 200 });
    }

    if (request.method !== "POST") {
      return new Response("method not allowed", { status: 405 });
    }

    const body = await request.text();
    const signature = request.headers.get("X-Dropbox-Signature") || "";
    if (!(await validDropboxSignature(body, signature, env.DROPBOX_APP_SECRET))) {
      return new Response("bad signature", { status: 403 });
    }

    // Acknowledge Dropbox quickly, then wake Cursor.
    const wake = fetch(env.CURSOR_WEBHOOK_URL, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${env.CURSOR_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        source: "dropbox",
        received_at: new Date().toISOString(),
        note: "File change notified — agent should run: ./process-job dropbox pull --run",
      }),
    });

    // Don't make Dropbox wait on Cursor; fire-and-forget with a short race.
    try {
      await Promise.race([
        wake,
        new Promise((resolve) => setTimeout(resolve, 2000)),
      ]);
    } catch (_) {
      // Cursor may still receive the request; Dropbox only needs 2xx from us.
    }

    return new Response("ok", { status: 200 });
  },
};

async function validDropboxSignature(body, signature, secret) {
  if (!secret || !signature) return false;
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const mac = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(body));
  const hex = [...new Uint8Array(mac)].map((b) => b.toString(16).padStart(2, "0")).join("");
  return timingSafeEqual(hex, signature.toLowerCase());
}

function timingSafeEqual(a, b) {
  if (a.length !== b.length) return false;
  let out = 0;
  for (let i = 0; i < a.length; i++) out |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return out === 0;
}
