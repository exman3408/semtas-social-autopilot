"""Premium, deterministically generated 4:5 / square art using the *actual* uploaded brand logo.
Does not render unverified numbers, metrics or synthetic client logos.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from math import sin, cos, pi

ROOT = Path(__file__).resolve().parent.parent
LOGO = ROOT/'assets/brand/semtas-logo-beyaz.png'
FREG = [
  '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
  '/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf',
  'C:/Windows/Fonts/arial.ttf',
]
FBOLD = [
  '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
  '/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf',
  'C:/Windows/Fonts/arialbd.ttf',
]

def face(size,bold=False):
    for name in FBOLD if bold else FREG:
        if Path(name).exists(): return ImageFont.truetype(name,size)
    return ImageFont.load_default()

def wrap(draw,text,ft,available,max_lines=4):
    ls=[];current=''
    for word in text.split():
        candidate=(current+' '+word).strip()
        if draw.textbbox((0,0),candidate,font=ft)[2] <= available:
            current=candidate
        else:
            if current:ls.append(current)
            current=word
    if current:ls.append(current)
    return ls if len(ls)<=max_lines else None

def alpha_color(hex_code, alpha=255):
    h=hex_code.lstrip('#');return tuple(int(h[i:i+2],16) for i in (0,2,4))+(alpha,)

def render_png(output_path,title,subtitle,category,layout='portrait'):
    W,H=(1080,1350) if layout=='portrait' else (1200,1200)
    # Header and content areas must remain legible on mobile.
    tint = '#3a9dff' if category in ('WEB TASARIM','SEO','DİJİTAL STRATEJİ') else ('#fa8136' if category=='REKLAM YÖNETİMİ' else '#b480ff')
    import math
    im=Image.new('RGB',(W,H));px=im.load()
    for y in range(H):
        for x in range(W):
            nx=x/W; ny=y/H
            light=max(0,1-(abs(nx-.79)*1.3+abs(ny-.58)*.9))
            px[x,y]=(int(6+12*light+ny*5),int(12+22*light+ny*7),int(24+45*light+ny*10))
    im=im.convert('RGBA')
    fx=Image.new('RGBA',(W,H),(0,0,0,0));f=ImageDraw.Draw(fx)
    rgb=alpha_color(tint)[:3]
    f.ellipse((W-600,265,W+150,1060),fill=(*rgb,55))
    f.ellipse((W-340,460,W+200,1020),fill=(*rgb,55))
    fx=fx.filter(ImageFilter.GaussianBlur(95));im=Image.alpha_composite(im,fx)
    layer=Image.new('RGBA',(W,H),(0,0,0,0));d=ImageDraw.Draw(layer)
    for x in range(52,W,66):
        d.line((x,218,x,H-132),fill=(123,165,215,11),width=1)
    for y in range(218,H-130,66):
        d.line((52,y,W-52,y),fill=(123,165,215,11),width=1)
    # actual original white logo, aspect ratio retained
    if not LOGO.exists():raise FileNotFoundError(f'Gerçek logo eksik: {LOGO}')
    lg=Image.open(LOGO).convert('RGBA');lg.thumbnail((430,132),Image.Resampling.LANCZOS)
    layer.alpha_composite(lg,(66,55))
    d.rounded_rectangle((W-320,85,W-62,134),radius=24,outline=(*rgb,138),fill=(8,20,38,205),width=2)
    d.text((W-295,99),'SEMTAŞ INSIGHTS',font=face(19,True),fill=(208,225,245))
    # category eyebrow
    category=category.upper()
    d.rounded_rectangle((66,210,min(W-80,120+len(category)*19),267),radius=28,fill=(*rgb,36),outline=(*rgb,180),width=2)
    d.text((87,226),category,font=face(23,True),fill=(*rgb,255))
    selection=None
    for size in (77,73,68,63,58,53,49):
        ft=face(size,True)
        parts=wrap(d,title,ft,W-150,5)
        if parts and len(parts)*int(size*1.28)<325:
            selection=(ft,parts,size);break
    if not selection:raise ValueError('Başlık görsele sığmıyor, daha kısa yaz')
    ft,ls,sz=selection
    sy=315
    for idx,txt in enumerate(ls):
        fill=(245,249,255) if idx<len(ls)-1 else (*rgb,255)
        d.text((66,sy),txt,font=ft,fill=fill,stroke_width=0)
        sy+=int(sz*1.27)
    fs=face(28)
    sub_lines=wrap(d,subtitle,fs,W-180,3)
    if sub_lines is None: raise ValueError('Alt başlık çok uzun')
    sy=max(sy+15,585)
    for ln in sub_lines:
        d.text((68,sy),ln,font=fs,fill=(205,222,241));sy+=42
    # cards: no numerical business metrics (interface-only visual accents)
    y1=max(sy+50,750 if H==1350 else 705)
    if y1>H-370: y1=H-370
    xs=[68,W//2+5]; widths=[W//2-80,W//2-80]
    for i,(x,w) in enumerate(zip(xs,widths)):
        d.rounded_rectangle((x,y1,x+w,y1+230),radius=24,fill=(11,27,46,230),outline=(*rgb,117),width=2)
        d.ellipse((x+22,y1+24,x+55,y1+57),fill=(*rgb,80),outline=(*rgb,230),width=2)
        d.text((x+69,y1+26),('STRATEJİ','DENEYİM')[i],font=face(20,True),fill=(243,248,255))
        if i==0:
            for j,h in enumerate([43,72,64,115,132,162]):
                d.rounded_rectangle((x+35+j*62,y1+206-h,x+65+j*62,y1+206),radius=5,fill=(*rgb,83+j*20))
        else:
            d.line([(x+42,y1+183),(x+108,y1+150),(x+167,y1+166),(x+240,y1+98),(x+339,y1+68)],fill=(*rgb,255),width=7,joint='curve')
            for a,b in ((42,183),(108,150),(167,166),(240,98),(339,68)):
                d.ellipse((x+a-7,y1+b-7,x+a+7,y1+b+7),fill=(245,250,255))
    # bottom divider and CTA
    d.line((67,H-165,W-67,H-165),fill=(98,127,160,110),width=2)
    d.text((68,H-137),'STRATEJİ  /  TASARIM  /  PERFORMANS',font=face(20,True),fill=(185,203,224))
    d.text((68,H-90),'semtasdijital.com',font=face(26),fill=(*rgb,255))
    output_path=Path(output_path);output_path.parent.mkdir(parents=True,exist_ok=True)
    im=Image.alpha_composite(im,layer).convert('RGB');im.save(output_path,'PNG',optimize=True)
    return output_path
