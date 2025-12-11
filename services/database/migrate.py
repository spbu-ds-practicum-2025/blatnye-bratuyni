import psycopg2
from config import DATABASE_URL

def run_sql_file(filename):
    with open(filename, encoding='utf-8') as f:
        sql = f.read()
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute(sql)
    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: migrate.py <sqlfile>")
    else:
        run_sql_file(sys.argv[1])