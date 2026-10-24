#!/usr/bin/env python3
"""Instagram API (Instagram Login) helper for the explainer reels.

Commands
  check                          verify the token and print the account
  publish SPEC VIDEO_URL         publish a reel; writes media id + permalink back into SPEC
  insights                       pull metrics for every posted reel into data/insights.json
  refresh                        refresh the long-lived token; prints the new token to stdout

Env: IG_ACCESS_TOKEN (required), IG_USER_ID (optional, looked up if missing),
     IG_API_VERSION (default v24.0)
"""
import json, os, sys, time, glob, datetime, urllib.request, urllib.parse, urllib.error

VER = os.environ.get("IG_API_VERSION", "v24.0")
BASE = f"https://graph.instagram.com/{VER}"
TOKEN = os.environ.get("IG_ACCESS_TOKEN", "")

def call(method, path, **params):
    params["access_token"] = TOKEN
    url = path if path.startswith("http") else f"{BASE}/{path}"
    data = None
    if method == "GET":
        url += "?" + urllib.parse.urlencode(params)
    else:
        data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url, data=data, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        raise SystemExit(f"Instagram API error {e.code} on {path}: {body}")

def user_id():
    return os.environ.get("IG_USER_ID") or call("GET", "me", fields="user_id")["user_id"]

def cmd_check():
    me = call("GET", "me", fields="user_id,username,account_type,media_count")
    print(json.dumps(me, indent=2))
    lim = call("GET", f"{me['user_id']}/content_publishing_limit", fields="quota_usage,config")
    print("publishing quota:", json.dumps(lim))

def cmd_publish(spec_path, video_url):
    spec = json.load(open(spec_path))
    uid = user_id()
    c = call("POST", f"{uid}/media", media_type="REELS", video_url=video_url,
             caption=spec.get("caption", ""), share_to_feed="true",
             thumb_offset=str(int(spec.get("cover_at", 2.0) * 1000)))
    cid = c["id"]
    print("container", cid)
    for _ in range(60):  # up to ~10 minutes
        st = call("GET", cid, fields="status_code,status")
        if st.get("status_code") == "FINISHED":
            break
        if st.get("status_code") in ("ERROR", "EXPIRED"):
            raise SystemExit(f"container failed: {st}")
        time.sleep(10)
    else:
        raise SystemExit("container did not finish processing in time")
    m = call("POST", f"{uid}/media_publish", creation_id=cid)
    mid = m["id"]
    info = call("GET", mid, fields="permalink,timestamp")
    spec["posted"] = {"media_id": mid, "permalink": info.get("permalink"), "timestamp": info.get("timestamp"),
                      "video_url": video_url}
    json.dump(spec, open(spec_path, "w"), indent=1, ensure_ascii=False)
    print("published", mid, info.get("permalink"))

# Reel metrics. Names change over API versions, so each is requested separately and failures are skipped.
METRICS = ["views", "reach", "likes", "comments", "shares", "saved", "total_interactions",
           "ig_reels_avg_watch_time", "ig_reels_video_view_total_time"]

def link_manual_posts():
    """Specs posted by hand have "posted": {"manual": true} and no media_id. Match each to the
    earliest unclaimed reel on the account published on/after the spec's date, and record it."""
    specs = []
    claimed = set()
    for sp in sorted(glob.glob("reels/posted/*.json")):
        s = json.load(open(sp))
        mid = (s.get("posted") or {}).get("media_id")
        if mid:
            claimed.add(mid)
        elif (s.get("posted") or {}).get("manual"):
            specs.append((sp, s))
    if not specs:
        return
    media = call("GET", f"{user_id()}/media", fields="id,media_type,media_product_type,permalink,timestamp",
                 limit=50).get("data", [])
    reels = sorted([m for m in media if m.get("media_product_type") == "REELS" or m.get("media_type") == "VIDEO"],
                   key=lambda m: m["timestamp"])
    for sp, s in specs:
        day = s["id"][:10]
        for m in reels:
            if m["id"] in claimed or m["timestamp"][:10] < day:
                continue
            s["posted"].update({"media_id": m["id"], "permalink": m.get("permalink"), "timestamp": m["timestamp"]})
            claimed.add(m["id"])
            json.dump(s, open(sp, "w"), indent=1, ensure_ascii=False)
            print("linked manual post", s["id"], "->", m.get("permalink"))
            break
        else:
            print("no matching reel yet for manual post", s["id"])

def cmd_insights():
    os.makedirs("data", exist_ok=True)
    path = "data/insights.json"
    db = json.load(open(path)) if os.path.exists(path) else {}
    now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="minutes")
    link_manual_posts()
    for sp in sorted(glob.glob("reels/posted/*.json")):
        spec = json.load(open(sp))
        mid = (spec.get("posted") or {}).get("media_id")
        if not mid:
            continue
        snap = {"fetched": now}
        for m in METRICS:
            try:
                r = call("GET", f"{mid}/insights", metric=m)
                snap[m] = r["data"][0]["values"][0]["value"] if r.get("data") else None
            except SystemExit as e:
                snap.setdefault("_errors", []).append(f"{m}: {str(e)[:160]}")
        rec = db.setdefault(spec["id"], {"topic": spec.get("topic"), "hook_type": spec.get("hook_type"),
                                         "hook": spec.get("hook"), "subject": spec.get("subject"), "duration": spec.get("duration"),
                                         "posted": spec["posted"].get("timestamp"),
                                         "permalink": spec["posted"].get("permalink"), "snapshots": []})
        rec["snapshots"].append(snap)
        rec["latest"] = {k: v for k, v in snap.items() if not k.startswith("_")}
        print(spec["id"], rec["latest"])
    # account-level follower count, if available
    rec = {"fetched": now}
    try:
        tok = call("GET", "me", fields="user_id,username")
        rec.update(token_user_id=tok.get("user_id"), username=tok.get("username"))
        rec["ig_user_id_secret_matches"] = (not os.environ.get("IG_USER_ID")) or os.environ["IG_USER_ID"] == tok.get("user_id")
    except SystemExit as e:
        rec["token_error"] = str(e)[:300]
    try:
        rec.update(call("GET", user_id(), fields="followers_count,media_count"))
    except SystemExit as e:
        rec["account_error"] = str(e)[:300]
    db.setdefault("_account", []).append(rec)
    json.dump(db, open(path, "w"), indent=1, ensure_ascii=False)

def cmd_refresh():
    r = call("GET", "https://graph.instagram.com/refresh_access_token", grant_type="ig_refresh_token")
    print(r["access_token"])

if __name__ == "__main__":
    if not TOKEN:
        raise SystemExit("IG_ACCESS_TOKEN is not set")
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    {"check": cmd_check, "publish": lambda: cmd_publish(sys.argv[2], sys.argv[3]),
     "insights": cmd_insights, "refresh": cmd_refresh}[cmd]()
