#!/usr/bin/env python3
"""Demo script to showcase CMUS Rich UI with screenshots."""

import sys
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align


def create_dashboard_demo():
    """Create a demo dashboard layout."""
    layout = Layout()
    
    layout.split_column(
        Layout(name="header", size=5),
        Layout(name="main"),
        Layout(name="footer", size=3),
    )
    
    layout["main"].split_row(
        Layout(name="sidebar", ratio=1),
        Layout(name="content", ratio=3),
    )
    
    # Now Playing Header
    now_playing = Panel(
        Align.center(
            Text.assemble(
                ("Come Together", "bold cyan"),
                "\n",
                ("by The Beatles", "yellow"),
                "\n",
                ("from Abbey Road", "blue"),
            ),
            vertical="middle"
        ),
        title="♪ ▶ Now Playing",
        border_style="green"
    )
    layout["header"].update(now_playing)
    
    # Queue Sidebar
    queue_table = Table(show_header=True, header_style="bold cyan")
    queue_table.add_column("#", width=3)
    queue_table.add_column("Track")
    
    queue_items = [
        ("1", "Something - The Beatles"),
        ("2", "Maxwell's Silver Hammer - The Beatles"),
        ("3", "Oh! Darling - The Beatles"),
        ("4", "Octopus's Garden - The Beatles"),
        ("5", "I Want You (She's So Heavy) - The Beatles"),
    ]
    
    for num, track in queue_items:
        queue_table.add_row(num, track)
    
    queue_panel = Panel(queue_table, title="Queue (5)", border_style="blue")
    layout["sidebar"].update(queue_panel)
    
    # Library Content
    library_content = Text("Library browser\n\n", style="cyan", justify="center")
    library_content.append("📁 Music Library\n\n", style="bold")
    library_content.append("  🎵 The Beatles - Abbey Road (1969)\n", style="dim")
    library_content.append("  🎵 Pink Floyd - Dark Side of the Moon (1973)\n", style="dim")
    library_content.append("  🎵 Led Zeppelin - IV (1971)\n", style="dim")
    library_content.append("  🎵 Queen - A Night at the Opera (1975)\n", style="dim")
    
    library_panel = Panel(
        Align.center(library_content, vertical="middle"),
        title="Library",
        border_style="cyan"
    )
    layout["content"].update(library_panel)
    
    # Progress Bar Footer
    bar_filled = 30
    bar_total = 60
    progress_bar = "█" * bar_filled + "━" * (bar_total - bar_filled)
    
    footer_content = Text.assemble(
        (progress_bar, "cyan"),
        "\n",
        ("02:25 / 04:19  Vol: 75%  🔀 ", "dim")
    )
    
    layout["footer"].update(Panel(footer_content))
    
    return layout


def create_paused_demo():
    """Create a paused state demo."""
    layout = Layout()
    
    layout.split_column(
        Layout(name="header", size=5),
        Layout(name="main"),
        Layout(name="footer", size=3),
    )
    
    layout["main"].split_row(
        Layout(name="sidebar", ratio=1),
        Layout(name="content", ratio=3),
    )
    
    # Now Playing Header - Paused
    now_playing = Panel(
        Align.center(
            Text.assemble(
                ("Come Together", "bold cyan"),
                "\n",
                ("by The Beatles", "yellow"),
                "\n",
                ("from Abbey Road", "blue"),
            ),
            vertical="middle"
        ),
        title="♪ ⏸ Now Playing",
        border_style="yellow"
    )
    layout["header"].update(now_playing)
    
    # Queue
    queue_table = Table(show_header=True, header_style="bold cyan")
    queue_table.add_column("#", width=3)
    queue_table.add_column("Track")
    
    for num, track in [("1", "Something - The Beatles"), ("2", "Maxwell's Silver Hammer - The Beatles")]:
        queue_table.add_row(num, track)
    
    layout["sidebar"].update(Panel(queue_table, title="Queue (2)", border_style="blue"))
    
    # Content
    library_content = Text("🎵 Music Player Paused", style="yellow", justify="center")
    layout["content"].update(Panel(Align.center(library_content, vertical="middle"), title="Library", border_style="cyan"))
    
    # Footer
    progress_bar = "█" * 30 + "━" * 30
    footer_content = Text.assemble(
        (progress_bar, "yellow"),
        "\n",
        ("02:25 / 04:19  Vol: 75%  ", "dim")
    )
    layout["footer"].update(Panel(footer_content))
    
    return layout


def create_stopped_demo():
    """Create a stopped state demo."""
    layout = Layout()
    
    layout.split_column(
        Layout(name="header", size=5),
        Layout(name="main"),
        Layout(name="footer", size=3),
    )
    
    layout["main"].split_row(
        Layout(name="sidebar", ratio=1),
        Layout(name="content", ratio=3),
    )
    
    # No track playing
    layout["header"].update(
        Panel(
            Align.center("No track playing", vertical="middle"),
            title="♪ Now Playing",
            border_style="dim"
        )
    )
    
    # Empty queue
    queue_table = Table(show_header=True, header_style="bold cyan")
    queue_table.add_column("#", width=3)
    queue_table.add_column("Track")
    queue_table.add_row("", "[dim]Queue is empty[/dim]")
    
    layout["sidebar"].update(Panel(queue_table, title="Queue (0)", border_style="blue"))
    
    # Content
    library_content = Text("Welcome to CMUS Rich!\n\nPress 'h' for help", style="dim", justify="center")
    layout["content"].update(Panel(Align.center(library_content, vertical="middle"), title="Library", border_style="cyan"))
    
    # Footer
    layout["footer"].update(Panel(Text("━" * 80, style="dim")))
    
    return layout


def main():
    """Generate UI screenshots."""
    # Playing state
    console = Console(record=True, width=120)
    layout = create_dashboard_demo()
    console.print(layout)
    console.save_svg("screenshots/dashboard_playing.svg", title="CMUS Rich - Now Playing")
    print("✅ Screenshot saved to: screenshots/dashboard_playing.svg")
    
    # Paused state
    console = Console(record=True, width=120)
    layout = create_paused_demo()
    console.print(layout)
    console.save_svg("screenshots/dashboard_paused.svg", title="CMUS Rich - Paused")
    print("✅ Screenshot saved to: screenshots/dashboard_paused.svg")
    
    # Stopped state
    console = Console(record=True, width=120)
    layout = create_stopped_demo()
    console.print(layout)
    console.save_svg("screenshots/dashboard_stopped.svg", title="CMUS Rich - Stopped")
    print("✅ Screenshot saved to: screenshots/dashboard_stopped.svg")
    
    print("\n🎉 All screenshots generated successfully!")
    print("\nYou can view them in the screenshots/ directory:")
    print("  - dashboard_playing.svg  (Active playback)")
    print("  - dashboard_paused.svg   (Paused state)")
    print("  - dashboard_stopped.svg  (No music)")


if __name__ == "__main__":
    main()



if __name__ == "__main__":
    main()
