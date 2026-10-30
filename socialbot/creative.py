"""Semtas image engine. Default is zero-billing Pillow; Gemini Image is explicit paid opt-in only."""
from __future__ import annotations
from pathlib import Path
from io import BytesIO
import base64
import hashlib
import math
import os
import random
import requests
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
WHITE_LOGO = ROOT / "assets/brand/semtas-logo-beyaz.png"
REFERENCE_IMAGES = [
    ROOT / "assets/approved/web.png",
    ROOT / "assets/approved/ads.png",
    ROOT / "assets/approved/shopify.png",
]

class ArtworkError(RuntimeError):
    pass

STYLE_GUIDE = """You are the art director for SEMTAS DIJITAL, a premium Turkish digital agency.
Aim for the level of an award-winning boutique creative studio, not Canva templates.
Visual language: cinematic editorial advertising, luxury commercial art direction,
carefully controlled negative space, sophisticated dark navy / ultramarine / soft ice blue,
dimensional glass structures, tangible materials, ray-traced rim light, realistic reflections,
restrained fine-grain texture, dramatic but tasteful lighting, intentional asymmetry.
Design for Turkish business owners. Convey the actual business subject through a powerful
specific visual metaphor. It must feel like a bespoke high-end commercial key visual.
Avoid: cheap gradients, generic corporate clip-art, random numbers, dashboards with invented
results, fake company names, meaningless charts, watermark, fake logos and random lettering.
Only generate BACKGROUND ART: no logo, no sentences, no readable text. Brand's real
wordmark and exact Turkish copy will be composited separately for perfect accuracy.
Reserve top 25% and bottom 18% as dark, uncluttered readable space for our typography.
Image composition vertical 4:5. The 3 supplied references define Semtas creative quality,
contrast, camera treatment and sophisticated layout; do not copy their words or logos.
"""

def _font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for path in candidates:
        if Path(path).is_file():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def _fit_lines(draw, text, width, max_lines=4, max_size=75, min_size=42):
    for sz in range(max_size, min_size-1, -3):
        font = _font(sz, True)
        lines, current = [], ""
        for word in text.split():
            candidate = (current+" "+word).strip()
            if draw.textbbox((0,0), candidate, font=font)[2] <= width:
                current = candidate
            else:
                if current: lines.append(current)
                current=word
        if current: lines.append(current)
        if len(lines) <= max_lines and (len(lines)*int(sz*1.17)) <= 310:
            return font, lines, sz
    raise ArtworkError("Gorsel basligi cok uzun: " + text[:90])

def _brand_overlay(im, title, subtitle, category):
    """Exact provided brand logo and text overlay, after AI / free visual is finished."""
    w,h=im.size
    xscale=w/1080
    layer=Image.new("RGBA",(w,h),(0,0,0,0))
    d=ImageDraw.Draw(layer)
    # readable text-backed overlays; avoid illegible model-generated text
    bg=Image.new("RGBA",(w,h),(0,0,0,0))
    z=ImageDraw.Draw(bg)
    z.rectangle((0,0,w,int(h*.36)), fill=(5,12,26,150))
    z.rectangle((0,int(h*.855),w,h), fill=(5,12,26,170))
    bg=bg.filter(ImageFilter.GaussianBlur(max(8,int(16*xscale))))
    layer.alpha_composite(bg)
    logo=WHITE_LOGO
    if not logo.is_file():
        raise ArtworkError("Gercek Semtas logosu yok")
    lg=Image.open(logo).convert("RGBA")
    lg.thumbnail((int(390*xscale),int(118*xscale)),Image.Resampling.LANCZOS)
    layer.alpha_composite(lg,(int(68*xscale),int(53*xscale)))
    d=ImageDraw.Draw(layer)
    cy=int(216*xscale)
    f=_font(int(20*xscale),True)
    d.text((int(70*xscale),cy),category.upper(),font=f,fill=(130,209,254,255))
    f,lines,sz=_fit_lines(d,title,int(930*xscale),max_size=int(72*xscale),min_size=int(43*xscale))
    y=int(271*xscale)
    for j,line in enumerate(lines):
        d.text((int(66*xscale),y),line,font=f,fill=(249,251,255,255) if j<len(lines)-1 else (111,202,255,255))
        y += int(sz*1.17)
    d.line((int(70*xscale),int(h-169*xscale),int(w-70*xscale),int(h-169*xscale)),fill=(127,189,240,140),width=max(1,int(2*xscale)))
    small=_font(int(21*xscale))
    d.text((int(70*xscale),int(h-138*xscale)), "STRATEJİ  •  TASARIM  •  PERFORMANS",font=small,fill=(209,223,239,255))
    link=_font(int(30*xscale),True)
    d.text((int(70*xscale),int(h-101*xscale)), "semtasdijital.com",font=link,fill=(255,255,255,255))
    return Image.alpha_composite(im.convert("RGBA"),layer).convert("RGB")

