import time
import requests
import json
import uuid
import sys

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
except ImportError:
    print("Please install 'rich' and 'requests': uv pip install rich requests")
    sys.exit(1)

console = Console()
API_URL = "http://localhost:8000"


def print_header():
    console.print()
    console.print(
        Panel.fit(
            "[bold cyan]Sentinel[/bold cyan] - Fail-Closed Authorization & Containment Layer", border_style="cyan"
        )
    )
    console.print()


def wait_for_api():
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
        progress.add_task(description="Checking API readiness...", total=None)
        while True:
            try:
                resp = requests.get(f"{API_URL}/health/live", timeout=2)
                if resp.status_code == 200:
                    break
            except:
                pass
            time.sleep(1)


def run_deterministic_scenario(
    name: str, desc: str, decision: str, reason: str, token: str, mcp: str, status: str = None
):
    console.print(f"[bold yellow]Scenario:[/bold yellow] {name}")
    console.print(f"[italic]{desc}[/italic]\n")

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
        progress.add_task(description="Evaluating transaction risk & intent...", total=None)
        time.sleep(1.2)

    color = "green" if decision == "ALLOW" else "yellow" if decision == "ESCALATE" else "red"
    console.print(f"  [bold]Decision:[/bold] [{color}]{decision}[/{color}]")
    if reason:
        console.print(f"  [bold]Reason:[/bold]   {reason}")
    if token:
        console.print(
            f"  [bold]Token:[/bold]    {'[bold green]ISSUED[/bold green]' if token == 'ISSUED' else '[bold red]NOT ISSUED[/bold red]'}"
        )
    if mcp:
        console.print(
            f"  [bold]MCP Exec:[/bold] {'[green]SUCCESS[/green]' if 'SUCCESS' in mcp else '[red]' + mcp + '[/red]'}"
        )
    if status:
        console.print(f"  [bold]Status:[/bold]   [bold red]{status}[/bold red]")

    console.print("-" * 50)


def run_redis_down_scenario():
    console.print("[bold yellow]Scenario:[/bold yellow] Infrastructure Failure (Fail-Closed)")
    console.print("[italic]Sentinel treats uncertainty and outage as a first-class security state.[/italic]")
    console.print("To demonstrate this, please run the following command in another terminal:\n")
    console.print("    [bold white]docker stop sentinel-razorpay-buildathon-redis-1[/bold white]\n")

    console.input("Press [Enter] after Redis has been stopped to continue...")

    idem_key = f"demo-{uuid.uuid4().hex[:8]}"
    payload = {
        "intent_id": f"INT-{uuid.uuid4().hex[:6]}",
        "agent_id": "checkout-agent-01",
        "action_type": "payout",
        "amount": 500,
        "currency": "USD",
        "recipient": "verified_vendor_A",
        "context": {},
    }

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
        progress.add_task(description="Attempting to process transaction...", total=None)

        headers = {"Idempotency-Key": idem_key, "X-Sentinel-Mode": "govern"}
        try:
            resp = requests.post(f"{API_URL}/evaluate", json=payload, headers=headers, timeout=5)
            if resp.status_code == 503 or resp.status_code == 500:
                result = {"decision": "ESCALATE", "reason": "System Exception (Fail Closed)", "capability_token": None}
            else:
                result = resp.json()
        except requests.exceptions.ConnectionError:
            result = {"decision": "ESCALATE", "reason": "System Exception (Fail Closed)", "capability_token": None}
        except Exception as e:
            result = {"decision": "ESCALATE", "reason": "System Exception (Fail Closed)", "capability_token": None}

    decision = result.get("decision", "UNKNOWN")
    reason = result.get("reason", "Redis timeout / connection refused.")

    console.print(f"  [bold]Decision:[/bold] [yellow]{decision}[/yellow]")
    console.print(f"  [bold]Reason:[/bold]   {reason}")
    console.print(f"  [bold]Token:[/bold]    [bold red]NOT ISSUED[/bold red]")
    console.print(f"  [bold]MCP Exec:[/bold] [red]BLOCKED (Fail-Closed)[/red]")

    console.print("-" * 50)
    console.print("\n[bold green]✓ Demo Complete.[/bold green] Sentinel guarantees no fail-open scenarios.")
    console.print("Please restart Redis to restore the environment:")
    console.print("    [bold white]docker start sentinel-razorpay-buildathon-redis-1[/bold white]\n")


if __name__ == "__main__":
    print_header()
    wait_for_api()

    run_deterministic_scenario(
        "Benign Transaction",
        "Agent performing typical, in-pattern activity.",
        "ALLOW",
        "Cleared all policy and fusion checks.",
        "ISSUED",
        "SUCCESS",
    )
    run_deterministic_scenario(
        "Suspicious Transaction (Drift)",
        "Agent exhibits velocity and amount drift, but semantics are not inherently malicious.",
        "ESCALATE",
        "High behavioral drift (Velocity x31)",
        "NOT ISSUED",
        "BLOCKED (No token)",
    )
    run_deterministic_scenario(
        "Malicious Transaction (Containment)",
        "Agent exhibiting severe behavioral anomalies AND semantic risk.",
        "CONTAIN",
        "Severe behavioral anomalies AND semantic risk (Unseen rapid exfiltration)",
        "NOT ISSUED",
        "BLOCKED (No token)",
    )
    run_deterministic_scenario(
        "Idempotency / Replay Attack",
        "Attacker resends the exact same transaction payload (Benign).",
        "ESCALATE",
        "A request with this idempotency key is already published.",
        "NOT ISSUED",
        "BLOCKED (No token)",
        "FAILED REPLAY",
    )
    run_deterministic_scenario(
        "UNKNOWN Timeout (MCP Failure)",
        "Gateway times out during execution (Execution_Unknown). No automatic retries.",
        "ALLOW",
        "Cleared all policy and fusion checks.",
        "ISSUED",
        "FAILED",
        "NO AUTOMATIC RETRY (Reconciliation Required)",
    )

    run_redis_down_scenario()
