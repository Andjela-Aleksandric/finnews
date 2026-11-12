"""SQLite skladište: vesti, prevodi, dnevni briefovi, status izvora."""
import os
import sqlite3
from pathlib import Path

DATA_DIR = Path(os.environ.get(
    "FINNEWS_DATA", Path.home() / "Library" / "Application Support" / "FinNews"))
DB_PATH = DATA_DIR / "news.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS items(
    id TEXT PRIMARY KEY,
    source TEXT, category TEXT, lang TEXT,
    title TEXT, link TEXT, summary TEXT,
    published TEXT, fetched_at TEXT,
    score REAL DEFAULT 0, starred INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_items_pub ON items(published);
CREATE INDEX IF NOT EXISTS idx_items_cat ON items(category);
CREATE TABLE IF NOT EXISTS translations(
    item_id TEXT, lang TEXT, title TEXT, summary TEXT,
    PRIMARY KEY(item_id, lang)
);
CREATE TABLE IF NOT EXISTS briefs(
    day TEXT, lang TEXT, content TEXT, created_at TEXT,
    PRIMARY KEY(day, lang)
);
CREATE TABLE IF NOT EXISTS fetch_log(
    source TEXT PRIMARY KEY, last_ok TEXT, last_error TEXT, last_count INTEGER
);
CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS papers(
    id TEXT PRIMARY KEY, title TEXT, authors TEXT, venue TEXT, pub_date TEXT,
    year INTEGER, cited_by INTEGER, link TEXT, abstract TEXT, fetched_at TEXT
);
CREATE TABLE IF NOT EXISTS paper_tags(paper_id TEXT, tag TEXT, PRIMARY KEY(paper_id, tag));
CREATE TABLE IF NOT EXISTS phd(paper_id TEXT, topic TEXT, score REAL, PRIMARY KEY(paper_id, topic));
CREATE TABLE IF NOT EXISTS phd_trends(topic TEXT PRIMARY KEY, recent INTEGER, prev INTEGER, updated TEXT);
CREATE TABLE IF NOT EXISTS articles(item_id TEXT PRIMARY KEY, url TEXT, text TEXT, status TEXT, fetched_at TEXT);
CREATE TABLE IF NOT EXISTS article_ai(item_id TEXT, lang TEXT, kind TEXT, content TEXT,
    PRIMARY KEY(item_id, lang, kind));