def _render_free_canvas(category, note, size):
    """A dynamic conceptual visual. Does not claim to be image-model output."""
    w,h=size
    r=random.Random(int(hashlib.sha256((category+"|"+note).encode()).hexdigest()[:12],16))
    c=Image.new("RGB",size,(4,10,24))
    d=ImageDraw.Draw(c)
    # Midnight gradient
    for y in range(h):
        t=y/h
        d.line((0,y,w,y),fill=(int(5+9*t),int(13+13*t),int(27+32*t)))
    im=c.convert("RGBA")
    palette={
        "SEO":(89,177,255), "REKLAM YÖNETİMİ":(244,153,95),
        "E-TİCARET":(166,120,248),"WEB TASARIM":(98,206,249),
        "DİJİTAL STRATEJİ":(78,162,252)}
    a=palette.get(category,(104,172,254))
    accent=Image.new("RGBA",size)
    ad=ImageDraw.Draw(accent)
    for i in range(7):
        cx=int(w*(.45+r.uniform(-.15,.5)));cy=int(h*(.5+r.uniform(-.16,.12)))
        rad=int(200+r.uniform(25,200))
        ad.ellipse((cx-rad,cy-rad,cx+rad,cy+rad),fill=(*a,17+i*2))
    accent=accent.filter(ImageFilter.GaussianBlur(85))
    im=Image.alpha_composite(im,accent)
    v=Image.new("RGBA",size)
    draw=ImageDraw.Draw(v)
    # cinematic floor perspective and light trails
    for j in range(18):
        x=int(w*(j/17))
        draw.line([(w//2,int(h*.65)),(x,int(h*.83))],fill=(135,187,246,22),width=1)
    for j in range(9):
        y=int(h*(.67+j*.019))
        draw.line((0,y,w,y),fill=(135,187,246,18),width=1)
    # big structural glass UI as business metaphor
    cx=int(w*.53);cy=int(h*.59)
    tilt=18 if r.random()>.5 else -18
    panes=[
        (int(w*.24),int(h*.40),int(w*.79),int(h*.79)),
        (int(w*.13),int(h*.48),int(w*.60),int(h*.76)),
    ]
    for i,(x1,y1,x2,y2) in enumerate(panes):
        offset=i*28
        draw.rounded_rectangle((x1+offset+tilt,y1+offset,x2+offset+tilt,y2+offset),radius=33,
                               fill=(17,38,67,214),outline=(*a,125),width=3)
        draw.line((x1+offset+tilt+27,y1+offset+48,x2+offset+tilt-27,y1+offset+48),
                  fill=(*a,90),width=2)
        for k in range(3):
            draw.ellipse((x1+offset+tilt+29+k*18,y1+offset+22,
                          x1+offset+tilt+37+k*18,y1+offset+30),fill=(*a,155))
        # interface details, no deceptive numerical metrics
        for k in range(4):
            yy=y1+offset+85+k*53
            draw.rounded_rectangle((x1+offset+tilt+30,yy,x2+offset+tilt-44,yy+17),radius=8,
                                 fill=(*a,int(95/(k+1))))
            draw.rounded_rectangle((x1+offset+tilt+30,yy+25,x2+offset+tilt-144,yy+34),radius=4,
                                 fill=(203,228,255,45))
    # orbit represents connected channels; intentionally NOT a fake performance plot
    x0=int(w*.66);y0=int(h*.59)
    for k,alpha in enumerate([100,85,55]):
        rr=102+k*24
        draw.arc((x0-rr,y0-rr,x0+rr,y0+rr),18,318,fill=(*a,alpha),width=5-k)
    for k in range(4):
        theta=k*math.pi*.62+.3
        rad=138
        x=int(x0+rad*math.cos(theta));y=int(y0+rad*math.sin(theta))
        draw.ellipse((x-13,y-13,x+13,y+13),fill=(*a,220),outline=(255,255,255,210),width=2)
    im=Image.alpha_composite(im,v)
    return im.convert("RGB")

def _render_nano_banana(title,subtitle,category,revision_note,layout,size):
    if os.getenv("ALLOW_PAID_GEMINI_IMAGE_API","false").lower() != "true":
        raise ArtworkError("Nano Banana API ucretli; ALLOW_PAID_GEMINI_IMAGE_API=true olmadan cagri yok")
    key=os.getenv("GEMINI_API_KEY","").strip()
    if not key:raise ArtworkError("GEMINI_API_KEY eksik")
    model=os.getenv("GEMINI_IMAGE_MODEL","gemini-nano-banana-2.1").strip()
    allowed={"gemini-nano-banana-2.1","gemini-3-pro-image","gemini-3.1-flash-image","gemini-3.1-flash-lite-image"}
    if model not in allowed:raise ArtworkError("Desteklenmeyen gorsel model: "+model)
    prompt=STYLE_GUIDE+"\nTopic: "+category+". Headline's visual meaning: "+title+"\nSupporting context: "+subtitle+"\nUser revision: "+(revision_note or "original premium layout")
    inp=[{"type":"text","text":prompt}]
    for ref in REFERENCE_IMAGES:
        if ref.is_file():
            image=Image.open(ref).convert("RGB")
            image.thumbnail((720,900),Image.Resampling.LANCZOS)
            out=BytesIO();image.save(out,"JPEG",quality=75,optimize=True)
            inp.append({"type":"image","mime_type":"image/jpeg","data":base64.b64encode(out.getvalue()).decode("ascii")})
    aspect="1:1" if layout=="square" else "4:5"
    body={"model":model,"input":inp,"response_format":{"type":"image","aspect_ratio":aspect,"image_size":"2K"}}
    try:
        r=requests.post("https://generativelanguage.googleapis.com/v1beta/interactions",
                        headers={"x-goog-api-key":key,"Content-Type":"application/json"},json=body,timeout=165)
        if r.status_code in (402,403,429):
            raise ArtworkError("Gemini Image API kota/faturalandirma engeli: HTTP "+str(r.status_code))
        r.raise_for_status()
        data=r.json()
        block=data.get("output_image")
        if not block or not block.get("data"):
            # Some interaction responses interleave image outputs in steps.
            for step in data.get("steps",[]):
                for part in step.get("content",[]) or []:
                    if part.get("type")=="image" and part.get("data"):block=part
        if not block or not block.get("data"):raise ArtworkError("Gemini gorsel blok dondurmedi")
        raw=base64.b64decode(block["data"],validate=True)
        if len(raw)>25_000_000:raise ArtworkError("Gorsel yaniti beklenenden buyuk")
        im=Image.open(BytesIO(raw)).convert("RGB")
        return im.resize(size,Image.Resampling.LANCZOS)
    except requests.RequestException as exc:
        raise ArtworkError("Gemini Image API baglanti hatasi: "+type(exc).__name__) from exc

def create_artwork(path,headline,subheadline,category,layout="portrait",revision_note=""):
    """Produces unique versioned output. Never silently falls back from paid image errors."""
    backend=os.getenv("IMAGE_ENGINE","premium_pillow").strip().lower()
    size=(1200,1200) if layout=="square" else (1080,1350)
    if backend=="gemini":
        art=_render_nano_banana(headline,subheadline,category,revision_note,layout,size)
        label=os.getenv("GEMINI_IMAGE_MODEL","gemini-nano-banana-2.1")
    elif backend=="premium_pillow":
        art=_render_free_canvas(category,revision_note or headline,size)
        label="premium-pillow-free"
    else:
        raise ArtworkError("IMAGE_ENGINE premium_pillow veya gemini olmali")
    result=_brand_overlay(art,headline,subheadline,category)
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    result.save(path,"PNG",optimize=True)
    return label
