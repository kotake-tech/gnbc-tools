import re
import shutil
import subprocess
import webbrowser
from datetime import date
from pathlib import Path
from urllib.parse import quote

import questionary
import typer

app = typer.Typer(help="GENIEEのbootcampで使う便利ツール")

GITHUB_REPO = "geniee-inc/bootcamp-workshop2026"


def get_ldac_name() -> str:
    return subprocess.check_output(["whoami"], text=True).strip()


def get_current_branch() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True
    ).strip()


def get_assignments(root: Path) -> list[str]:
    """MMdd_講義名 パターンのディレクトリを取得し、今日の日付で絞り込む。"""
    today = date.today()
    prefix = today.strftime("%m%d")

    all_assignments = sorted(
        d.name
        for d in root.iterdir()
        if d.is_dir() and re.match(r"^\d{4}_", d.name)
    )

    today_assignments = [a for a in all_assignments if a.startswith(prefix)]
    return today_assignments if today_assignments else all_assignments


def get_instructor_dirs(assignment_dir: Path, ldac: str) -> list[Path]:
    """LDAC名以外のディレクトリを講師ディレクトリとして返す。"""
    return [d for d in assignment_dir.iterdir() if d.is_dir() and d.name != ldac]


@app.command()
def branch():
    """課題のブランチを作成する"""
    root = Path.cwd()
    ldac = get_ldac_name()

    assignments = get_assignments(root)
    if not assignments:
        typer.echo("課題ディレクトリが見つかりませんでした")
        raise typer.Exit(1)

    assignment = questionary.select(
        "課題を選択してください:",
        choices=assignments,
    ).ask()

    if assignment is None:
        raise typer.Exit(0)

    branch_name = f"{assignment}/{ldac}"
    subprocess.run(["git", "checkout", "-b", branch_name], check=True)
    typer.echo(f"ブランチ '{branch_name}' を作成しました")


@app.command()
def copy():
    """テンプレをコピーする"""
    root = Path.cwd()
    ldac = get_ldac_name()

    current_branch = get_current_branch()
    if "/" in current_branch:
        assignment = current_branch.rsplit("/", 1)[0]
    else:
        assignments = get_assignments(root)
        if not assignments:
            typer.echo("課題ディレクトリが見つかりませんでした")
            raise typer.Exit(1)
        assignment = questionary.select(
            "課題を選択してください:",
            choices=assignments,
        ).ask()
        if assignment is None:
            raise typer.Exit(0)

    assignment_dir = root / assignment
    if not assignment_dir.exists():
        typer.echo(f"課題ディレクトリ '{assignment}' が見つかりません")
        raise typer.Exit(1)

    instructor_dirs = get_instructor_dirs(assignment_dir, ldac)
    if not instructor_dirs:
        typer.echo("テンプレートとなる講師ディレクトリが見つかりませんでした")
        raise typer.Exit(1)

    if len(instructor_dirs) == 1:
        template_dir = instructor_dirs[0]
    else:
        choice = questionary.select(
            "テンプレートを選択してください:",
            choices=[d.name for d in instructor_dirs],
        ).ask()
        if choice is None:
            raise typer.Exit(0)
        template_dir = assignment_dir / choice

    dest_dir = assignment_dir / ldac
    if dest_dir.exists():
        typer.echo(f"'{dest_dir.relative_to(root)}' は既に存在します")
        raise typer.Exit(1)

    shutil.copytree(template_dir, dest_dir)
    typer.echo(f"'{template_dir.name}' を '{dest_dir.relative_to(root)}' にコピーしました")


@app.command()
def pr():
    """PRを作成する"""
    root = Path.cwd()
    ldac = get_ldac_name()

    current_branch = get_current_branch()
    pr_title = current_branch

    assignees: list[str] = []
    if "/" in current_branch:
        assignment = current_branch.rsplit("/", 1)[0]
        assignment_dir = root / assignment
        if assignment_dir.exists():
            assignees = [d.name for d in get_instructor_dirs(assignment_dir, ldac)]

    encoded_branch = quote(current_branch, safe="")
    encoded_title = quote(pr_title, safe="")
    encoded_assignees = quote(",".join(assignees), safe="")

    url = (
        f"https://github.com/{GITHUB_REPO}/compare/"
        f"{encoded_branch}...main"
        f"?quick_pull=1&title={encoded_title}&assignees={encoded_assignees}"
    )

    webbrowser.open(url)
    typer.echo(f"PRページを開きました: {url}")


def main():
    app()
