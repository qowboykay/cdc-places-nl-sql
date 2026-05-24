from __future__ import annotations

import click
from dotenv import load_dotenv

from cdc_places_nl_sql.executor import run_query
from cdc_places_nl_sql.llm import generate_sql, summarize_results
from cdc_places_nl_sql.schema import get_schema_description
from cdc_places_nl_sql.validator import UnsafeSQLError, validate_and_cap

load_dotenv()


@click.group()
def cli() -> None:
    """CDC PLACES natural-language SQL assistant."""


@cli.command()
@click.argument("question")
@click.option("--show-sql", is_flag=True, default=False, help="Print the SQL query.")
def ask(question: str, show_sql: bool) -> None:
    """Ask a plain-English question about CDC PLACES health data."""
    click.echo("Fetching schema...")
    schema = get_schema_description()

    click.echo("Generating SQL...")
    raw_sql = generate_sql(question, schema)

    try:
        safe_sql = validate_and_cap(raw_sql)
    except UnsafeSQLError as exc:
        raise click.ClickException(f"Unsafe SQL rejected: {exc}") from exc

    if show_sql:
        click.echo(f"\nSQL:\n{safe_sql}\n")

    click.echo("Running query...")
    df = run_query(safe_sql)

    if df.empty:
        click.echo("Query returned no results.")
        return

    click.echo(f"\nResults ({len(df)} rows):")
    click.echo(df.to_string(index=False))

    click.echo("\nSummary:")
    summary = summarize_results(question, df)
    click.echo(summary)


if __name__ == "__main__":
    cli()
