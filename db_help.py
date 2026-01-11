import pymysql # type: ignore
import os

def get_db():
    try:
        # Fetching and cleaning variables
        # .strip() is critical to remove that newline seen in your screenshot
        host = os.environ.get("MYSQLHOST", "").strip()
        user = os.environ.get("MYSQLUSER", "").strip()
        password = os.environ.get("MYSQLPASSWORD", "").strip()
        database = os.environ.get("MYSQLDATABASE", "").strip()
        
        # Safe integer conversion for the port
        port_env = os.environ.get("MYSQLPORT", "3306").strip()
        port = int(port_env) 

        # This will show up in your Railway logs to help you verify the host
        print(f"DEBUG: Connecting to host: {host} on port: {port}")

        return pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            port=port,
            connect_timeout=10,
            cursorclass=pymysql.cursors.DictCursor
        )
    except Exception as e:
        print(f"DATABASE CONNECTION ERROR: {e}")
        raise e

def fetch_cutoffs_all_years(branch, rank, limit=20):
    if rank is None or not branch:
        return []

    db = None
    try:
        db = get_db()
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
            return cur.fetchall()
    finally:
        if db:
            db.close()