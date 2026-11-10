import json
import os
import re
import sqlite3
import unicodedata
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

            CREATE TABLE IF NOT EXISTS agent_settings (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                test_mode INTEGER NOT NULL DEFAULT 1,
                auto_send_enabled INTEGER NOT NULL DEFAULT 0,
                boss_phone TEXT NOT NULL DEFAULT '551999958516',
                test_client_phone TEXT NOT NULL DEFAULT '5519996109028',
                attendant_name TEXT NOT NULL DEFAULT 'Léo',
                company_name TEXT NOT NULL DEFAULT 'Estúdio Digital',
                bridge_url TEXT NOT NULL DEFAULT 'http://127.0.0.1:3100',
                uazapi_url TEXT NOT NULL DEFAULT '',
                uazapi_token TEXT NOT NULL DEFAULT '',
                debounce_seconds REAL NOT NULL DEFAULT 6.0,
                pause_minutes_on_human INTEGER NOT NULL DEFAULT 60,
                updated_at TEXT NOT NULL DEFAULT ''
            );

            INSERT OR IGNORE INTO agent_settings (
                id, test_mode, auto_send_enabled, boss_phone, test_client_phone,
                attendant_name, company_name, bridge_url, debounce_seconds,
                pause_minutes_on_human, updated_at
            ) VALUES (
                1, 1, 0, '551999958516', '5519996109028',
                'Léo', 'Estúdio Digital', 'http://127.0.0.1:3100', 6.0,
                60, datetime('now')
            );

            CREATE TABLE IF NOT EXISTS agent_conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER NOT NULL,
                queue_id INTEGER,
                chatid TEXT NOT NULL,
                real_lead_phone TEXT NOT NULL DEFAULT '',
                is_test_session INTEGER NOT NULL DEFAULT 1,
                status TEXT NOT NULL DEFAULT 'active',
                paused_until TEXT,
                pause_reason TEXT NOT NULL DEFAULT '',
                collected_requirements_json TEXT NOT NULL DEFAULT '{}',
                suggested_price_cents INTEGER NOT NULL DEFAULT 0,
                approved_price_text TEXT NOT NULL DEFAULT '',
                turn_version INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(lead_id) REFERENCES leads(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_agent_conv_chatid ON agent_conversations(chatid, status);
            CREATE INDEX IF NOT EXISTS idx_agent_conv_lead ON agent_conversations(lead_id);

            CREATE TABLE IF NOT EXISTS agent_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                direction TEXT NOT NULL DEFAULT 'inbound',
                content TEXT NOT NULL DEFAULT '',
                external_message_id TEXT NOT NULL DEFAULT '',
                tool_calls_json TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL,
                FOREIGN KEY(conversation_id) REFERENCES agent_conversations(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_agent_msg_conv ON agent_messages(conversation_id, id ASC);

            CREATE TABLE IF NOT EXISTS price_consultations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                lead_id INTEGER NOT NULL,
                client_summary TEXT NOT NULL DEFAULT '',
                scope_type TEXT NOT NULL DEFAULT 'LANDING_PAGE',
                suggested_price_cents INTEGER NOT NULL DEFAULT 0,
                price_range_text TEXT NOT NULL DEFAULT '',
                boss_reply_text TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL,
                responded_at TEXT,
                FOREIGN KEY(conversation_id) REFERENCES agent_conversations(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_price_consult_status ON price_consultations(status, id DESC);

            CREATE TABLE IF NOT EXISTS lead_prototypes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER NOT NULL,
                conversation_id INTEGER,
                scope_type TEXT NOT NULL DEFAULT 'LANDING_PAGE',
                briefing_json TEXT NOT NULL DEFAULT '{}',
                html_content TEXT NOT NULL DEFAULT '',
                output_path TEXT NOT NULL DEFAULT '',
                ai_provider_used TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'ready',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(lead_id) REFERENCES leads(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_prototypes_lead ON lead_prototypes(lead_id, id DESC);
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


def normalize_business_title(title: str) -> str:
    """Normaliza o nome da empresa para comparação invariante de deduplicação."""
    text = (title or "").lower().strip()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("utf-8")
    text = re.sub(r"[\s\-_|/–—:;,.]+", " ", text).strip()
    return text


def _make_dedupe_key(lead: Dict[str, Any]) -> str:
    place_id = (lead.get("place_id") or "").strip()
    if place_id:
        return f"pid:{place_id}"
    cnpj = (lead.get("cnpj") or "").strip()
    if cnpj:
        return f"cnpj:{cnpj}"
    title = normalize_business_title(lead.get("title") or "")
    city = (lead.get("city") or "").strip().lower()
    phone = (lead.get("whatsapp_clean") or lead.get("phone") or "").strip()
    return f"tc:{title}|{city}|{phone}"


def _find_existing_lead_id(
    conn: sqlite3.Connection,
    place_id: str,
    whatsapp_clean: str,
    title: str,
    city: str,
    dedupe_key: str,
) -> Optional[int]:
    """Localiza se a empresa já existe no banco através de múltiplos identificadores únicos."""
    # 1. Pela dedupe_key direta
    row = conn.execute("SELECT id FROM leads WHERE dedupe_key = ?", (dedupe_key,)).fetchone()
    if row:
        return int(row["id"])

    # 2. Pelo place_id se não vazio
    if place_id:
        row = conn.execute("SELECT id FROM leads WHERE place_id = ?", (place_id,)).fetchone()
        if row:
            return int(row["id"])

    norm_city = (city or "").strip().lower()

    # 3. Pelo WhatsApp limpo + cidade (10+ dígitos)
    clean_wp = (whatsapp_clean or "").strip()
    if clean_wp and len(clean_wp) >= 10:
        row = conn.execute(
            "SELECT id FROM leads WHERE whatsapp_clean = ? AND LOWER(TRIM(city)) = ? LIMIT 1",
            (clean_wp, norm_city),
        ).fetchone()
        if row:
            return int(row["id"])

    # 4. Pelo título normalizado + cidade
    norm_t = normalize_business_title(title)
    if norm_t and len(norm_t) > 3:
        candidates = conn.execute(
            "SELECT id, title FROM leads WHERE LOWER(TRIM(city)) = ?", (norm_city,)
        ).fetchall()
        for cand in candidates:
            if normalize_business_title(cand["title"]) == norm_t:
                return int(cand["id"])

    return None


def upsert_lead(lead: Dict[str, Any], db_path: Optional[str] = None) -> int:
    dedupe_key = _make_dedupe_key(lead)
    now = _now_iso()
    place_id = (lead.get("place_id") or "").strip()
    title = (lead.get("title") or "Empresa Sem Nome").strip()
    city = (lead.get("city") or "").strip()
    whatsapp_clean = (lead.get("whatsapp_clean") or "").strip()
    category = (lead.get("category") or "").strip()
    phone = (lead.get("phone") or "").strip()
    emails = (lead.get("emails") or "").strip()
    website = (lead.get("website") or "").strip()
    address = (lead.get("address") or "").strip()
    state = (lead.get("state") or "SP").strip()
    niche_slug = lead.get("niche_slug") or "geral"

    try:
        rating = float(lead.get("review_rating") or 0.0)
    except (TypeError, ValueError):
        rating = 0.0
    try:
        rcount = int(float(lead.get("review_count") or 0))
    except (TypeError, ValueError):
        rcount = 0

    with get_connection(db_path) as conn:
        existing_id = _find_existing_lead_id(
            conn,
            place_id=place_id,
            whatsapp_clean=whatsapp_clean,
            title=title,
            city=city,
            dedupe_key=dedupe_key,
        )
        if existing_id is not None:
            # Já existe! Atualiza e enriquece os dados sem duplicar
            conn.execute(
                """
                UPDATE leads SET
                    job_id = COALESCE(?, job_id),
                    place_id = CASE WHEN (leads.place_id IS NULL OR leads.place_id = '') AND ? != '' THEN ? ELSE leads.place_id END,
                    dedupe_key = CASE WHEN (leads.place_id IS NULL OR leads.place_id = '') AND ? != '' THEN ? ELSE leads.dedupe_key END,
                    niche_slug = CASE WHEN ? != 'geral' THEN ? ELSE leads.niche_slug END,
                    category = CASE WHEN ? != '' THEN ? ELSE leads.category END,
                    phone = CASE WHEN ? != '' THEN ? ELSE leads.phone END,
                    whatsapp_clean = CASE WHEN ? != '' THEN ? ELSE leads.whatsapp_clean END,
                    emails = CASE WHEN ? != '' THEN ? ELSE leads.emails END,
                    website = CASE WHEN ? != '' THEN ? ELSE leads.website END,
                    address = CASE WHEN ? != '' THEN ? ELSE leads.address END,
                    review_rating = CASE WHEN ? > 0 THEN ? ELSE leads.review_rating END,
                    review_count = CASE WHEN ? > 0 THEN ? ELSE leads.review_count END,
                    instagram = CASE WHEN ? != '' THEN ? ELSE leads.instagram END,
                    facebook = CASE WHEN ? != '' THEN ? ELSE leads.facebook END,
                    linkedin = CASE WHEN ? != '' THEN ? ELSE leads.linkedin END,
                    cnpj = CASE WHEN ? != '' THEN ? ELSE leads.cnpj END,
                    opened_date = CASE WHEN ? != '' THEN ? ELSE leads.opened_date END,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    lead.get("job_id"),
                    place_id, place_id,
                    place_id, f"pid:{place_id}",
                    niche_slug, niche_slug,
                    category, category,
                    phone, phone,
                    whatsapp_clean, whatsapp_clean,
                    emails, emails,
                    website, website,
                    address, address,
                    rating, rating,
                    rcount, rcount,
                    (lead.get("instagram") or "").strip(), (lead.get("instagram") or "").strip(),
                    (lead.get("facebook") or "").strip(), (lead.get("facebook") or "").strip(),
                    (lead.get("linkedin") or "").strip(), (lead.get("linkedin") or "").strip(),
                    (lead.get("cnpj") or "").strip(), (lead.get("cnpj") or "").strip(),
                    (lead.get("opened_date") or "").strip(), (lead.get("opened_date") or "").strip(),
                    now,
                    existing_id,
                ),
            )
            return existing_id

        # Novo registro
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
                place_id,
                dedupe_key,
                niche_slug,
                title,
                category,
                phone,
                whatsapp_clean,
                emails,
                website,
                address,
                city,
                state,
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


def deduplicate_existing_leads_db(db_path: Optional[str] = None) -> int:
    """
    Varre o banco e consolida empresas duplicadas (mesmo WhatsApp, mesmo place_id,
    ou mesmo título normalizado na mesma cidade). Preserva o registro mais completo
    (com place_id e categoria) e exclui registros redundantes.
    """
    with get_connection(db_path) as conn:
        leads = conn.execute("SELECT * FROM leads ORDER BY id ASC").fetchall()
        if not leads:
            return 0

        seen_keys: Dict[str, int] = {}
        to_delete: List[int] = []

        for lead in leads:
            lid = int(lead["id"])
            city = (lead["city"] or "").strip().lower()
            pid = (lead["place_id"] or "").strip()
            wp = (lead["whatsapp_clean"] or "").strip()
            title_norm = normalize_business_title(lead["title"])

            match_id: Optional[int] = None
            if pid and pid in seen_keys:
                match_id = seen_keys[pid]
            elif wp and len(wp) >= 10 and f"wp:{wp}|{city}" in seen_keys:
                match_id = seen_keys[f"wp:{wp}|{city}"]
            elif title_norm and len(title_norm) > 3 and f"t:{title_norm}|{city}" in seen_keys:
                match_id = seen_keys[f"t:{title_norm}|{city}"]

            if match_id is not None and match_id != lid:
                primary = conn.execute("SELECT * FROM leads WHERE id = ?", (match_id,)).fetchone()
                if primary:
                    prim_weight = (1 if primary["place_id"] else 0) + (1 if primary["category"] else 0) + (1 if primary["opportunity_score"] > 0 else 0)
                    lead_weight = (1 if lead["place_id"] else 0) + (1 if lead["category"] else 0) + (1 if lead["opportunity_score"] > 0 else 0)

                    survivor_id = match_id
                    redundant_id = lid

                    if lead_weight > prim_weight:
                        survivor_id = lid
                        redundant_id = match_id
                        if pid: seen_keys[pid] = lid
                        if wp and len(wp) >= 10: seen_keys[f"wp:{wp}|{city}"] = lid
                        if title_norm and len(title_norm) > 3: seen_keys[f"t:{title_norm}|{city}"] = lid

                    s = conn.execute("SELECT * FROM leads WHERE id = ?", (survivor_id,)).fetchone()
                    r = conn.execute("SELECT * FROM leads WHERE id = ?", (redundant_id,)).fetchone()
                    if s and r:
                        conn.execute(
                            """
                            UPDATE leads SET
                                place_id = CASE WHEN (leads.place_id IS NULL OR leads.place_id = '') THEN ? ELSE leads.place_id END,
                                category = CASE WHEN (leads.category IS NULL OR leads.category = '') THEN ? ELSE leads.category END,
                                phone = CASE WHEN (leads.phone IS NULL OR leads.phone = '') THEN ? ELSE leads.phone END,
                                whatsapp_clean = CASE WHEN (leads.whatsapp_clean IS NULL OR leads.whatsapp_clean = '') THEN ? ELSE leads.whatsapp_clean END,
                                website = CASE WHEN (leads.website IS NULL OR leads.website = '') THEN ? ELSE leads.website END,
                                review_count = MAX(leads.review_count, ?),
                                review_rating = CASE WHEN leads.review_rating <= 0 THEN ? ELSE leads.review_rating END,
                                opportunity_score = MAX(leads.opportunity_score, ?),
                                dedupe_key = CASE WHEN (leads.place_id IS NULL OR leads.place_id = '') AND ? != '' THEN ? ELSE leads.dedupe_key END
                            WHERE id = ?
                            """,
                            (
                                r["place_id"] or "",
                                r["category"] or "",
                                r["phone"] or "",
                                r["whatsapp_clean"] or "",
                                r["website"] or "",
                                r["review_count"] or 0,
                                r["review_rating"] or 0.0,
                                r["opportunity_score"] or 0,
                                r["place_id"] or "",
                                f"pid:{r['place_id']}" if r["place_id"] else s["dedupe_key"],
                                survivor_id,
                            ),
                        )
                    conn.execute("UPDATE outreach_queue SET lead_id = ? WHERE lead_id = ?", (survivor_id, redundant_id))
                    to_delete.append(redundant_id)
            else:
                if pid:
                    seen_keys[pid] = lid
                if wp and len(wp) >= 10:
                    seen_keys[f"wp:{wp}|{city}"] = lid
                if title_norm and len(title_norm) > 3:
                    seen_keys[f"t:{title_norm}|{city}"] = lid

        deleted_count = 0
        if to_delete:
            unique_to_delete = list(set(to_delete))
            placeholders = ",".join("?" for _ in unique_to_delete)
            cur = conn.execute(f"DELETE FROM leads WHERE id IN ({placeholders})", unique_to_delete)
            deleted_count = cur.rowcount

        return deleted_count


def migrate_humanized_scripts_db(db_path: Optional[str] = None) -> int:
    """
    Atualiza scripts de leads existentes que ainda usam formato antigo de mensagem (ex: 'Olá, equipe da...').
    Regenera de forma segura usando o diagnóstico técnico já gravado no banco, sem chamadas de rede.
    """
    from app.services.outreach_generator import generate_outreach_scripts

    updated = 0
    with get_connection(db_path) as conn:
        rows = conn.execute(
            """
            SELECT * FROM leads 
            WHERE outreach_scripts_json LIKE '%Olá, equipe da%' 
               OR outreach_scripts_json LIKE '%Consultoria de Desenvolvimento Web%'
               OR outreach_scripts_json IS NULL
               OR outreach_scripts_json = ''
            """
        ).fetchall()
        for r in rows:
            lead = _deserialize_lead(r)
            if not lead:
                continue
            lid = lead["id"]
            xray = lead.get("xray_raw") or {
                "has_website": lead.get("has_website", False),
                "is_social_only_url": lead.get("is_social_only_url", False),
                "site_in_air": lead.get("site_in_air", False),
                "suggested_domain": lead.get("suggested_domain", ""),
                "domain_available_br": lead.get("domain_available_br", False),
                "detected_cms": lead.get("detected_cms", "Sem Site"),
            }
            score = {
                "opportunity_score": lead.get("opportunity_score", 0),
                "primary_pain": lead.get("primary_pain", "SEM_SITE"),
                "recommended_service": lead.get("recommended_service", "SITE_NOVO"),
                "pain_summary": lead.get("pain_summary", ""),
            }
            new_scripts = generate_outreach_scripts(lead, xray, score)
            conn.execute(
                "UPDATE leads SET outreach_scripts_json = ? WHERE id = ?",
                (json.dumps(new_scripts, ensure_ascii=False), lid),
            )
            updated += 1

    return updated


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
            "SELECT COUNT(*) FROM leads WHERE lead_status IN ('contatado', 'respondeu', 'reuniao', 'fechado', 'fazendo', 'vou_fazer')"
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


# ---------------------------------------------------------------------------
# Agente WhatsApp, Consultas de Preço e Protótipos IA
# ---------------------------------------------------------------------------


def normalize_phone_digits(phone: str) -> str:
    """
    Extrai somente dígitos de um telefone ou chatid ('5519996109028@s.whatsapp.net' -> '5519996109028').
    Adiciona prefixo 55 caso venha apenas DDD + número (10 ou 11 dígitos).
    """
    base = (phone or "").split("@")[0]
    digits = re.sub(r"\D", "", base)
    if not digits:
        return ""
    if len(digits) in (10, 11) and not digits.startswith("55"):
        digits = "55" + digits
    return digits


def br_phone_variants(phone: str) -> List[str]:
    """
    Gera variantes com e sem o 9º dígito para números brasileiros (ex: 551999958516 <-> 5519999958516),
    pois o WhatsApp JID às vezes omite ou inclui o 9º dígito após o DDD.
    """
    d = normalize_phone_digits(phone)
    if not d:
        return []
    variants = [d]
    if d.startswith("55") and len(d) == 12:
        # 55 + DD (2) + 8 dígitos -> adiciona '9' após o DDD
        with_nine = d[:4] + "9" + d[4:]
        if with_nine not in variants:
            variants.append(with_nine)
    elif d.startswith("55") and len(d) == 13 and d[4] == "9":
        # 55 + DD (2) + 9 + 8 dígitos -> versão de 8 dígitos
        without_nine = d[:4] + d[5:]
        if without_nine not in variants:
            variants.append(without_nine)
    return variants


def phones_match_br(phone_a: str, phone_b: str) -> bool:
    va = set(br_phone_variants(phone_a))
    vb = set(br_phone_variants(phone_b))
    return bool(va and vb and va.intersection(vb))


def get_agent_settings(db_path: Optional[str] = None) -> Dict[str, Any]:
    with get_connection(db_path) as conn:
        row = conn.execute("SELECT * FROM agent_settings WHERE id = 1").fetchone()
        if not row:
            now = _now_iso()
            conn.execute(
                """
                INSERT OR IGNORE INTO agent_settings (
                    id, test_mode, auto_send_enabled, boss_phone, test_client_phone,
                    attendant_name, company_name, bridge_url, debounce_seconds,
                    pause_minutes_on_human, updated_at
                ) VALUES (1, 1, 0, '551999958516', '5519996109028', 'Léo', 'Estúdio Digital', 'http://127.0.0.1:3100', 6.0, 60, ?)
                """,
                (now,),
            )
            row = conn.execute("SELECT * FROM agent_settings WHERE id = 1").fetchone()
    d = dict(row)
    d["test_mode"] = bool(d.get("test_mode", 1))
    d["auto_send_enabled"] = bool(d.get("auto_send_enabled", 0))
    return d


def update_agent_settings(updates: Dict[str, Any], db_path: Optional[str] = None) -> Dict[str, Any]:
    current = get_agent_settings(db_path)
    now = _now_iso()
    test_mode = 1 if updates.get("test_mode", current["test_mode"]) else 0
    auto_send = 1 if updates.get("auto_send_enabled", current["auto_send_enabled"]) else 0
    boss_phone = normalize_phone_digits(updates.get("boss_phone") or current["boss_phone"]) or "551999958516"
    test_client_phone = (
        normalize_phone_digits(updates.get("test_client_phone") or current["test_client_phone"]) or "5519996109028"
    )
    attendant_name = (updates.get("attendant_name") or current["attendant_name"] or "Léo").strip()
    company_name = (updates.get("company_name") or current["company_name"] or "Estúdio Digital").strip()
    bridge_url = (updates.get("bridge_url") if updates.get("bridge_url") is not None else current["bridge_url"]).strip()
    uazapi_url = (updates.get("uazapi_url") if updates.get("uazapi_url") is not None else current["uazapi_url"]).strip()
    uazapi_token = (
        updates.get("uazapi_token") if updates.get("uazapi_token") is not None else current["uazapi_token"]
    ).strip()
    debounce_seconds = float(
        updates["debounce_seconds"] if updates.get("debounce_seconds") is not None else current["debounce_seconds"]
    )
    pause_minutes = int(
        updates["pause_minutes_on_human"]
        if updates.get("pause_minutes_on_human") is not None
        else current["pause_minutes_on_human"]
    )

    with get_connection(db_path) as conn:
        conn.execute(
            """
            UPDATE agent_settings SET
                test_mode = ?,
                auto_send_enabled = ?,
                boss_phone = ?,
                test_client_phone = ?,
                attendant_name = ?,
                company_name = ?,
                bridge_url = ?,
                uazapi_url = ?,
                uazapi_token = ?,
                debounce_seconds = ?,
                pause_minutes_on_human = ?,
                updated_at = ?
            WHERE id = 1
            """,
            (
                test_mode,
                auto_send,
                boss_phone,
                test_client_phone,
                attendant_name,
                company_name,
                bridge_url,
                uazapi_url,
                uazapi_token,
                debounce_seconds,
                pause_minutes,
                now,
            ),
        )
    return get_agent_settings(db_path)


def _deserialize_conversation(row: Optional[sqlite3.Row]) -> Optional[Dict[str, Any]]:
    if not row:
        return None
    d = dict(row)
    d["is_test_session"] = bool(d.get("is_test_session", 1))
    d["collected_requirements"] = json.loads(d.pop("collected_requirements_json", "{}") or "{}")
    return d


def create_or_activate_agent_conversation(
    lead_id: int,
    chatid: str,
    real_lead_phone: str = "",
    queue_id: Optional[int] = None,
    is_test_session: bool = True,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    now = _now_iso()
    clean_chat = normalize_phone_digits(chatid)
    clean_real = normalize_phone_digits(real_lead_phone)

    with get_connection(db_path) as conn:
        # Se for sessão de teste e já houver outra conversa ativa no mesmo número de teste para outro lead,
        # arquiva as anteriores para que a resposta do número de teste vá para o lead recém-confirmado.
        if is_test_session:
            variants = br_phone_variants(clean_chat)
            if variants:
                ph = ",".join("?" for _ in variants)
                conn.execute(
                    f"""
                    UPDATE agent_conversations
                    SET status = 'superseded', updated_at = ?
                    WHERE chatid IN ({ph}) AND lead_id != ? AND status IN ('active', 'waiting_boss_price')
                    """,
                    [now, *variants, lead_id],
                )

        existing = conn.execute(
            """
            SELECT * FROM agent_conversations
            WHERE lead_id = ? AND chatid = ?
            ORDER BY id DESC LIMIT 1
            """,
            (lead_id, clean_chat),
        ).fetchone()

        if existing:
            cid = int(existing["id"])
            conn.execute(
                """
                UPDATE agent_conversations SET
                    queue_id = COALESCE(?, queue_id),
                    real_lead_phone = COALESCE(NULLIF(?, ''), real_lead_phone),
                    is_test_session = ?,
                    status = 'active',
                    paused_until = NULL,
                    pause_reason = '',
                    updated_at = ?
                WHERE id = ?
                """,
                (queue_id, clean_real, 1 if is_test_session else 0, now, cid),
            )
        else:
            cur = conn.execute(
                """
                INSERT INTO agent_conversations (
                    lead_id, queue_id, chatid, real_lead_phone, is_test_session,
                    status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, 'active', ?, ?)
                """,
                (lead_id, queue_id, clean_chat, clean_real, 1 if is_test_session else 0, now, now),
            )
            cid = int(cur.lastrowid)

        row = conn.execute(
            """
            SELECT c.*, l.title AS lead_title, l.city AS lead_city, l.niche_slug AS lead_niche,
                   l.primary_pain AS lead_pain, l.recommended_service AS lead_service
            FROM agent_conversations c
            LEFT JOIN leads l ON l.id = c.lead_id
            WHERE c.id = ?
            """,
            (cid,),
        ).fetchone()
    return _deserialize_conversation(row) or {}


def get_agent_conversation(conversation_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    with get_connection(db_path) as conn:
        row = conn.execute(
            """
            SELECT c.*, l.title AS lead_title, l.city AS lead_city, l.niche_slug AS lead_niche,
                   l.primary_pain AS lead_pain, l.recommended_service AS lead_service
            FROM agent_conversations c
            LEFT JOIN leads l ON l.id = c.lead_id
            WHERE c.id = ?
            """,
            (conversation_id,),
        ).fetchone()
    return _deserialize_conversation(row)


def get_active_conversation_by_chatid(chatid: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    variants = br_phone_variants(chatid)
    if not variants:
        return None
    ph = ",".join("?" for _ in variants)
    with get_connection(db_path) as conn:
        row = conn.execute(
            f"""
            SELECT c.*, l.title AS lead_title, l.city AS lead_city, l.niche_slug AS lead_niche,
                   l.primary_pain AS lead_pain, l.recommended_service AS lead_service
            FROM agent_conversations c
            LEFT JOIN leads l ON l.id = c.lead_id
            WHERE c.chatid IN ({ph})
              AND c.status != 'superseded'
            ORDER BY c.updated_at DESC, c.id DESC
            LIMIT 1
            """,
            variants,
        ).fetchone()
    return _deserialize_conversation(row)


def list_agent_conversations(limit: int = 50, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    with get_connection(db_path) as conn:
        rows = conn.execute(
            """
            SELECT c.*, l.title AS lead_title, l.city AS lead_city, l.niche_slug AS lead_niche,
                   l.primary_pain AS lead_pain, l.recommended_service AS lead_service
            FROM agent_conversations c
            LEFT JOIN leads l ON l.id = c.lead_id
            ORDER BY c.updated_at DESC, c.id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [_deserialize_conversation(r) for r in rows if r]


def update_agent_conversation(
    conversation_id: int,
    status: Optional[str] = None,
    paused_until: Optional[str] = "__KEEP__",
    pause_reason: Optional[str] = None,
    collected_requirements: Optional[Dict[str, Any]] = None,
    suggested_price_cents: Optional[int] = None,
    approved_price_text: Optional[str] = None,
    increment_turn: bool = False,
    db_path: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    current = get_agent_conversation(conversation_id, db_path)
    if not current:
        return None
    now = _now_iso()
    merged_reqs = dict(current.get("collected_requirements") or {})
    if collected_requirements:
        for k, v in collected_requirements.items():
            if v is not None and str(v).strip() != "":
                merged_reqs[k] = v

    new_status = status if status is not None else current["status"]
    new_paused_until = current.get("paused_until") if paused_until == "__KEEP__" else paused_until
    new_pause_reason = pause_reason if pause_reason is not None else current.get("pause_reason", "")
    new_price = (
        suggested_price_cents if suggested_price_cents is not None else current.get("suggested_price_cents", 0)
    )
    new_approved = (
        approved_price_text if approved_price_text is not None else current.get("approved_price_text", "")
    )
    new_turn = int(current.get("turn_version", 0)) + (1 if increment_turn else 0)

    with get_connection(db_path) as conn:
        conn.execute(
            """
            UPDATE agent_conversations SET
                status = ?,
                paused_until = ?,
                pause_reason = ?,
                collected_requirements_json = ?,
                suggested_price_cents = ?,
                approved_price_text = ?,
                turn_version = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                new_status,
                new_paused_until,
                new_pause_reason,
                json.dumps(merged_reqs, ensure_ascii=False),
                new_price,
                new_approved,
                new_turn,
                now,
                conversation_id,
            ),
        )
    return get_agent_conversation(conversation_id, db_path)


def append_agent_message(
    conversation_id: int,
    role: str,
    content: str,
    direction: str = "inbound",
    external_message_id: str = "",
    tool_calls: Optional[List[Dict[str, Any]]] = None,
    db_path: Optional[str] = None,
) -> int:
    now = _now_iso()
    with get_connection(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO agent_messages (
                conversation_id, role, direction, content,
                external_message_id, tool_calls_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                conversation_id,
                role,
                direction,
                content,
                external_message_id or "",
                json.dumps(tool_calls or [], ensure_ascii=False),
                now,
            ),
        )
        conn.execute(
            "UPDATE agent_conversations SET updated_at = ? WHERE id = ?",
            (now, conversation_id),
        )
        return int(cur.lastrowid)


def list_agent_messages(conversation_id: int, limit: int = 100, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    with get_connection(db_path) as conn:
        rows = conn.execute(
            """
            SELECT * FROM agent_messages
            WHERE conversation_id = ?
            ORDER BY id ASC
            LIMIT ?
            """,
            (conversation_id, limit),
        ).fetchall()
    result = []
    for r in rows:
        d = dict(r)
        d["tool_calls"] = json.loads(d.pop("tool_calls_json", "[]") or "[]")
        result.append(d)
    return result


def delete_agent_messages_after(conversation_id: int, max_message_id: int, db_path: Optional[str] = None) -> int:
    """Usado por desfazerTurno (anti-resposta-velha) para apagar mensagens geradas em um turno descartado."""
    with get_connection(db_path) as conn:
        cur = conn.execute(
            "DELETE FROM agent_messages WHERE conversation_id = ? AND id > ?",
            (conversation_id, max_message_id),
        )
        return int(cur.rowcount)


def create_price_consultation(
    conversation_id: int,
    lead_id: int,
    client_summary: str,
    scope_type: str,
    suggested_price_cents: int,
    price_range_text: str,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    now = _now_iso()
    with get_connection(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO price_consultations (
                conversation_id, lead_id, client_summary, scope_type,
                suggested_price_cents, price_range_text, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)
            """,
            (conversation_id, lead_id, client_summary, scope_type, suggested_price_cents, price_range_text, now),
        )
        cid = int(cur.lastrowid)
        row = conn.execute(
            """
            SELECT p.*, l.title AS lead_title, l.city AS lead_city
            FROM price_consultations p
            LEFT JOIN leads l ON l.id = p.lead_id
            WHERE p.id = ?
            """,
            (cid,),
        ).fetchone()
    return dict(row) if row else {}


def get_pending_price_consultation(
    consultation_id: Optional[int] = None,
    lead_id: Optional[int] = None,
    db_path: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    with get_connection(db_path) as conn:
        if consultation_id is not None:
            row = conn.execute(
                """
                SELECT p.*, l.title AS lead_title, l.city AS lead_city
                FROM price_consultations p
                LEFT JOIN leads l ON l.id = p.lead_id
                WHERE p.id = ?
                """,
                (consultation_id,),
            ).fetchone()
            if row:
                return dict(row)
        if lead_id is not None:
            row = conn.execute(
                """
                SELECT p.*, l.title AS lead_title, l.city AS lead_city
                FROM price_consultations p
                LEFT JOIN leads l ON l.id = p.lead_id
                WHERE p.lead_id = ? AND p.status = 'pending'
                ORDER BY p.id DESC LIMIT 1
                """,
                (lead_id,),
            ).fetchone()
            if row:
                return dict(row)
        row = conn.execute(
            """
            SELECT p.*, l.title AS lead_title, l.city AS lead_city
            FROM price_consultations p
            LEFT JOIN leads l ON l.id = p.lead_id
            WHERE p.status = 'pending'
            ORDER BY p.id DESC LIMIT 1
            """
        ).fetchone()
    return dict(row) if row else None


def resolve_price_consultation(
    consultation_id: int,
    boss_reply_text: str,
    db_path: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    now = _now_iso()
    with get_connection(db_path) as conn:
        conn.execute(
            """
            UPDATE price_consultations
            SET status = 'approved', boss_reply_text = ?, responded_at = ?
            WHERE id = ?
            """,
            (boss_reply_text.strip(), now, consultation_id),
        )
        row = conn.execute(
            """
            SELECT p.*, l.title AS lead_title, l.city AS lead_city
            FROM price_consultations p
            LEFT JOIN leads l ON l.id = p.lead_id
            WHERE p.id = ?
            """,
            (consultation_id,),
        ).fetchone()
    return dict(row) if row else None


def list_price_consultations(limit: int = 30, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    with get_connection(db_path) as conn:
        rows = conn.execute(
            """
            SELECT p.*, l.title AS lead_title, l.city AS lead_city
            FROM price_consultations p
            LEFT JOIN leads l ON l.id = p.lead_id
            ORDER BY p.id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows if r]


def save_lead_prototype(
    lead_id: int,
    scope_type: str,
    briefing: Dict[str, Any],
    html_content: str,
    output_path: str,
    ai_provider_used: str,
    conversation_id: Optional[int] = None,
    status: str = "ready",
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    now = _now_iso()
    with get_connection(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO lead_prototypes (
                lead_id, conversation_id, scope_type, briefing_json,
                html_content, output_path, ai_provider_used, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                lead_id,
                conversation_id,
                scope_type,
                json.dumps(briefing or {}, ensure_ascii=False),
                html_content,
                output_path,
                ai_provider_used,
                status,
                now,
                now,
            ),
        )
        pid = int(cur.lastrowid)
        row = conn.execute(
            """
            SELECT pr.*, l.title AS lead_title, l.city AS lead_city
            FROM lead_prototypes pr
            LEFT JOIN leads l ON l.id = pr.lead_id
            WHERE pr.id = ?
            """,
            (pid,),
        ).fetchone()
    d = dict(row) if row else {}
    if d:
        d["briefing"] = json.loads(d.pop("briefing_json", "{}") or "{}")
    return d


def get_latest_lead_prototype(lead_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    with get_connection(db_path) as conn:
        row = conn.execute(
            """
            SELECT pr.*, l.title AS lead_title, l.city AS lead_city
            FROM lead_prototypes pr
            LEFT JOIN leads l ON l.id = pr.lead_id
            WHERE pr.lead_id = ?
            ORDER BY pr.id DESC LIMIT 1
            """,
            (lead_id,),
        ).fetchone()
    if not row:
        return None
    d = dict(row)
    d["briefing"] = json.loads(d.pop("briefing_json", "{}") or "{}")
    return d


def list_lead_prototypes(limit: int = 30, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    with get_connection(db_path) as conn:
        rows = conn.execute(
            """
            SELECT pr.id, pr.lead_id, pr.conversation_id, pr.scope_type, pr.briefing_json,
                   pr.output_path, pr.ai_provider_used, pr.status, pr.created_at, pr.updated_at,
                   l.title AS lead_title, l.city AS lead_city
            FROM lead_prototypes pr
            LEFT JOIN leads l ON l.id = pr.lead_id
            ORDER BY pr.id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    result = []
    for r in rows:
        d = dict(r)
        d["briefing"] = json.loads(d.pop("briefing_json", "{}") or "{}")
        result.append(d)
    return result

