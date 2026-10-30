"""Semtas approval via GitHub Issues. Review is mandatory before publication."""
from datetime import datetime, timezone
from pathlib import Path
import json
import os
import re
import sys
import requests

ROOT = Path(__file__).resolve().parent.parent
POSTS = ROOT / "content" / "posts"
MARKER = "semtas-autopilot-review"

def identity():
    repo = os.environ.get("GITHUB_REPOSITORY", "").strip()
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if repo != "exman3408/semtas-social-autopilot" or not token:
        raise RuntimeError("Yalnizca dogrulanmis Semtas GitHub deposunda calisir")
    return repo, token

def github(method, endpoint, token, data=None):
    url = "https://api.github.com" + endpoint
    r = requests.request(
        method, url,
        headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        json=data, timeout=30
    )
    if not r.ok:
        raise RuntimeError("GitHub Issue API hatasi: HTTP " + str(r.status_code) + " " + r.text[:200])
    return r.json()

def read_post(day):
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day or ""):
        raise RuntimeError("Gecersiz tarih")
    path = POSTS / (day + ".json")
    if not path.is_file():
        raise RuntimeError("Icerik dosyasi yok: " + day)
    return path, json.loads(path.read_text(encoding="utf-8"))

def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def issue_body(post, base):
    lines = [
        "<!-- " + MARKER + ":" + post["date"] + " -->",
        "# SEMTAŞ DİJİTAL — Yayın öncesi onay",
        "",
        "@exman3408, yeni bir Semtaş Dijital içeriği incelemeni bekliyor.",
        "",
        "**Tarih:** " + post["date"],
        "**Konu:** " + post.get("category", ""),
        "**Başlık:** " + post.get("headline", ""),
        "",
        "### Görsel önizleme",
        "![Semtaş Dijital içerik görseli](" + base + "/" + post["media_file"] + ")",
        "",
        "Görsel açılmıyorsa yayın onayı verme. Önizleme herkesin erişebileceği GitHub Pages üzerinde barındırılır.",
        "",
        "### Platform metinleri",
    ]
    for channel, item in post.get("channels", {}).items():
        lines.extend(["", "#### " + channel.title(), "", item.get("caption", "")])
    lines.extend([
        "", "---", "",
        "**Onaylamak için:** Bu Issue altına yalnızca `/onayla` yaz.",
        "**Reddetmek için:** `/reddet` yaz.",
        "**Revize istemek için:** `/revize daha premium, gerçek logolu ve dikkat çekici bir tasarım hazırla` gibi açıklama yaz.",
        "",
        "Sadece depo sahibi hesabının yorumları kabul edilir. Onay verilmeden Buffer kuyruğuna aktarılmaz.",
        "Yayınlama ana anahtarı `PUBLISH_ENABLED` ayrıca açık olmalıdır.",
        "Revize talebi mevcut onayı geçersiz kılar. Yeni görsel üretilmeden yeniden `/onayla` kabul edilmez.",
    ])
    return "\n".join(lines)

def request_review():
    repo, token = identity()
    from zoneinfo import ZoneInfo
    today = datetime.now(ZoneInfo("Europe/Istanbul")).date().isoformat()
    path, data = read_post(today)
    if data.get("review", {}).get("issue_number"):
        print("[review] Onay Issue zaten mevcut:", data["review"]["issue_number"])
        return
    base = os.getenv("MEDIA_BASE_URL", "").strip().rstrip("/")
    if not base.startswith("https://"):
        raise RuntimeError("MEDIA_BASE_URL HTTPS olmali")
    title = "[ONAY BEKLIYOR] " + today + " | " + data.get("headline", "Semtas Icerik")
    response = github("POST", "/repos/" + repo + "/issues", token, {
        "title": title,
        "body": issue_body(data, base),
        "assignees": [repo.split("/")[0]]
    })
    if not response.get("number"):
        raise RuntimeError("GitHub Issue numarasi alinmadi")
    data["review"] = {"status": "pending", "issue_number": response["number"], "requested_at": datetime.now(timezone.utc).isoformat()}
    save(path, data)
    print("[review] Onay istegi olusturuldu:", response.get("html_url", ""))

