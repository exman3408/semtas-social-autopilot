"""Automatic re-render + new mobile approval issue for each /revize instruction."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from .creative import ArtworkError, create_artwork
from .review import POSTS, ROOT, identity, github, issue_body, save

MEDIA=ROOT/"docs"/"media"

def _pending_revisions():
    for path in sorted(POSTS.glob("*.json")):
        data=json.loads(path.read_text(encoding="utf-8"))
        if data.get("review",{}).get("status")=="revision_requested":
            yield path,data

def render_pending():
    count=0
    for path,post in _pending_revisions():
        if any(v.get("state") in ("queued","published") or v.get("buffer_post_id")
               for v in post.get("channels",{}).values()):
            raise RuntimeError("Buffer'a alinmis gonderi otomatik revize edilemez")
        review=post["review"]
        count_ver=int(review.get("version",1))+1
        date=post["date"]
        name=f"semtas-{date}-r{count_ver}.png"
        dest=MEDIA/name
        note=review.get("revision_note","Daha kaliteli, premium, konuya ozel tasarim")
        layout="square" if list(post.get("channels",{}))==["linkedin"] else "portrait"
        # Never overwrite existing artwork, especially something manually revised.
        if dest.exists():
            raise RuntimeError("Revize gorseli zaten mevcut: "+name)
        backend=create_artwork(dest,post["headline"],post.get("subheadline",""),
                               post.get("category","SEMTAŞ"),layout,note)
        if not dest.is_file() or dest.stat().st_size<10_000:
            raise RuntimeError("Gorsel dogrulama basarisiz")
        old_issue=review.get("issue_number")
        post["media_file"]=name
        post["art_type"]=backend
        review["previous_issue_number"]=old_issue
        review["issue_number"]=None
        review["status"]="revision_rendered"
        review["version"]=count_ver
        review["rendered_at"]=datetime.now(timezone.utc).isoformat()
        review["render_engine"]=backend
        review.pop("approved_at",None)
        review.pop("approved_by",None)
        review["reviewed_revision_note"]=note
        for entry in review.get("revision_requests",[]):
            if entry.get("status")=="awaiting_redesign":entry["status"]="rendered"
        save(path,post)
        print("[revise] Yeni tasarim:",dest.name,"motor:",backend)
        count+=1
    print("[revise] Render tamam:",count)

def request_approval():
    repo,token=identity()
    base=os.getenv("MEDIA_BASE_URL","").strip().rstrip("/")
    if not base.startswith("https://"):
        raise RuntimeError("MEDIA_BASE_URL HTTPS gerekli")
    count=0
    for path in sorted(POSTS.glob("*.json")):
        post=json.loads(path.read_text(encoding="utf-8"))
        review=post.get("review") or {}
        if review.get("status")!="revision_rendered":
            continue
        if not (MEDIA/post["media_file"]).is_file():
            raise RuntimeError("Yayinlanacak yeni gorsel dosyasi eksik")
        name=f"[YENİ ONAY • V{review['version']}] {post['date']} | {post['headline']}"
        body=issue_body(post,base)+"\n\n---\n**Revize talebi:** "+review.get("reviewed_revision_note","")
        response=github("POST","/repos/"+repo+"/issues",token,{
            "title":name,"body":body,"assignees":[repo.split("/")[0]]
        })
        number=response.get("number")
        if not number:raise RuntimeError("Yeni Issue olusturulamadi")
        review["issue_number"]=number
        review["status"]="pending"
        review["requested_at"]=datetime.now(timezone.utc).isoformat()
        save(path,post)
        old=review.get("previous_issue_number")
        if isinstance(old,int) and old!=number:
            try:
                github("POST","/repos/"+repo+"/issues/"+str(old)+"/comments",token,{
                    "body":"Yeni revizyonun onay kaydi: "+response.get("html_url","")+
                           "\n\nOnceki surumdeki /onayla gecersizdir."
                })
                github("PATCH","/repos/"+repo+"/issues/"+str(old),token,{"state":"closed"})
            except RuntimeError as ex:
                print("[revise] Eski Issue kapatilamadi, eski onay yine de gecersiz:",str(ex)[:120])
        print("[revise] Yeni mobil onay:",response.get("html_url",""))
        count+=1
    print("[revise] Yeni onay istegi:",count)

def main():
    import sys
    mode=sys.argv[1] if len(sys.argv)>1 else ""
    if mode=="render":render_pending()
    elif mode=="request":request_approval()
    else:raise RuntimeError("Kullanim: python -m socialbot.revise render|request")

if __name__=="__main__":
    main()
