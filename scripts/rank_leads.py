"""
Gera o ranking de leads (chance de fechar + preço sugerido) por nicho e o plano de disparos.

Uso:
  python scripts/rank_leads.py [--per-day 20] [--start 2026-11-11] [--tiers A,B] [--db caminho.db]

Saída (pasta exports/, ignorada pelo git por conter dados pessoais):
  ranking_leads_<data>.csv   (todos os leads, ordenados)
  ranking_leads_<data>.md    (resumo por nicho + plano de disparo)

Somente leitura: não altera o banco, não enfileira e não envia nenhuma mensagem.
"""

import argparse
import os
import sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from app.database import list_leads, list_outreach_queue  # noqa: E402
from app.services.deal_ranker import (  # noqa: E402
    build_outreach_plan,
    export_ranking_csv,
    group_by_segment,
    rank_leads,
    render_markdown_report,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--per-day", type=int, default=20, help="Disparos por dia (padrão 20, seguro p/ número novo)")
    parser.add_argument("--start", type=str, default=None, help="Data do dia 1 (AAAA-MM-DD); pula fins de semana")
    parser.add_argument("--tiers", type=str, default="A,B,C", help="Tiers incluídos no plano (padrão A,B,C)")
    parser.add_argument("--db", type=str, default=None, help="Caminho do banco SQLite (padrão: o do painel)")
    parser.add_argument("--out", type=str, default=os.path.join(ROOT, "exports"), help="Pasta de saída")
    args = parser.parse_args()

    leads = list_leads(limit=100000, db_path=args.db)
    queued = {q["lead_id"] for q in list_outreach_queue(limit=100000, db_path=args.db)}
    ranked = rank_leads(leads, contacted_lead_ids=queued)
    groups = group_by_segment(ranked)
    start = date.fromisoformat(args.start) if args.start else None
    plan = build_outreach_plan(ranked, per_day=args.per_day, start_date=start, tiers=args.tiers.split(","))

    os.makedirs(args.out, exist_ok=True)
    stamp = date.today().isoformat()
    csv_path = os.path.join(args.out, f"ranking_leads_{stamp}.csv")
    md_path = os.path.join(args.out, f"ranking_leads_{stamp}.md")
    export_ranking_csv(ranked, csv_path)
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write(render_markdown_report(ranked, groups, plan))

    print(f"{len(ranked)} leads ranqueados | {sum(1 for r in ranked if r['outreach_ready'])} prontos | {len(plan)} dia(s) de disparo")
    print(csv_path)
    print(md_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
