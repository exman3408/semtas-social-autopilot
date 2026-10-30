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
        "",
        "Sadece depo sahibi hesabının yorumları kabul edilir. Onay verilmeden Buffer kuyruğuna aktarılmaz.",
        "Yayınlama ana anahtarı `PUBLISH_ENABLED` ayrıca açık olmalıdır.",
        "Yayın öncesi değişiklik gerekiyorsa `/reddet` yazıp yeni taslak iste.",
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
    command = str(comment.get("body") or "").strip().lower()
    if command not in ("/onayla", "/reddet"):
        print("[review] Yorum onay komutu degil")
        return
    path, data = read_post(match.group(1))
    review = data.get("review") or {}
    if review.get("issue_number") != issue.get("number"):
        print("[review] Issue numarasi taslakla eslesmedi")
        return
    if review.get("status") != "pending":
        print("[review] Icerik zaten karara baglanmis:", review.get("status"))
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
