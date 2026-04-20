"""
MMF Platform CLI — v0.7.2
Production-grade CLI using Click for structured commands.
Commands: serve, validate, stats, rollback, test-query, build
"""
import os
import sys
import json
import click

# Resolve backend scope natively
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MMF_DEV = os.path.join(BASE_DIR, 'mmf_dev')
MMF_ZIP = os.path.join(BASE_DIR, 'assistant.mmf')


def _get_runtime():
    """Creates and initializes a runtime instance."""
    from mmf.loader import MMFLoader
    from mmf.matcher import TfidfMatcher
    from mmf.runtime import MMFRuntime

    target = MMF_ZIP if os.path.exists(MMF_ZIP) else MMF_DEV
    loader = MMFLoader(directory_path=target)
    matcher = TfidfMatcher()
    runtime = MMFRuntime(loader=loader, matcher=matcher)
    runtime.initialize()
    return runtime


@click.group()
@click.version_option(version="0.7.2", prog_name="MMF Platform")
def cli():
    """MMF Platform — Deterministic High-Precision Retrieval Engine CLI."""
    pass


@cli.command()
@click.option('--host', default='0.0.0.0', help='Host to bind to.')
@click.option('--port', default=5000, type=int, help='Port to serve on.')
@click.option('--debug', is_flag=True, default=False, help='Enable debug mode.')
def serve(host, port, debug):
    """Start the MMF web server."""
    from app import create_app
    app = create_app()
    click.echo(f"🚀 MMF Platform starting on {host}:{port} (debug={debug})")
    app.run(host=host, port=port, debug=debug)


@cli.command()
def validate():
    """Validate the knowledge base for corruption or structural issues."""
    from mmf.learner import MMFLearner

    click.echo("🔍 Validating knowledge base...")
    learner = MMFLearner(MMF_DEV)
    result = learner.validate_knowledge()

    if result["valid"]:
        click.secho(f"✅ Knowledge base is valid. ({result['entry_count']} entries)", fg="green")
    else:
        click.secho(f"❌ Knowledge base has {len(result['errors'])} error(s):", fg="red")
        for err in result["errors"]:
            click.echo(f"   • {err}")

    return result["valid"]


@cli.command()
def stats():
    """Display system statistics and knowledge base info."""
    click.echo("📊 MMF Platform Statistics")
    click.echo("=" * 40)

    # Knowledge stats
    k_path = os.path.join(MMF_DEV, 'knowledge.json')
    if os.path.exists(k_path):
        with open(k_path, 'r', encoding='utf-8') as f:
            knowledge = json.load(f)

        total = len(knowledge)
        sources = {}
        tags_count = 0
        for item in knowledge:
            src = item.get("source", "unknown")
            sources[src] = sources.get(src, 0) + 1
            tags_count += len(item.get("tags", []))

        click.echo(f"  Total Entries:    {total}")
        click.echo(f"  Total Tags:       {tags_count}")
        click.echo(f"  Avg Tags/Entry:   {tags_count / total:.1f}" if total > 0 else "  Avg Tags/Entry:   0")
        click.echo(f"  Sources:")
        for src, count in sorted(sources.items(), key=lambda x: -x[1]):
            click.echo(f"    {src}: {count}")
    else:
        click.secho("  ⚠ knowledge.json not found.", fg="yellow")

    # File sizes
    click.echo(f"\n  Knowledge File:   {os.path.getsize(k_path) / 1024:.1f} KB" if os.path.exists(k_path) else "")
    if os.path.exists(MMF_ZIP):
        click.echo(f"  MMF Archive:      {os.path.getsize(MMF_ZIP) / 1024:.1f} KB")

    # Backup info
    backup_dir = os.path.join(MMF_DEV, 'backups')
    if os.path.exists(backup_dir):
        backups = [f for f in os.listdir(backup_dir) if f.startswith('knowledge_')]
        click.echo(f"  Backups:          {len(backups)}")
    else:
        click.echo("  Backups:          0")


