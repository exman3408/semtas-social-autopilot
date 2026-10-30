"""Schedule manually curated Nov 2-6 content at 12:30 Istanbul, only where image and approval are final."""
from datetime import datetime, time, date, timezone
from zoneinfo import ZoneInfo
import os, json
from .__main__ import POSTS, media_accessible, save_json
from .buffer_api import BufferAPI, BufferError

WEEK_START="2026-11-02"
APPROVED_MEDIA={
    "2026-11-02":"approved-web.png",
    "2026-11-03":"approved-ads.png",
    "2026-11-05":"approved-shopify.png",
    # Nov 4/6 intentionally absent until real replacement images are in GitHub.
}

def main():
    if os.getenv("WEEK_QUEUE_AUTHORIZATION")!="OWNER_REQUEST_2026_10_30":
        raise RuntimeError("Owner's explicit one-time queue authorization missing")
    org=os.getenv("BUFFER_ORG_ID","").strip()
    base=os.getenv("MEDIA_BASE_URL","").rstrip("/")
    if not org or not base.startswith("https://"):raise RuntimeError("Buffer org/media settings missing")
    api=BufferAPI()
    channels={c["id"]:c for c in api.channels(org)}
    for day,expected_media in APPROVED_MEDIA.items():
        path=POSTS/(day+".json")
        post=json.loads(path.read_text(encoding="utf-8"))
        if post.get("manual_week")!=WEEK_START or post.get("media_file")!=expected_media:
            raise RuntimeError(day+": media/weekly plan mismatch; abort")
        review=post.get("review") or {}
        if review.get("status")!="approved" or review.get("approved_by")!="exman3408":
            print("[week queue] not approved: ",day);continue
        target=datetime.combine(date.fromisoformat(day),time(12,30),ZoneInfo("Europe/Istanbul")).astimezone(timezone.utc).isoformat().replace("+00:00","Z")
        for platform,item in post["channels"].items():
            if item.get("state") in ("queued","published") or item.get("buffer_post_id"):continue
            cid=os.getenv("BUFFER_"+platform.upper()+"_CHANNEL_ID","").strip()
            ch=channels.get(cid)
            if not ch or ch.get("service")!=platform or "semtas" not in ch.get("name","").lower().replace("ş","s"):
                print("[week queue] channel not verified:",platform);continue
            if ch.get("isDisconnected") or ch.get("isQueuePaused") or ch.get("isLocked"):
                print("[week queue] channel unavailable:",platform);continue
            url=base+"/"+expected_media
            if not media_accessible(url):raise RuntimeError("Public image unavailable: "+url)
            duplicate=api.exists_matching_post(org,cid,item["caption"])
            result={"id":duplicate,"dueAt":target} if duplicate else api.queue_image(cid,item["caption"],url,due_at=target)
            item.update({"state":"queued","buffer_post_id":result["id"],
                         "due_at":result.get("dueAt"),"approved_queue_source":"manual-week-2026-11-02"})
            save_json(path,post)
            print("[week queue]",day,platform,"Buffer ID",result["id"],"scheduled",result.get("dueAt"))
    print("[week queue] Nov 4 and Nov 6 blocked pending real artwork transfer; cannot send old images.")

if __name__=="__main__":main()
