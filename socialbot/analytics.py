"""Weekly report from Buffer's native per-post metrics (where supported)."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import json
import os
from .buffer_api import BufferAPI

REPORTS = Path(__file__).resolve().parent.parent/'reports'

def create_weekly_report():
    org = os.getenv('BUFFER_ORG_ID', '').strip()
    if not org:
        raise RuntimeError('BUFFER_ORG_ID gerekli')
    api = BufferAPI()
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=7)
    report = [f'# SEMTAŞ DİJİTAL — Sosyal Medya Haftalık Raporu',
              f'**Tarih aralığı (UTC):** {start.date()} – {end.date()}',
              '', 'Buffer üzerinden API ile alınan veriler. Erişim olmayan metrikler "veri yok" olarak gösterilir.', '']
    for platform in ('instagram', 'facebook', 'linkedin'):
        channel = os.getenv(f'BUFFER_{platform.upper()}_CHANNEL_ID', '').strip()
        if not channel:
            continue
        # Official aggregatedPostMetrics query: more efficient and accurate than per-post paging.
        start_iso = start.strftime('%Y-%m-%dT%H:%M:%SZ')
        end_iso = end.strftime('%Y-%m-%dT%H:%M:%SZ')
        q = ('query { aggregatedPostMetrics(input: {organizationId: ' + json.dumps(org) +
             ', startDateTime: ' + json.dumps(start_iso) +
             ', endDateTime: ' + json.dumps(end_iso) +
             ', channelIds: [' + json.dumps(channel) + ']})'
             ' { metrics {type name value unit} metricsUpdatedAt } }')
        data = api.call(q)['aggregatedPostMetrics']
        report.extend([f'## {platform.title()}', f'Metrik güncellemesi: {data.get("metricsUpdatedAt") or "Veri yok"}', ''])
        for metric in data.get('metrics') or []:
            report.append(f'- {metric.get("name") or metric.get("type")}: {metric.get("value")} {metric.get("unit") or ""}')
        report.append('')
    REPORTS.mkdir(parents=True, exist_ok=True)
    dest = REPORTS/f'weekly-{end.date().isoformat()}.md'
    dest.write_text('\n'.join(report), encoding='utf-8')
    print(f'[report] Oluşturuldu: {dest}')