def apply_comment():
    repo, _ = identity()
    event_path = os.getenv("GITHUB_EVENT_PATH", "")
    if not event_path or not Path(event_path).is_file():
        raise RuntimeError("Issue comment GitHub event bilgisi yok")
    evt = json.loads(Path(event_path).read_text(encoding="utf-8"))
    comment = evt.get("comment") or {}
    issue = evt.get("issue") or {}
    actor = str((comment.get("user") or {}).get("login", ""))
    if actor != repo.split("/")[0]:
        print("[review] Sadece depo sahibinin onayi kabul edilir")
        return
    if issue.get("pull_request") or (issue.get("user") or {}).get("login") != "github-actions[bot]":
        print("[review] Otomasyon tarafindan olusturulmamis Issue")
        return
    body = str(issue.get("body") or "")
    match = re.search(r"<!-- " + MARKER + r":(\d{4}-\d{2}-\d{2}) -->", body)
    if not match:
        print("[review] Bu Semtas onay kaydi degil")
        return
    raw_command = str(comment.get("body") or "").strip()
    command = raw_command.lower()
    revision_match = re.match(r"^/revize(?:\\s+(.+))?$", raw_command, flags=re.IGNORECASE | re.DOTALL)
    if command not in ("/onayla", "/reddet") and not revision_match:
        print("[review] Yorum onay veya revize komutu degil")
        return
    path, data = read_post(match.group(1))
    review = data.get("review") or {}
    if review.get("issue_number") != issue.get("number"):
        print("[review] Issue numarasi taslakla eslesmedi")
        return
    if revision_match:
        instruction = (revision_match.group(1) or "").strip()
        if len(instruction) < 8 or len(instruction) > 1800:
            raise RuntimeError("Revize talebi acik ve 8-1800 karakter olmali")
        # A post already on Buffer cannot safely be replaced by this event handler.
        queued = [k for k, v in data.get("channels", {}).items()
                  if v.get("state") in ("queued", "published") or v.get("buffer_post_id")]
        if queued:
            raise RuntimeError("Bu gonderi Buffer'da zaten sirada/yayinda. Once Buffer'dan iptal edilmeli: " + ", ".join(queued))
        old_ids = {str(req.get("comment_id")) for req in review.get("revision_requests", [])}
        if str(comment.get("id")) in old_ids:
            print("[review] Bu revize yorumu daha once kaydedilmis")
            return
        requests_list = list(review.get("revision_requests") or [])
        requests_list.append({
            "comment_id": comment.get("id"),
            "instruction": instruction,
            "requested_by": actor,
            "requested_at": datetime.now(timezone.utc).isoformat(),
            "status": "awaiting_redesign",
        })
        review.update(
            status="revision_requested",
            revision_note=instruction,
            revision_comment_id=comment.get("id"),
            revision_requests=requests_list,
            revision_requested_at=datetime.now(timezone.utc).isoformat(),
        )
        review.pop("approved_at", None)
        review.pop("approved_by", None)
        review.pop("rejected_at", None)
        review.pop("rejected_by", None)
        data["review"] = review
        save(path, data)
        print("[review] Revize talebi kaydedildi. Bu gorsel YAYINLANAMAZ:", instruction[:140])
        return

    if review.get("status") != "pending":
        print("[review] Mevcut taslak icin onay verilemez:", review.get("status"),
              "- once yeni gorselin hazirlanmasi gerekir")
        return
    if command == "/onayla":
        review.update(status="approved", approved_by=actor, approved_at=datetime.now(timezone.utc).isoformat())
    else:
        review.update(status="rejected", rejected_by=actor, rejected_at=datetime.now(timezone.utc).isoformat())
    data["review"] = review
    save(path, data)
    print("[review]", data["date"], review["status"])

def main():
    action = sys.argv[1] if len(sys.argv) > 1 else ""
    if action == "request":
        request_review()
    elif action == "apply":
        apply_comment()
    else:
        raise RuntimeError("Kullanim: python -m socialbot.review request|apply")

if __name__ == "__main__":
    main()
