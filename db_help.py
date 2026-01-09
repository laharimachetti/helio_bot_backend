import pymysql # type: ignore
import os

def get_db():
    return pymysql.connect(
        host=os.environ.get("MYSQLHOST"),
        user=os.environ.get("MYSQLUSER"),
        password=os.environ.get("MYSQLPASSWORD"),
        database=os.environ.get("MYSQLDATABASE"),
        port=int(os.environ.get("MYSQLPORT", 3306)),
        cursorclass=pymysql.cursors.DictCursor
    )

def fetch_cutoffs_all_years(branch, rank, limit=20):
    if rank is None or not branch:
        return []

    db = get_db()
    try:
        with db.cursor() as cur:
            query = """
                SELECT institute, academic_program, MIN(closing_rank) AS best_rank
                FROM cutoff_ranks
                WHERE academic_program LIKE %s
                  AND closing_rank >= %s
                GROUP BY institute, academic_program
                ORDER BY best_rank
                LIMIT %s;
            """
            cur.execute(query, (f"%{branch}%", rank, limit))
            results = cur.fetchall()
            return results
    finally:
        db.close()
