"""Safe read-only API key readiness probe. Never sends a paid image generation request."""
import os
import requests

def main():
    key=os.getenv("GEMINI_API_KEY","").strip()
    if not key:
        raise RuntimeError("GEMINI_API_KEY GitHub Secrets'ta yok")
    url="https://generativelanguage.googleapis.com/v1beta/models"
    try:
        response=requests.get(url,headers={"x-goog-api-key":key},params={"pageSize":100},timeout=25)
    except requests.RequestException as ex:
        raise RuntimeError("Gemini modeller listesi baglanti hatasi: "+type(ex).__name__) from ex
    print("Gemini key status:",response.status_code)
    if response.status_code!=200:
        raise RuntimeError("Gemini key dogrulanamadi (anahtar, proje veya kota ayarlarina bak): HTTP "+str(response.status_code))
    result=response.json()
    model_names=[m.get("name","").removeprefix("models/") for m in result.get("models",[])]
    for name in ("gemini-3.5-flash-lite","gemini-nano-banana-2.1","gemini-3-pro-image"):
        print(name, "LISTED" if name in model_names else "NOT IN FIRST PAGE")
    print("OK: Anahtar Gemini Model List API'ye ulasiyor. Bu GORSEL URETIMININ UCRETSIZ OLDUGU anlamina gelmez!")
    print("Nano Banana API image models have no Free Tier according to official Google pricing.")

if __name__=="__main__":
    main()
