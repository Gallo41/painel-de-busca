import json
import os
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "painel_busca.db",
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    target = db_path or os.environ.get("PAINEL_DB_PATH") or DEFAULT_DB_PATH
    os.makedirs(os.path.dirname(os.path.abspath(target)), exist_ok=True)
    conn = sqlite3.connect(target, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def init_db(db_path: Optional[str] = None) -> None:
    with get_connection(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS niches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                category_group TEXT NOT NULL,
                search_terms_json TEXT NOT NULL DEFAULT '[]',
                cnae_codes_json TEXT NOT NULL DEFAULT '[]',
                recommended_offer TEXT NOT NULL DEFAULT 'SITE_NOVO',
                description TEXT NOT NULL DEFAULT '',
                active INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS search_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                city TEXT NOT NULL,
                state TEXT NOT NULL DEFAULT 'SP',
                niche_slugs_json TEXT NOT NULL DEFAULT '[]',
                keywords_json TEXT NOT NULL DEFAULT '[]',
                depth INTEGER NOT NULL DEFAULT 5,
                grid_size INTEGER NOT NULL DEFAULT 1,
                include_socials INTEGER NOT NULL DEFAULT 1,
                source_mode TEXT NOT NULL DEFAULT 'google_maps',
                status TEXT NOT NULL DEFAULT 'pending',
                total_found INTEGER NOT NULL DEFAULT 0,
                error_message TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                completed_at TEXT
            );

            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER,
                place_id TEXT,
                dedupe_key TEXT UNIQUE NOT NULL,
                niche_slug TEXT NOT NULL DEFAULT 'geral',
                title TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT '',
                phone TEXT NOT NULL DEFAULT '',
                whatsapp_clean TEXT NOT NULL DEFAULT '',
                emails TEXT NOT NULL DEFAULT '',
                website TEXT NOT NULL DEFAULT '',
                address TEXT NOT NULL DEFAULT '',
                city TEXT NOT NULL DEFAULT '',
                state TEXT NOT NULL DEFAULT '',
                review_rating REAL NOT NULL DEFAULT 0.0,
                review_count INTEGER NOT NULL DEFAULT 0,
                instagram TEXT NOT NULL DEFAULT '',
                facebook TEXT NOT NULL DEFAULT '',
                linkedin TEXT NOT NULL DEFAULT '',
                cnpj TEXT NOT NULL DEFAULT '',
                opened_date TEXT NOT NULL DEFAULT '',
                source TEXT NOT NULL DEFAULT 'google_maps',

                -- Raio-X Indexado
                has_website INTEGER NOT NULL DEFAULT 0,
                is_social_only_url INTEGER NOT NULL DEFAULT 0,
                site_in_air INTEGER NOT NULL DEFAULT 0,
                http_status INTEGER NOT NULL DEFAULT 0,
                has_ssl INTEGER NOT NULL DEFAULT 0,
                response_time_ms INTEGER NOT NULL DEFAULT 0,
                suggested_domain TEXT NOT NULL DEFAULT '',
                domain_available_br INTEGER NOT NULL DEFAULT 0,
                detected_cms TEXT NOT NULL DEFAULT 'Nao Analisado',
                tech_stack_json TEXT NOT NULL DEFAULT '[]',
                has_whatsapp_widget INTEGER NOT NULL DEFAULT 0,
                has_analytics_pixel INTEGER NOT NULL DEFAULT 0,
                is_mobile_friendly INTEGER NOT NULL DEFAULT 0,
                has_complex_system INTEGER NOT NULL DEFAULT 0,
                wayback_first_seen TEXT,
                wayback_last_seen TEXT,
                wayback_days_since_update INTEGER,
                external_tools_links_json TEXT NOT NULL DEFAULT '{}',
                xray_raw_json TEXT NOT NULL DEFAULT '{}',

                -- Qualificacao & Score
                opportunity_score INTEGER NOT NULL DEFAULT 0,
                primary_pain TEXT NOT NULL DEFAULT 'NAO_ANALISADO',
                recommended_service TEXT NOT NULL DEFAULT 'SITE_NOVO',
                pain_summary TEXT NOT NULL DEFAULT '',
                outreach_scripts_json TEXT NOT NULL DEFAULT '{}',

                -- Gestao de Carteira (Voce + Amigo)
                assigned_to TEXT NOT NULL DEFAULT 'nao_atribuido',
                lead_status TEXT NOT NULL DEFAULT 'novo',
                notes TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_leads_score ON leads(opportunity_score DESC);
            CREATE INDEX IF NOT EXISTS idx_leads_pain ON leads(primary_pain);
            CREATE INDEX IF NOT EXISTS idx_leads_niche ON leads(niche_slug);
            CREATE INDEX IF NOT EXISTS idx_leads_assigned ON leads(assigned_to);
            CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(lead_status);

            CREATE TABLE IF NOT EXISTS outreach_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER NOT NULL,
                channel TEXT NOT NULL,
                recipient TEXT NOT NULL DEFAULT '',
                subject TEXT NOT NULL DEFAULT '',
                message_body TEXT NOT NULL DEFAULT '',
                diagnostic_context_json TEXT NOT NULL DEFAULT '{}',
                status TEXT NOT NULL DEFAULT 'ready',
                worker_id TEXT NOT NULL DEFAULT '',
                scheduled_for TEXT,
                sent_at TEXT,
                external_message_id TEXT NOT NULL DEFAULT '',
                webhook_response_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(lead_id) REFERENCES leads(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_outreach_status_channel ON outreach_queue(status, channel);
            """
        )


def upsert_niches(niches: List[Dict[str, Any]], db_path: Optional[str] = None) -> None:
    with get_connection(db_path) as conn:
        for n in niches:
            conn.execute(
                """
                INSERT INTO niches (
                    slug, name, category_group, search_terms_json,
                    cnae_codes_json, recommended_offer, description, active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(slug) DO UPDATE SET
                    name = excluded.name,
                    category_group = excluded.category_group,
                    search_terms_json = excluded.search_terms_json,
                    cnae_codes_json = excluded.cnae_codes_json,
                    recommended_offer = excluded.recommended_offer,
                    description = excluded.description,
                    active = excluded.active
                """,
                (
                    n["slug"],
                    n["name"],
                    n.get("category_group", "Geral"),
                    json.dumps(n.get("search_terms", []), ensure_ascii=False),
                    json.dumps(n.get("cnae_codes", []), ensure_ascii=False),
                    n.get("recommended_offer", "SITE_NOVO"),
                    n.get("description", ""),
                    1 if n.get("active", True) else 0,
                ),
            )


def list_niches(active_only: bool = True, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    query = "SELECT * FROM niches"
    if active_only:
        query += " WHERE active = 1"
    query += " ORDER BY category_group, name"
    with get_connection(db_path) as conn:
        rows = conn.execute(query).fetchall()
    result = []
    for r in rows:
        d = dict(r)
        d["search_terms"] = json.loads(d.pop("search_terms_json", "[]"))
        d["cnae_codes"] = json.loads(d.pop("cnae_codes_json", "[]"))
        d["active"] = bool(d["active"])
        result.append(d)
    return result


def create_search_job(
    city: str,
    state: str,
    niche_slugs: List[str],
    keywords: List[str],
    depth: int = 5,
    grid_size: int = 1,
    include_socials: bool = True,
    source_mode: str = "google_maps",
    db_path: Optional[str] = None,
) -> int:
    with get_connection(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO search_jobs (
                city, state, niche_slugs_json, keywords_json,
                depth, grid_size, include_socials, source_mode, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
            """,
            (
                city.strip(),
                state.strip().upper(),
                json.dumps(niche_slugs, ensure_ascii=False),
                json.dumps(keywords, ensure_ascii=False),
                depth,
                grid_size,
                1 if include_socials else 0,
                source_mode,
                _now_iso(),
            ),
        )
        return int(cur.lastrowid)


def update_search_job(
    job_id: int,
    status: str,
    total_found: Optional[int] = None,
    error_message: str = "",
    db_path: Optional[str] = None,
) -> None:
    completed_at = _now_iso() if status in ("completed", "failed") else None
    with get_connection(db_path) as conn:
        if total_found is not None:
            conn.execute(
                """
                UPDATE search_jobs
                SET status = ?, total_found = ?, error_message = ?, completed_at = COALESCE(?, completed_at)
                WHERE id = ?
                """,
                (status, total_found, error_message, completed_at, job_id),
            )
        else:
            conn.execute(
                """
                UPDATE search_jobs
                SET status = ?, error_message = ?, completed_at = COALESCE(?, completed_at)
                WHERE id = ?
                """,
                (status, error_message, completed_at, job_id),
            )


def _deserialize_job(row: Optional[sqlite3.Row]) -> Optional[Dict[str, Any]]:
    if not row:
        return None
    d = dict(row)
    d["niche_slugs"] = json.loads(d.pop("niche_slugs_json", "[]"))
    d["keywords"] = json.loads(d.pop("keywords_json", "[]"))
    d["include_socials"] = bool(d["include_socials"])
    return d


def get_search_job(job_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    with get_connection(db_path) as conn:
        row = conn.execute("SELECT * FROM search_jobs WHERE id = ?", (job_id,)).fetchone()
    return _deserialize_job(row)


def list_search_jobs(limit: int = 30, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    with get_connection(db_path) as conn:
        rows = conn.execute("SELECT * FROM search_jobs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [_deserialize_job(r) for r in rows if r]


def _make_dedupe_key(lead: Dict[str, Any]) -> str:
    place_id = (lead.get("place_id") or "").strip()
    if place_id:
        return f"pid:{place_id}"
    cnpj = (lead.get("cnpj") or "").strip()
    if cnpj:
        return f"cnpj:{cnpj}"
    title = (lead.get("title") or "").strip().lower()
    city = (lead.get("city") or "").strip().lower()
    phone = (lead.get("phone") or "").strip()
    return f"tc:{title}|{city}|{phone}"


def upsert_lead(lead: Dict[str, Any], db_path: Optional[str] = None) -> int:
    dedupe_key = _make_dedupe_key(lead)
    now = _now_iso()
    try:
        rating = float(lead.get("review_rating") or 0.0)
    except (TypeError, ValueError):
        rating = 0.0
    try:
        rcount = int(float(lead.get("review_count") or 0))
    except (TypeError, ValueError):
        rcount = 0

    with get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO leads (
                job_id, place_id, dedupe_key, niche_slug, title, category,
                phone, whatsapp_clean, emails, website, address, city, state,
                review_rating, review_count, instagram, facebook, linkedin,
                cnpj, opened_date, source, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(dedupe_key) DO UPDATE SET
                job_id = COALESCE(excluded.job_id, leads.job_id),
                niche_slug = CASE WHEN excluded.niche_slug != 'geral' THEN excluded.niche_slug ELSE leads.niche_slug END,
                category = CASE WHEN excluded.category != '' THEN excluded.category ELSE leads.category END,
                phone = CASE WHEN excluded.phone != '' THEN excluded.phone ELSE leads.phone END,
                whatsapp_clean = CASE WHEN excluded.whatsapp_clean != '' THEN excluded.whatsapp_clean ELSE leads.whatsapp_clean END,
                emails = CASE WHEN excluded.emails != '' THEN excluded.emails ELSE leads.emails END,
                website = CASE WHEN excluded.website != '' THEN excluded.website ELSE leads.website END,
                address = CASE WHEN excluded.address != '' THEN excluded.address ELSE leads.address END,
                review_rating = CASE WHEN excluded.review_rating > 0 THEN excluded.review_rating ELSE leads.review_rating END,
                review_count = CASE WHEN excluded.review_count > 0 THEN excluded.review_count ELSE leads.review_count END,
                instagram = CASE WHEN excluded.instagram != '' THEN excluded.instagram ELSE leads.instagram END,
                facebook = CASE WHEN excluded.facebook != '' THEN excluded.facebook ELSE leads.facebook END,
                linkedin = CASE WHEN excluded.linkedin != '' THEN excluded.linkedin ELSE leads.linkedin END,
                cnpj = CASE WHEN excluded.cnpj != '' THEN excluded.cnpj ELSE leads.cnpj END,
                opened_date = CASE WHEN excluded.opened_date != '' THEN excluded.opened_date ELSE leads.opened_date END,
                updated_at = excluded.updated_at
            """,
            (
                lead.get("job_id"),
                (lead.get("place_id") or "").strip(),
                dedupe_key,
                lead.get("niche_slug") or "geral",
                (lead.get("title") or "Empresa Sem Nome").strip(),
                (lead.get("category") or "").strip(),
                (lead.get("phone") or "").strip(),
                (lead.get("whatsapp_clean") or "").strip(),
                (lead.get("emails") or "").strip(),
                (lead.get("website") or "").strip(),
                (lead.get("address") or "").strip(),
                (lead.get("city") or "").strip(),
                (lead.get("state") or "SP").strip(),
                rating,
                rcount,
                (lead.get("instagram") or "").strip(),
                (lead.get("facebook") or "").strip(),
                (lead.get("linkedin") or "").strip(),
                (lead.get("cnpj") or "").strip(),
                (lead.get("opened_date") or "").strip(),
                lead.get("source") or "google_maps",
                now,
                now,
            ),
        )
        row = conn.execute("SELECT id FROM leads WHERE dedupe_key = ?", (dedupe_key,)).fetchone()
        return int(row["id"])


def update_lead_xray_and_score(
    lead_id: int,
    xray_data: Dict[str, Any],
    score_data: Dict[str, Any],
    outreach_scripts: Dict[str, Any],
    db_path: Optional[str] = None,
) -> None:
    now = _now_iso()
    with get_connection(db_path) as conn:
        conn.execute(
            """
            UPDATE leads SET
                has_website = ?,
                is_social_only_url = ?,
                site_in_air = ?,
                http_status = ?,
                has_ssl = ?,
                response_time_ms = ?,
                suggested_domain = ?,
                domain_available_br = ?,
                detected_cms = ?,
                tech_stack_json = ?,
                has_whatsapp_widget = ?,
                has_analytics_pixel = ?,
                is_mobile_friendly = ?,
                has_complex_system = ?,
                wayback_first_seen = ?,
                wayback_last_seen = ?,
                wayback_days_since_update = ?,
                external_tools_links_json = ?,
                xray_raw_json = ?,
                opportunity_score = ?,
                primary_pain = ?,
                recommended_service = ?,
                pain_summary = ?,
                outreach_scripts_json = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                1 if xray_data.get("has_website") else 0,
                1 if xray_data.get("is_social_only_url") else 0,
                1 if xray_data.get("site_in_air") else 0,
                int(xray_data.get("http_status") or 0),
                1 if xray_data.get("has_ssl") else 0,
                int(xray_data.get("response_time_ms") or 0),
                xray_data.get("suggested_domain") or "",
                1 if xray_data.get("domain_available_br") else 0,
                xray_data.get("detected_cms") or "Sem Site",
                json.dumps(xray_data.get("tech_stack") or [], ensure_ascii=False),
                1 if xray_data.get("has_whatsapp_widget") else 0,
                1 if xray_data.get("has_analytics_pixel") else 0,
                1 if xray_data.get("is_mobile_friendly") else 0,
                1 if xray_data.get("has_complex_system") else 0,
                xray_data.get("wayback_first_seen"),
                xray_data.get("wayback_last_seen"),
                xray_data.get("wayback_days_since_update"),
                json.dumps(xray_data.get("external_tools_links") or {}, ensure_ascii=False),
                json.dumps(xray_data, ensure_ascii=False),
                int(score_data.get("opportunity_score") or 0),
                score_data.get("primary_pain") or "SEM_SITE",
                score_data.get("recommended_service") or "SITE_NOVO",
                score_data.get("pain_summary") or "",
                json.dumps(outreach_scripts or {}, ensure_ascii=False),
                now,
                lead_id,
            ),
        )


def update_lead_management(
    lead_id: int,
    assigned_to: Optional[str] = None,
    lead_status: Optional[str] = None,
    notes: Optional[str] = None,
    db_path: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    fields = []
    params: List[Any] = []
    if assigned_to is not None:
        fields.append("assigned_to = ?")
        params.append(assigned_to)
    if lead_status is not None:
        fields.append("lead_status = ?")
        params.append(lead_status)
    if notes is not None:
        fields.append("notes = ?")
        params.append(notes)
    if not fields:
        return get_lead(lead_id, db_path=db_path)

    fields.append("updated_at = ?")
    params.append(_now_iso())
    params.append(lead_id)

    with get_connection(db_path) as conn:
        conn.execute(f"UPDATE leads SET {', '.join(fields)} WHERE id = ?", params)
    return get_lead(lead_id, db_path=db_path)


def _deserialize_lead(row: Optional[sqlite3.Row]) -> Optional[Dict[str, Any]]:
    if not row:
        return None
    d = dict(row)
    for bool_col in (
        "has_website",
        "is_social_only_url",
        "site_in_air",
        "has_ssl",
        "domain_available_br",
        "has_whatsapp_widget",
        "has_analytics_pixel",
        "is_mobile_friendly",
        "has_complex_system",
    ):
        d[bool_col] = bool(d.get(bool_col))
    d["tech_stack"] = json.loads(d.pop("tech_stack_json", "[]"))
    d["external_tools_links"] = json.loads(d.pop("external_tools_links_json", "{}"))
    d["xray_raw"] = json.loads(d.pop("xray_raw_json", "{}"))
    d["outreach_scripts"] = json.loads(d.pop("outreach_scripts_json", "{}"))
    return d


def get_lead(lead_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    with get_connection(db_path) as conn:
        row = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
    return _deserialize_lead(row)


def list_leads(
    niche_slug: Optional[str] = None,
    city: Optional[str] = None,
    primary_pain: Optional[str] = None,
    recommended_service: Optional[str] = None,
    assigned_to: Optional[str] = None,
    lead_status: Optional[str] = None,
    min_score: int = 0,
    only_domain_available: bool = False,
    search_query: Optional[str] = None,
    limit: int = 200,
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    clauses = ["opportunity_score >= ?"]
    params: List[Any] = [min_score]

    if niche_slug:
        clauses.append("niche_slug = ?")
        params.append(niche_slug)
    if city:
        clauses.append("LOWER(city) LIKE ?")
        params.append(f"%{city.strip().lower()}%")
    if primary_pain:
        clauses.append("primary_pain = ?")
        params.append(primary_pain)
    if recommended_service:
        clauses.append("recommended_service = ?")
        params.append(recommended_service)
    if assigned_to:
        clauses.append("assigned_to = ?")
        params.append(assigned_to)
    if lead_status:
        clauses.append("lead_status = ?")
        params.append(lead_status)
    if only_domain_available:
        clauses.append("domain_available_br = 1")
    if search_query:
        q = f"%{search_query.strip().lower()}%"
        clauses.append("(LOWER(title) LIKE ? OR LOWER(category) LIKE ? OR LOWER(address) LIKE ?)")
        params.extend([q, q, q])

    params.append(limit)
    sql = f"SELECT * FROM leads WHERE {' AND '.join(clauses)} ORDER BY opportunity_score DESC, review_count DESC LIMIT ?"
    with get_connection(db_path) as conn:
        rows = conn.execute(sql, params).fetchall()
    return [_deserialize_lead(r) for r in rows if r]


def purge_simulated_leads(db_path: Optional[str] = None) -> int:
    """Remove leads de demonstração/simulados (place_id 'sim_*' ou origem de gerador CNAE ilustrativo)."""
    with get_connection(db_path) as conn:
        cur = conn.execute(
            "DELETE FROM leads WHERE place_id LIKE 'sim_%' OR source = 'cnae_recem_abertas'"
        )
        return cur.rowcount


def get_dashboard_stats(db_path: Optional[str] = None) -> Dict[str, Any]:
    with get_connection(db_path) as conn:
        total = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
        without_site = conn.execute(
            "SELECT COUNT(*) FROM leads WHERE has_website = 0 OR is_social_only_url = 1"
        ).fetchone()[0]
        site_down = conn.execute(
            "SELECT COUNT(*) FROM leads WHERE has_website = 1 AND is_social_only_url = 0 AND site_in_air = 0"
        ).fetchone()[0]
        domain_available = conn.execute(
            "SELECT COUNT(*) FROM leads WHERE domain_available_br = 1"
        ).fetchone()[0]
        complex_opp = conn.execute(
            "SELECT COUNT(*) FROM leads WHERE recommended_service = 'SISTEMA_COMPLEXO' OR primary_pain = 'OPORTUNIDADE_SISTEMA'"
        ).fetchone()[0]
        assigned_eu = conn.execute(
            "SELECT COUNT(*) FROM leads WHERE assigned_to = 'eu'"
        ).fetchone()[0]
        assigned_amigo = conn.execute(
            "SELECT COUNT(*) FROM leads WHERE assigned_to = 'amigo'"
        ).fetchone()[0]
        contacted = conn.execute(
            "SELECT COUNT(*) FROM leads WHERE lead_status IN ('contatado', 'respondeu', 'reuniao', 'fechado')"
        ).fetchone()[0]
        queue_ready = conn.execute(
            "SELECT COUNT(*) FROM outreach_queue WHERE status = 'ready'"
        ).fetchone()[0]

    return {
        "total_leads": total,
        "without_site": without_site,
        "site_down": site_down,
        "domain_available": domain_available,
        "complex_system_opportunities": complex_opp,
        "assigned_eu": assigned_eu,
        "assigned_amigo": assigned_amigo,
        "contacted": contacted,
        "outreach_queue_ready": queue_ready,
    }


def enqueue_outreach(
    lead_id: int,
    channel: str,
    recipient: str,
    subject: str,
    message_body: str,
    diagnostic_context: Optional[Dict[str, Any]] = None,
    scheduled_for: Optional[str] = None,
    db_path: Optional[str] = None,
) -> int:
    now = _now_iso()
    channel_clean = channel.strip().lower()
    ctx_json = json.dumps(diagnostic_context or {}, ensure_ascii=False)

    with get_connection(db_path) as conn:
        existing = conn.execute(
            """
            SELECT id FROM outreach_queue
            WHERE lead_id = ? AND channel = ? AND status IN ('ready', 'queued')
            """,
            (lead_id, channel_clean),
        ).fetchone()

        if existing:
            qid = int(existing["id"])
            conn.execute(
                """
                UPDATE outreach_queue
                SET recipient = ?, subject = ?, message_body = ?,
                    diagnostic_context_json = ?, scheduled_for = ?, updated_at = ?
                WHERE id = ?
                """,
                (recipient, subject, message_body, ctx_json, scheduled_for, now, qid),
            )
            return qid

        cur = conn.execute(
            """
            INSERT INTO outreach_queue (
                lead_id, channel, recipient, subject, message_body,
                diagnostic_context_json, status, scheduled_for, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, 'ready', ?, ?, ?)
            """,
            (lead_id, channel_clean, recipient, subject, message_body, ctx_json, scheduled_for, now, now),
        )
        return int(cur.lastrowid)


def _deserialize_outreach(row: Optional[sqlite3.Row]) -> Optional[Dict[str, Any]]:
    if not row:
        return None
    d = dict(row)
    d["diagnostic_context"] = json.loads(d.pop("diagnostic_context_json", "{}"))
    d["webhook_response"] = json.loads(d.pop("webhook_response_json", "{}"))
    return d


def list_outreach_queue(
    status: Optional[str] = None,
    channel: Optional[str] = None,
    limit: int = 100,
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    clauses = ["1=1"]
    params: List[Any] = []
    if status:
        clauses.append("q.status = ?")
        params.append(status)
    if channel:
        clauses.append("q.channel = ?")
        params.append(channel.strip().lower())
    params.append(limit)

    sql = f"""
        SELECT q.*, l.title AS lead_title, l.city AS lead_city, l.assigned_to AS lead_assigned_to
        FROM outreach_queue q
        LEFT JOIN leads l ON l.id = q.lead_id
        WHERE {' AND '.join(clauses)}
        ORDER BY q.id ASC
        LIMIT ?
    """
    with get_connection(db_path) as conn:
        rows = conn.execute(sql, params).fetchall()
    return [_deserialize_outreach(r) for r in rows if r]


def claim_next_outreach(
    channel: str = "whatsapp",
    worker_id: str = "default-worker",
    db_path: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    now = _now_iso()
    with get_connection(db_path) as conn:
        row = conn.execute(
            """
            SELECT id FROM outreach_queue
            WHERE channel = ? AND status = 'ready'
              AND (scheduled_for IS NULL OR scheduled_for <= ?)
            ORDER BY id ASC
            LIMIT 1
            """,
            (channel.strip().lower(), now),
        ).fetchone()
        if not row:
            return None
        qid = int(row["id"])
        conn.execute(
            "UPDATE outreach_queue SET status = 'sending', worker_id = ?, updated_at = ? WHERE id = ?",
            (worker_id, now, qid),
        )
        claimed = conn.execute(
            """
            SELECT q.*, l.title AS lead_title, l.city AS lead_city
            FROM outreach_queue q
            LEFT JOIN leads l ON l.id = q.lead_id
            WHERE q.id = ?
            """,
            (qid,),
        ).fetchone()
    return _deserialize_outreach(claimed)


def update_outreach_status(
    queue_id: int,
    status: str,
    external_message_id: Optional[str] = None,
    webhook_response: Optional[Dict[str, Any]] = None,
    db_path: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    now = _now_iso()
    sent_at = now if status == "sent" else None
    with get_connection(db_path) as conn:
        conn.execute(
            """
            UPDATE outreach_queue SET
                status = ?,
                external_message_id = COALESCE(?, external_message_id),
                webhook_response_json = CASE WHEN ? = 1 THEN ? ELSE webhook_response_json END,
                sent_at = COALESCE(?, sent_at),
                updated_at = ?
            WHERE id = ?
            """,
            (
                status,
                external_message_id,
                1 if webhook_response is not None else 0,
                json.dumps(webhook_response or {}, ensure_ascii=False),
                sent_at,
                now,
                queue_id,
            ),
        )
        if status == "sent":
            conn.execute(
                """
                UPDATE leads SET lead_status = 'contatado', updated_at = ?
                WHERE id = (SELECT lead_id FROM outreach_queue WHERE id = ?)
                  AND lead_status IN ('novo', 'analisado')
                """,
                (now, queue_id),
            )
        elif status == "replied":
            conn.execute(
                """
                UPDATE leads SET lead_status = 'respondeu', updated_at = ?
                WHERE id = (SELECT lead_id FROM outreach_queue WHERE id = ?)
                """,
                (now, queue_id),
            )
        row = conn.execute("SELECT * FROM outreach_queue WHERE id = ?", (queue_id,)).fetchone()
    return _deserialize_outreach(row)
