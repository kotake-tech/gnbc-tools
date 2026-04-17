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


def get_github_repo() -> str:
    """git remote originのURLから owner/repo 形式を取得する"""
    url = subprocess.check_output(
        ["git", "config", "--get", "remote.origin.url"], text=True
    ).strip()

    if url.endswith(".git"):
        url = url[:-4]

    if url.startswith("https://github.com/"):
        return url.replace("https://github.com/", "")
    elif url.startswith("http://github.com/"):
        return url.replace("http://github.com/", "")
    elif url.startswith("git@github.com:"):
        return url.replace("git@github.com:", "")
    else:
        raise ValueError(f"Unsupported GitHub URL format: {url}")


def get_ldac_name() -> str:
    return subprocess.check_output(["whoami"], text=True).strip()


def get_current_branch() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True
    ).strip()


def get_repo_root() -> Path:
    """Gitリポジトリのルートディレクトリを取得する"""
    return Path(
        subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], text=True
        ).strip()
    )


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
    root = get_repo_root()
    ldac = get_ldac_name()

    current_branch = get_current_branch()
    if current_branch != "main":
        typer.echo(
            f"警告: 現在のブランチは '{current_branch}' です。"
            " main に checkout して pull することを推奨します。",
            err=True,
        )
        proceed = questionary.confirm("このまま続行しますか?", default=False).ask()
        if not proceed:
            raise typer.Exit(0)

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
    root = get_repo_root()
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
    root = get_repo_root()
    ldac = get_ldac_name()

    current_branch = get_current_branch()
    pr_title = current_branch

    assignees: list[str] = []
    if "/" in current_branch:
        assignment = current_branch.rsplit("/", 1)[0]
        assignment_dir = root / assignment
        if assignment_dir.exists():
            assignees = [d.name for d in get_instructor_dirs(assignment_dir, ldac)]

    if not assignees:
        typer.echo("警告: 講師ディレクトリが見つかりませんでした。assigneesを指定せずにPRページを開きます", err=True)

    encoded_branch = quote(current_branch, safe="")
    encoded_title = quote(pr_title, safe="")

    query = f"quick_pull=1&title={encoded_title}&draft=true"
    if assignees:
        query += f"&assignees={quote(','.join(assignees), safe='')}"

    github_repo = get_github_repo()
    url = (
        f"https://github.com/{github_repo}/compare/"
        f"main...{encoded_branch}?{query}"
    )

    webbrowser.open(url)
    typer.echo(f"PRページを開きました: {url}")


def main():
    app()
