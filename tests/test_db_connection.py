import psycopg2

from cybernetics.db_interface.postgres import PostgresClient


def test_postgres_connection():
    host = "localhost"
    port = 5432
    user = "postgres"
    password = "12345"
    db_name = "postgres"

    # Connect to Postgres
    version_sql = "SELECT version();"
    try:
        conn = psycopg2.connect(host=host, port=port, user=user, password=password, dbname=db_name)
        print("\n    Connected to Postgres.")

        with conn.cursor() as cursor:
            cursor.execute(version_sql)
            postgres_version = cursor.fetchone()[0].split(" ")[1]
            assert(float(postgres_version) >= 6.3) # 6.3 was introduced in 1998

        conn.close()
    except:
        print("\n    Unable to connect to the database.")
    
    pg_client = PostgresClient(host, port, user, password, db_name)
    print("    Connected to Postgres.")
    
    postgres_version = pg_client.execute_and_fetch_results(version_sql, json=False)[0][0].split(" ")[1]
    assert(float(postgres_version) >= 6.3)

    pg_client.close_connection()
