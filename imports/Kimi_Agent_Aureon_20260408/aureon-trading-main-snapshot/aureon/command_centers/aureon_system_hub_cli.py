#!/usr/bin/env python3
"""
🌌 AUREON SYSTEM HUB - CLI INTERFACE
====================================
Command-line interface for system hub operations.

Commands:
  scan          - Scan workspace and generate registry
  list          - List all systems by category
  search TERM   - Search for systems
  stats         - Show category statistics
  info SYSTEM   - Show detailed system information
  map           - Generate ASCII mind map
  launch        - Launch web dashboard

Author: Aureon Trading System
Date: January 2026
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys, os
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        import io
        def _is_utf8_wrapper(stream):
            return (isinstance(stream, io.TextIOWrapper) and 
                    hasattr(stream, 'encoding') and stream.encoding and
                    stream.encoding.lower().replace('-', '') == 'utf8')
        if hasattr(sys.stdout, 'buffer') and not _is_utf8_wrapper(sys.stdout):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        if hasattr(sys.stderr, 'buffer') and not _is_utf8_wrapper(sys.stderr):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    except Exception:
        pass

import argparse
from aureon_system_hub import SystemRegistry
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich import box

console = Console()


def cmd_scan(registry: SystemRegistry):
    """Scan workspace and generate registry."""
    console.print("[bold cyan]🔍 Scanning workspace...[/bold cyan]")
    registry.scan_workspace()
    registry.save_registry()
    console.print("[bold green]✅ Registry generated successfully[/bold green]")


def cmd_list(registry: SystemRegistry, category: str = None):
    """List all systems by category."""
    registry.scan_workspace()
    
    if category:
        # Filter by specific category
        categories = {k: v for k, v in registry.categories.items() if category.lower() in k.lower()}
    else:
        categories = registry.categories
    
    for cat_name, category_obj in categories.items():
        table = Table(title=f"{category_obj.icon} {cat_name}", box=box.ROUNDED)
        table.add_column("System", style="cyan")
        table.add_column("LOC", justify="right", style="yellow")
        table.add_column("Integrations", style="green")
        table.add_column("Description", style="white")
        
        for system in sorted(category_obj.systems, key=lambda s: s.name):
            integrations = []
            if system.is_dashboard:
                integrations.append(f"🌐:{system.dashboard_port}")
            if system.has_thought_bus:
                integrations.append("🔗TB")
            if system.has_queen_integration:
                integrations.append("👑Q")
            
            table.add_row(
                system.name,
                f"{system.lines_of_code:,}",
                " ".join(integrations),
                system.description[:60] + "..." if len(system.description) > 60 else system.description
            )
        
        console.print(table)
        console.print()


def cmd_search(registry: SystemRegistry, term: str):
    """Search for systems."""
    registry.scan_workspace()
    
    results = []
    for system in registry.systems.values():
        if (term.lower() in system.name.lower() or 
            term.lower() in system.description.lower() or
            term.lower() in system.category.lower()):
            results.append(system)
    
    if not results:
        console.print(f"[red]❌ No systems found matching '{term}'[/red]")
        return
    
    table = Table(title=f"🔍 Search Results: '{term}'", box=box.ROUNDED)
    table.add_column("System", style="cyan")
    table.add_column("Category", style="magenta")
    table.add_column("LOC", justify="right", style="yellow")
    table.add_column("Description", style="white")
    
    for system in sorted(results, key=lambda s: s.name):
        table.add_row(
            system.name,
            system.category,
            f"{system.lines_of_code:,}",
            system.description[:60] + "..." if len(system.description) > 60 else system.description
        )
    
    console.print(table)
    console.print(f"\n[green]Found {len(results)} systems[/green]")


def cmd_stats(registry: SystemRegistry):
    """Show category statistics."""
    registry.scan_workspace()
    
    stats = registry.get_category_stats()
    
    table = Table(title="📊 System Statistics", box=box.DOUBLE)
    table.add_column("Category", style="cyan")
    table.add_column("Systems", justify="right", style="yellow")
    table.add_column("Total LOC", justify="right", style="green")
    table.add_column("Dashboards", justify="center", style="magenta")
    table.add_column("ThoughtBus", justify="center", style="blue")
    table.add_column("Queen", justify="center", style="red")
    
    total_systems = 0
    total_loc = 0
    total_dashboards = 0
    total_tb = 0
    total_queen = 0
    
    for cat_name, cat_stats in sorted(stats.items()):
        category = registry.categories[cat_name]
        table.add_row(
            f"{category.icon} {cat_name}",
            str(cat_stats['count']),
            f"{cat_stats['total_loc']:,}",
            str(cat_stats['dashboards']),
            str(cat_stats['thought_bus_integrated']),
            str(cat_stats['queen_integrated'])
        )
        
        total_systems += cat_stats['count']
        total_loc += cat_stats['total_loc']
        total_dashboards += cat_stats['dashboards']
        total_tb += cat_stats['thought_bus_integrated']
        total_queen += cat_stats['queen_integrated']
    
    table.add_section()
    table.add_row(
        "[bold]TOTAL[/bold]",
        f"[bold]{total_systems}[/bold]",
        f"[bold]{total_loc:,}[/bold]",
        f"[bold]{total_dashboards}[/bold]",
        f"[bold]{total_tb}[/bold]",
        f"[bold]{total_queen}[/bold]"
    )
    
    console.print(table)


def cmd_info(registry: SystemRegistry, system_name: str):
    """Show detailed system information."""
    registry.scan_workspace()
    
    if system_name not in registry.systems:
        console.print(f"[red]❌ System '{system_name}' not found[/red]")
        return
    
    system = registry.systems[system_name]
    
    # Create info panel
    info_text = f"""
