import argparse
import json

from cybernetics.db_interface.postgres import PostgresClient


SELECTED_KNOB_LOGICAL_GROUPS = []


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    
    arg_parser.add_argument("--host", type=str, default="localhost", help="Host name")
    arg_parser.add_argument("--port", type=int, default=5432, help="Port number")
    arg_parser.add_argument("--user", type=str, default="postgres", help="User name")
    arg_parser.add_argument("--password", type=str, default="12345", help="Password")
    arg_parser.add_argument("--db_name", type=str, default="postgres", help="Database name")

    args = arg_parser.parse_args()

    # Connect to Postgres
    pg_client = PostgresClient(args.host, args.port, args.user, args.password, args.db_name)

    # Retrieve database version
    version_sql = "SELECT version();"
    db_version = pg_client.fetch_results(version_sql, json=False)[0][0].split(" ")[1]

    # Specify output file paths
    stats_filepath = f"./postgres_{db_version}_stats.json"
    all_knobs_filepath = f"./postgres_{db_version}_all_knobs.json"
    selected_knobs_filepath = f"./postgres_{db_version}_selected_knobs.json"

    # https://www.postgresql.org/docs/current/view-pg-settings.html
    knob_sql = "SELECT name, setting, unit, category, short_desc, extra_desc, context, vartype, source, min_val, max_val, enumvals, boot_val, reset_val FROM pg_settings;"

    all_knobs_info = pg_client.fetch_results(knob_sql)

    with open(all_knobs_filepath, "w") as ak_f:
        json.dump(all_knobs_info, ak_f, indent=4)

    logical_groups = {}
    for knob_spec in all_knobs_info:
        if knob_spec["category"] not in logical_groups:
            logical_groups[knob_spec["category"]] = 1
        else:
            logical_groups[knob_spec["category"]] += 1

    logical_groups = {k: v for k, v in sorted(logical_groups.items(), key=lambda item: item[1], reverse=True)}

    stats = {
        "Number of knobs": len(all_knobs_info),
        "Number of logical groups": len(logical_groups)
    }

    with open(stats_filepath, "w") as stats_f:
        json.dump([stats, logical_groups], stats_f, indent=4)
