"""Manual, zero-API-cost, one-week Semtas editorial pack.
Reads content/weeks/YYYY-MM-DD.json; three approved image assets plus two licensed photo-based compositions.
Does not publish or use paid AI models. Each post still requires owner mobile approval.
"""
from __future__ import annotations
from datetime import date, datetime, timezone
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from .review import ROOT, github, identity, issue_body, save
import json, os, sys, requests, time

ASSETS=ROOT/"assets"
MEDIA=ROOT/"docs"/"media"
POSTS=ROOT/"content"/"posts"
WEEKS=ROOT/"content"/"weeks"
SIZE=(1080,1350)

def font(size,bold=False):
    files=[
       "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
       "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for name in files:
        if Path(name).exists():return ImageFont.truetype(name,size)
    return ImageFont.load_default()

def wrapped(draw,text,face,maxwidth):
    lines=[];current=""
    for word in text.split():
        test=(current+" "+word).strip()
        if current and draw.textbbox((0,0),test,font=face)[2]>maxwidth:
            lines.append(current);current=word
        else:current=test
    if current:lines.append(current)
    return lines

def render_editorial(day,dest):
    # Licensed project artwork already in repository; genuine photographic/3D material,
    # never the old geometric browser-wireframe generator.
    strategy=day["date"].endswith("-06")
    src=ASSETS/"approved"/("ads.png" if strategy else "web.png")
    if not src.is_file():raise RuntimeError("Premium artwork source missing: "+str(src))
    base=Image.open(src).convert("RGB")
    crop=(765,120,1099,850) if strategy else (765,585,1099,1100)
    subject=base.crop(crop)
    scale=max(1080/subject.width,960/subject.height)
    subject=subject.resize((int(subject.width*scale)+1,int(subject.height*scale)+1),Image.Resampling.LANCZOS)
    ox=(subject.width-1080)//2;oy=(subject.height-960)//2
    subject=subject.crop((ox,oy,ox+1080,oy+960))
    image=Image.new("RGBA",SIZE,(4,12,25,255))
    image.paste(subject,(0,390))
    shadow=Image.new("RGBA",SIZE,(0,0,0,0));d=ImageDraw.Draw(shadow)
    for x in range(1080):
        alpha=240 if x<430 else max(0,int(240*(750-x)/320))
        if alpha:d.line((x,390,x,1350),fill=(4,10,22,alpha))
    for y in range(1350):
        if y<300:alpha=236
        elif y<790:alpha=max(8,int(236-(y-300)*.46))
        elif y<1050:alpha=30
        else:alpha=min(192,int((y-1050)*.64))
        d.line((0,y,1080,y),fill=(4,10,22,alpha))
    image=Image.alpha_composite(image,shadow)
    layer=Image.new("RGBA",SIZE,(0,0,0,0))
    logo=Image.open(ASSETS/"brand"/"semtas-logo-beyaz.png").convert("RGBA")
    logo.thumbnail((390,145),Image.Resampling.LANCZOS)
    layer.alpha_composite(logo,(72,52))
    d=ImageDraw.Draw(layer)
    accent=(255,181,92) if strategy else (99,195,254)
    d.line((72,214,1008,214),fill=(*accent,150),width=2)
    d.text((72,240),day["category"],font=font(23,True),fill=(*accent,255))
    d.text((944,240),"05/05" if strategy else "03/05",font=font(22),fill=(229,232,242,200))
    head=("Büyüme tek bir","kanaldan gelmez.") if strategy else ("Google sizi","keşfedebiliyor mu?")
    d.text((69,317),head[0],font=font(72,True),fill=(255,255,255,255))
    d.text((69,405),head[1],font=font(68,True),fill=(*accent,255))
    small=font(28)
    y=511
    for line in wrapped(d,day["subheadline"],small,900):
        d.text((74,y),line,font=small,fill=(242,246,250,255));y+=41
    d.rounded_rectangle((72,1164,532,1242),radius=35,fill=(*accent,240))
    d.text((103,1182),"PROJENİ KONUŞALIM",font=font(24,True),fill=(8,17,28,255))
    d.text((474,1181),"→",font=font(29,True),fill=(8,17,28,255))
    d.text((74,1280),"semtasdijital.com  /  STRATEJİ  ·  TASARIM  ·  PERFORMANS",font=font(18),fill=(230,239,250,215))
    image=Image.alpha_composite(image,layer).convert("RGB")
    dest.parent.mkdir(parents=True,exist_ok=True)
    image.save(dest,"PNG",optimize=True)
    if dest.stat().st_size<20000:raise RuntimeError("Artwork suspiciously small")

def get_pack(week):
    if not week or len(week)!=10 or week[4]!="-":
        raise RuntimeError("Week must be YYYY-MM-DD")
    path=WEEKS/(week+".json")
    if not path.is_file():raise RuntimeError("Week not found: "+week)
    pack=json.loads(path.read_text(encoding="utf-8"))
    if len(pack.get("posts",[]))!=5:raise RuntimeError("Expected five posts")
    return pack

def prepare(week):
    pack=get_pack(week)
    for day in pack["posts"]:
        d=date.fromisoformat(day["date"])
        if d.weekday()>4:raise RuntimeError("Weekend entry prohibited")
        media_name=day["media_file"]
        if "/" in media_name or "\\" in media_name:raise RuntimeError("Unexpected image path")
        media=MEDIA/media_name
        if media_name not in ("approved-web.png","approved-ads.png","approved-shopify.png") and not media.is_file():
            render_editorial(day,media)
        if not media.is_file():raise RuntimeError("Required premium image missing: "+media_name)
        path=POSTS/(day["date"]+".json")
        if path.is_file():
            print("[manual-week] existing post; preserving owner's edits:",path.name)
            continue
        record={
          "date":day["date"],"category":day["category"],"seed":day["headline"],
          "headline":day["headline"],"subheadline":day["subheadline"],
          "art_type":"editorial-premium-manual","manual_week":week,
          "media_file":media_name,
          "channels":{name:{"caption":day[name],"state":"pending","buffer_post_id":None}
                      for name in day["channels"]},
          "review":{"status":"awaiting_issue"}
        }
        save(path,record)
        print("[manual-week] staged",path.name,media_name)
    print("[manual-week] READY: five posts, no Buffer API used")

def notify(week):
    pack=get_pack(week)
    repo,token=identity()
    media_base=os.getenv("MEDIA_BASE_URL","").rstrip("/")
    if not media_base.startswith("https://"):
        raise RuntimeError("MEDIA_BASE_URL HTTPS required")
    for day in pack["posts"]:
        path=POSTS/(day["date"]+".json")
        record=json.loads(path.read_text(encoding="utf-8"))
        review=record.get("review") or {}
        if review.get("issue_number"):
            print("[manual-week] existing Issue",review["issue_number"])
            continue
        if review.get("status")!="awaiting_issue":
            print("[manual-week] review state changed, skipping:",path.name)
            continue
        media_url=media_base+"/"+record["media_file"]
        # User approval must not be requested against an inaccessible image.
        r=requests.get(media_url,timeout=22,stream=True)
        good=r.status_code==200 and r.headers.get("content-type","").lower().startswith("image/")
        r.close()
        if not good:raise RuntimeError("Image URL not live: "+media_url)
        title="[HAFTALIK ONAY] "+record["date"]+" | "+record["headline"]
        body=issue_body(record,media_base)+"\n\n**Planlanan gün:** "+record["date"]+"\n**Yayın:** Yalnızca /onayla sonrasında; hesap ve Buffer sırası uygunsa."
        result=github("POST","/repos/"+repo+"/issues",token,{
            "title":title,"body":body,"assignees":[repo.split("/")[0]]
        })
        review.update(status="pending",issue_number=result["number"],
                      requested_at=datetime.now(timezone.utc).isoformat())
        record["review"]=review
        save(path,record)
        print("[manual-week] OWNER REVIEW:",result.get("html_url",""))
    print("[manual-week] Requests ready; no posts published")

def main():
    if len(sys.argv)!=3 or sys.argv[1] not in ("prepare","notify"):
        raise RuntimeError("Usage: python -m socialbot.manual_week prepare|notify YYYY-MM-DD")
    {"prepare":prepare,"notify":notify}[sys.argv[1]](sys.argv[2])

if __name__=="__main__":main()