[bold cyan]Name:[/bold cyan] {system.name}
[bold cyan]Category:[/bold cyan] {system.category}
[bold cyan]File:[/bold cyan] {system.filepath}
[bold cyan]Lines of Code:[/bold cyan] {system.lines_of_code:,}
[bold cyan]Last Modified:[/bold cyan] {system.last_modified}

[bold cyan]Description:[/bold cyan]
{system.description}

[bold cyan]Integrations:[/bold cyan]
• ThoughtBus: {'✅' if system.has_thought_bus else '❌'}
• Queen Hive: {'✅' if system.has_queen_integration else '❌'}
• Dashboard: {'✅ Port ' + str(system.dashboard_port) if system.is_dashboard else '❌'}

[bold cyan]Sacred Frequencies:[/bold cyan]
{', '.join(str(f) for f in system.sacred_frequencies) if system.sacred_frequencies else 'None'}

[bold cyan]Imports ({len(system.imports)}):[/bold cyan]
{', '.join(system.imports[:10])}{'...' if len(system.imports) > 10 else ''}
    """
    
    panel = Panel(info_text, title=f"🔍 System Info: {system.name}", border_style="cyan")
    console.print(panel)


def cmd_map(registry: SystemRegistry):
    """Generate ASCII mind map."""
    registry.scan_workspace()
    
    tree = Tree("🌌 [bold cyan]Aureon Trading System[/bold cyan]")
    
    for cat_name, category in sorted(registry.categories.items()):
        cat_branch = tree.add(f"{category.icon} [bold]{cat_name}[/bold] ({category.system_count} systems)")
        
        for system in sorted(category.systems, key=lambda s: s.name)[:5]:  # Show first 5
            badges = []
            if system.is_dashboard:
                badges.append("🌐")
            if system.has_thought_bus:
                badges.append("🔗")
            if system.has_queen_integration:
                badges.append("👑")
            
            badge_str = " ".join(badges)
            cat_branch.add(f"{system.name} {badge_str}")
        
        if category.system_count > 5:
            cat_branch.add(f"[dim]... and {category.system_count - 5} more[/dim]")
    
    console.print(tree)


def cmd_launch(registry: SystemRegistry):
    """Launch web dashboard."""
    import subprocess
    
    console.print("[bold cyan]🚀 Launching Aureon System Hub Dashboard...[/bold cyan]")
    console.print("[yellow]URL: http://localhost:13001[/yellow]")
    console.print("[dim]Press Ctrl+C to stop[/dim]\n")
    
    try:
        subprocess.run([sys.executable, "aureon_system_hub_dashboard.py"])
    except KeyboardInterrupt:
        console.print("\n[yellow]Dashboard stopped[/yellow]")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="🌌 Aureon System Hub - CLI Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Scan command
    subparsers.add_parser('scan', help='Scan workspace and generate registry')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all systems by category')
    list_parser.add_argument('category', nargs='?', help='Filter by category')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search for systems')
    search_parser.add_argument('term', help='Search term')
    
    # Stats command
    subparsers.add_parser('stats', help='Show category statistics')
    
    # Info command
    info_parser = subparsers.add_parser('info', help='Show detailed system information')
    info_parser.add_argument('system', help='System name')
    
    # Map command
    subparsers.add_parser('map', help='Generate ASCII mind map')
    
    # Launch command
    subparsers.add_parser('launch', help='Launch web dashboard')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    registry = SystemRegistry()
    
    if args.command == 'scan':
        cmd_scan(registry)
    elif args.command == 'list':
        cmd_list(registry, args.category if hasattr(args, 'category') else None)
    elif args.command == 'search':
        cmd_search(registry, args.term)
    elif args.command == 'stats':
        cmd_stats(registry)
    elif args.command == 'info':
        cmd_info(registry, args.system)
    elif args.command == 'map':
        cmd_map(registry)
    elif args.command == 'launch':
        cmd_launch(registry)


if __name__ == "__main__":
    main()