@cli.command()
@click.option('--version', 'version_name', required=True, help='Backup filename to restore (e.g. knowledge_20260420_120000.json)')
def rollback(version_name):
    """Restore knowledge base from a backup version."""
    from mmf.learner import MMFLearner

    learner = MMFLearner(MMF_DEV)
    versions = learner.get_versions()

    if not versions:
        click.secho("❌ No backup versions available.", fg="red")
        return

    click.echo(f"📋 Available versions:")
    for v in versions:
        marker = " ← target" if v["filename"] == version_name else ""
        click.echo(f"   {v['filename']} ({v['size_bytes'] / 1024:.1f} KB, {v['modified']}){marker}")

    if not any(v["filename"] == version_name for v in versions):
        click.secho(f"❌ Version '{version_name}' not found.", fg="red")
        return

    if click.confirm(f"⚠ This will replace the current knowledge base with '{version_name}'. Continue?"):
        try:
            learner.rollback(version_name)
            click.secho(f"✅ Successfully rolled back to {version_name}", fg="green")
        except Exception as e:
            click.secho(f"❌ Rollback failed: {str(e)}", fg="red")


@cli.command('test-query')
@click.argument('query')
@click.option('--debug', is_flag=True, default=False, help='Show debug scoring details.')
def test_query(query, debug):
    """Test a query against the retrieval engine and show debug output."""
    click.echo(f"🔎 Testing query: \"{query}\"")
    click.echo("-" * 50)

    try:
        runtime = _get_runtime()
        result = runtime.query(query, debug=debug)

        if result["type"] == "match":
            click.secho(f"✅ Match found!", fg="green")
            click.echo(f"   Score:     {result.get('final_score', 0):.4f}")
            click.echo(f"   Similarity: {result.get('similarity', 0):.4f}")
            click.echo(f"   Matched:   {result.get('matching_query', 'N/A')}")
            click.echo(f"   Chunks:    {result.get('chunks_used', 0)}")
            click.echo(f"   Source:    {result.get('source', 'N/A')}")
            click.echo(f"\n📝 Response:")
            click.echo(result.get("response", ""))
        else:
            click.secho(f"❌ No match found.", fg="red")
            click.echo(f"   Message: {result.get('message', 'N/A')}")

    except Exception as e:
        click.secho(f"❌ Error: {str(e)}", fg="red")


@cli.command()
def build():
    """Rebuild the .mmf archive from mmf_dev."""
    from mmf.builder import build_mmf

    click.echo("🔨 Building MMF archive...")
    try:
        build_mmf(MMF_DEV, BASE_DIR, "assistant.mmf")
        size = os.path.getsize(MMF_ZIP) / 1024
        click.secho(f"✅ Built successfully: assistant.mmf ({size:.1f} KB)", fg="green")
    except Exception as e:
        click.secho(f"❌ Build failed: {str(e)}", fg="red")


@cli.command()
def interactive():
    """Start an interactive chat session in the terminal."""
    click.echo("💬 MMF Interactive Chat (type 'exit' or 'quit' to stop)")
    click.echo("=" * 50)

    try:
        runtime = _get_runtime()
        click.echo(f"Loaded: {runtime.manifest.get('name', 'MMF')} v{runtime.manifest.get('version', '?')}\n")
    except Exception as e:
        click.secho(f"❌ Failed to initialize: {str(e)}", fg="red")
        return

    from mmf.learner import MMFLearner
    learner = MMFLearner(MMF_DEV)

    while True:
        try:
            q = click.prompt("You", prompt_suffix="> ").strip()
            if not q:
                continue
            if q.lower() in ['quit', 'exit']:
                click.echo("Goodbye! 👋")
                break

            response = runtime.query(q)

            if response["type"] == "match":
                click.echo(f"MMF> {response['response']}\n")
            elif response["type"] == "no_match":
                click.echo("MMF> I don't know this yet. Teach me:")
                teach = click.prompt("Response", prompt_suffix="> ", default="", show_default=False).strip()
                if teach:
                    learner.learn(query=q, response=teach)
                    runtime.initialize()
                    click.secho("MMF> Learned successfully.\n", fg="green")
                else:
                    click.echo("MMF> Learning skipped.\n")

        except (KeyboardInterrupt, EOFError):
            click.echo("\nGoodbye! 👋")
            break


if __name__ == "__main__":
    cli()