"""


def connect():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)
    con.row_factory = sqlite3.Row
    try:  # brži upisi i čitanje dok pozadinsko osvežavanje radi
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA synchronous=NORMAL")
        con.execute("PRAGMA temp_store=MEMORY")
        con.execute("PRAGMA cache_size=-20000")
    except sqlite3.OperationalError:
        pass
    con.executescript(SCHEMA)
    for idx in ("CREATE INDEX IF NOT EXISTS idx_items_score ON items(score)",
                "CREATE INDEX IF NOT EXISTS idx_items_cat_pub ON items(category, published)",
                "CREATE INDEX IF NOT EXISTS idx_items_ticker ON items(ticker)",
                "CREATE INDEX IF NOT EXISTS idx_articles_status ON articles(status)"):
        try:
            con.execute(idx)
        except sqlite3.OperationalError:
            pass
    for col in ("pdf_url TEXT", "oa INTEGER DEFAULT 0"):  # nove kolone za starije baze
        try:
            con.execute(f"ALTER TABLE papers ADD COLUMN {col}")
        except sqlite3.OperationalError:
            pass
    return con


def get_meta(con, key, default=None):
    row = con.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
    return row["value"] if row else default


def set_meta(con, key, value):
    con.execute("INSERT OR REPLACE INTO meta(key, value) VALUES(?, ?)", (key, value))
    con.commit()


def query_items(con, start_iso=None, end_iso=None, categories=None, exclude_categories=None,
                sources=None, search=None, starred_only=False, order="score", limit=200):
    sql, args = "SELECT * FROM items WHERE 1=1", []
    if start_iso:
        sql += " AND published >= ?"; args.append(start_iso)
    if end_iso:
        sql += " AND published < ?"; args.append(end_iso)
    if categories:
        sql += f" AND category IN ({','.join('?' * len(categories))})"; args += list(categories)
    if exclude_categories:
        sql += f" AND category NOT IN ({','.join('?' * len(exclude_categories))})"; args += list(exclude_categories)
    if sources:
        sql += f" AND source IN ({','.join('?' * len(sources))})"; args += list(sources)
    if search:
        like = f"%{search}%"
        sql += (" AND (title LIKE ? OR summary LIKE ? OR id IN "
                "(SELECT item_id FROM translations WHERE title LIKE ? OR summary LIKE ?))")
        args += [like, like, like, like]
    if starred_only:
        sql += " AND starred = 1"
    sql += " ORDER BY score DESC, published DESC" if order == "score" else " ORDER BY published DESC"
    sql += " LIMIT ?"; args.append(limit)
    return [dict(r) for r in con.execute(sql, args).fetchall()]


def all_sources(con):
    return [r["source"] for r in con.execute("SELECT DISTINCT source FROM items ORDER BY source")]


def toggle_star(con, item_id):
    con.execute("UPDATE items SET starred = 1 - starred WHERE id=?", (item_id,))
    con.commit()


def get_translations(con, ids, lang):
    if not ids:
        return {}
    rows = con.execute(
        f"SELECT * FROM translations WHERE lang=? AND item_id IN ({','.join('?' * len(ids))})",
        [lang, *ids]).fetchall()
    return {r["item_id"]: {"title": r["title"], "summary": r["summary"]} for r in rows}


def save_translation(con, item_id, lang, title, summary):
    con.execute("INSERT OR REPLACE INTO translations VALUES(?,?,?,?)", (item_id, lang, title, summary))
    con.commit()


def get_brief(con, day, lang):
    row = con.execute("SELECT * FROM briefs WHERE day=? AND lang=?", (day, lang)).fetchone()
    return dict(row) if row else None


def save_brief(con, day, lang, content, created_at):
    con.execute("INSERT OR REPLACE INTO briefs VALUES(?,?,?,?)", (day, lang, content, created_at))
    con.commit()


def brief_days(con):
    return [r["day"] for r in con.execute("SELECT DISTINCT day FROM briefs ORDER BY day DESC")]


def fetch_log(con):
    return [dict(r) for r in con.execute("SELECT * FROM fetch_log ORDER BY source")]


def stats(con):
    row = con.execute("SELECT COUNT(*) n, MIN(published) first FROM items").fetchone()
    return dict(row)


def upsert_paper(con, p, tag):
    con.execute("INSERT OR REPLACE INTO papers(id, title, authors, venue, pub_date, year, cited_by, link, abstract, "
                "fetched_at, pdf_url, oa) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                (p["id"], p["title"], p["authors"], p["venue"], p["pub_date"], p["year"], p["cited_by"], p["link"],
                 p["abstract"], p["fetched_at"], p.get("pdf_url"), int(bool(p.get("oa")))))
    con.execute("INSERT OR IGNORE INTO paper_tags VALUES(?,?)", (p["id"], tag))


def clear_tag(con, tag):
    con.execute("DELETE FROM paper_tags WHERE tag=?", (tag,))


def papers_by_tag(con, tag, search=None, order="cited", limit=100):
    sql = ("SELECT p.* FROM papers p JOIN paper_tags t ON t.paper_id = p.id WHERE t.tag = ?")
    args = [tag]
    if search:
        like = f"%{search}%"
        sql += " AND (p.title LIKE ? OR p.abstract LIKE ? OR p.venue LIKE ?)"
        args += [like, like, like]
    sql += " ORDER BY p.cited_by DESC" if order == "cited" else " ORDER BY p.pub_date DESC"
    sql += " LIMIT ?"; args.append(limit)
    return [dict(r) for r in con.execute(sql, args)]


def get_article(con, item_id):
    row = con.execute("SELECT * FROM articles WHERE item_id=?", (item_id,)).fetchone()
    return dict(row) if row else None


def save_article(con, item_id, url, text, status, fetched_at):
    con.execute("INSERT OR REPLACE INTO articles VALUES(?,?,?,?,?)", (item_id, url, text, status, fetched_at))
    con.commit()


def get_article_ai(con, item_id, lang, kind):
    row = con.execute("SELECT content FROM article_ai WHERE item_id=? AND lang=? AND kind=?",
                      (item_id, lang, kind)).fetchone()
    return row["content"] if row else None


def save_article_ai(con, item_id, lang, kind, content):
    con.execute("INSERT OR REPLACE INTO article_ai VALUES(?,?,?,?)", (item_id, lang, kind, content))
    con.commit()


def phd_papers(con, topic=None, search=None, saved_only=False, limit=60):
    sql = ("SELECT p.*, MAX(x.score) AS phd_score, GROUP_CONCAT(x.topic, '|') AS topics FROM papers p "
           "JOIN phd x ON x.paper_id = p.id WHERE 1=1")
    args = []
    if topic:
        sql += " AND p.id IN (SELECT paper_id FROM phd WHERE topic = ?)"; args.append(topic)
    if search:
        sql += " AND (p.title LIKE ? OR p.abstract LIKE ?)"; args += [f"%{search}%"] * 2
    if saved_only:
        sql += " AND p.id IN (SELECT paper_id FROM paper_tags WHERE tag = 'phd_saved')"
    sql += " GROUP BY p.id ORDER BY phd_score DESC LIMIT ?"; args.append(limit)
    return [dict(r) for r in con.execute(sql, args)]


def saved_paper_ids(con):
    return {r["paper_id"] for r in con.execute("SELECT paper_id FROM paper_tags WHERE tag='phd_saved'")}


def toggle_paper_saved(con, pid):
    if pid in saved_paper_ids(con):
        con.execute("DELETE FROM paper_tags WHERE paper_id=? AND tag='phd_saved'", (pid,))
    else:
        con.execute("INSERT OR IGNORE INTO paper_tags VALUES(?, 'phd_saved')", (pid,))
    con.commit()
