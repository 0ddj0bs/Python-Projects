import sys
import pyperclip
from pathlib import Path

# Ensure pyvault root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from getpass import getpass
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# These imports reference the src folder correctly inside pyvault
from src.crypto import generate_salt, derive_key, encrypt_secret, decrypt_secret
from src.database import (
    init_db,
    save_salt,
    get_salt,
    store_secret,
    get_secret_record,
    list_services,
    delete_secret_record,
)

console = Console()


def authenticate_vault() -> bytes:
    """Handle vault initialization or master password authentication, returning the derived key."""
    init_db()
    salt = get_salt()

    if not salt:
        console.print(Panel("[bold yellow]Initializing New Vault[/bold yellow]\nNo master password found. Set one up now.", border_style="yellow"))
        while True:
            pwd1 = getpass("Enter a strong Master Password: ")
            pwd2 = getpass("Confirm Master Password: ")
            if pwd1 != pwd2:
                console.print("[red]Passwords do not match. Try again.[/red]")
                continue
            if len(pwd1) < 8:
                console.print("[red]Master password must be at least 8 characters long.[/red]")
                continue
            break

        salt = generate_salt()
        save_salt(salt)
        console.print("[green][✓] Vault initialized successfully![/green]\n")
        return derive_key(pwd1, salt)
    else:
        console.print(Panel("[bold cyan]Locked Vault[/bold cyan]\nEnter your master password to unlock.", border_style="cyan"))
        for attempt in range(3):
            pwd = getpass("Master Password: ")
            key = derive_key(pwd, salt)
            return key
        console.print("[bold red]Too many failed attempts. Exiting.[/bold red]")
        sys.exit(1)


def main():
    key = authenticate_vault()

    while True:
        console.print("\n[bold magenta]=== PYVAULT SECURE MANAGER ===[/bold magenta]")
        console.print("1. [cyan]Add / Update Secret[/cyan]")
        console.print("2. [cyan]Retrieve Secret[/cyan]")
        console.print("3. [cyan]List Stored Services[/cyan]")
        console.print("4. [cyan]Delete Secret[/cyan]")
        console.print("5. [red]Exit[/red]")

        choice = input("\nSelect an option (1-5): ").strip()

        if choice == "1":
            service = input("Service Name (e.g., github, aws): ").strip().lower()
            username = input("Username / Email: ").strip()
            password = getpass("Password / API Key to store: ")

            if not service or not password:
                console.print("[red]Service name and password cannot be empty.[/red]")
                continue

            encrypted = encrypt_secret(password, key)
            store_secret(service, username, encrypted)
            console.print(f"[green][✓] Successfully saved credentials for '{service}'![/green]")

        elif choice == "2":
            service = input("Service Name to lookup: ").strip().lower()
            record = get_secret_record(service)

            if not record:
                console.print(f"[yellow]No record found for '{service}'.[/yellow]")
                continue

            username, encrypted_pwd = record
            try:
                decrypted = decrypt_secret(encrypted_pwd, key)
                
                # Automatically copy password to clipboard
                pyperclip.copy(decrypted)

                console.print(Panel(
                    f"[bold]Service:[/bold] {service}\n"
                    f"[bold]Username:[/bold] {username or 'N/A'}\n"
                    f"[bold]Password:[/bold] [green]{decrypted}[/green]\n\n"
                    f"[dim italic]✨ Password automatically copied to clipboard![/dim italic]",
                    title="Retrieved Secret",
                    border_style="green"
                ))
            except ValueError as e:
                console.print(f"[bold red]Error:[/bold red] {e}")

        elif choice == "3":
            services = list_services()
            if not services:
                console.print("[yellow]Vault is currently empty.[/yellow]")
            else:
                table = Table(title="Stored Vault Services", show_header=True, header_style="bold cyan")
                table.add_column("#", style="dim", width=4)
                table.add_column("Service Name", style="bold")
                for idx, srv in enumerate(services, 1):
                    table.add_row(str(idx), srv)
                console.print(table)

        elif choice == "4":
            service = input("Service Name to delete: ").strip().lower()
            confirm = input(f"Are you sure you want to delete '{service}'? (y/n): ").strip().lower()
            if confirm == 'y':
                deleted = delete_secret_record(service)
                if deleted:
                    console.print(f"[green][✓] Deleted '{service}' from vault.[/green]")
                else:
                    console.print(f"[yellow]Service '{service}' not found.[/yellow]")

        elif choice == "5":
            console.print("[cyan]Locking vault and exiting. Stay secure![/cyan]")
            break
        else:
            console.print("[red]Invalid choice. Enter a number between 1 and 5.[/red]")


if __name__ == "__main__":
    main()
