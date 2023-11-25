from rich.console import Console
from rich.panel import Panel

# Function to display a music player UI with search bar and always visible options
def display_music_player():
    console = Console()

    # Display rectangular dialogues for options
    options_text = "1. Recently Played\n2. Library\n3. Recommendations"
    options_panel = Panel.fit(options_text, title="Options", border_style="blue", width=60)
    console.print(options_panel)

    # Display search bar
    search_query = console.input("Search: ")

    # Display colored search results
    results_text = f"Search results for "{search_query}":\n1. Result A\n2. Result B\n3. Result C"
    results_panel = Panel.fit(results_text, title="Results", border_style="green")
    console.print(results_panel)

# Call the function to display the music player UI
display_music_player()
