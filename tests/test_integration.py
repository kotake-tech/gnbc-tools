"""gnbc-toolsの統合テスト

CLIコマンドをエンドツーエンドで検証する。
- `typer.testing.CliRunner` でコマンド全体を呼び出す
- 実際のfilesystem操作に `tmp_path` を使用する
- 外部依存（git/subprocess、questionary、webbrowser、os.execvp）のみモックする

対象コマンド:
- `gnbc branch` - ブランチ作成
- `gnbc copy`   - テンプレートコピー
- `gnbc cd`     - ディレクトリ移動
- `gnbc pr`     - PR作成
- `gnbc init`   - 一括セットアップ
"""

import os
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest
from typer.testing import CliRunner

from gnbc_tools.cli import app

runner = CliRunner()

LDAC = "kotake-tech"
INSTRUCTOR = "instructor-a"
ASSIGNMENT = "0511_test"
BRANCH = f"{ASSIGNMENT}/{LDAC}"
GITHUB_REPO = "geniee-inc/bootcamp-workshop2026"


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """課題ディレクトリと講師テンプレートを持つ疑似リポジトリ"""
    (tmp_path / ASSIGNMENT / INSTRUCTOR).mkdir(parents=True)
    (tmp_path / ASSIGNMENT / INSTRUCTOR / "README.md").write_text("template")
    (tmp_path / "0420_old").mkdir()
    (tmp_path / "0420_old" / INSTRUCTOR).mkdir()
    return tmp_path


# ---------------------------------------------------------------------------
# gnbc branch
# ---------------------------------------------------------------------------

class TestBranchCommand:
    """ブランチ作成コマンドの統合テスト"""

    def test_creates_branch_from_main(self, repo: Path):
        """mainブランチからブランチを作成できる"""
        with (
            patch("gnbc_tools.cli.get_repo_root", return_value=repo),
            patch("gnbc_tools.cli.get_ldac_name", return_value=LDAC),
            patch("gnbc_tools.cli.get_current_branch", return_value="main"),
            patch("gnbc_tools.cli.questionary.select") as mock_select,
            patch("gnbc_tools.cli.subprocess.run") as mock_run,
        ):
            mock_select.return_value.ask.return_value = ASSIGNMENT
            result = runner.invoke(app, ["branch", "--date", "0511"])

        assert result.exit_code == 0
        mock_run.assert_called_once_with(
            ["git", "checkout", "-b", BRANCH], check=True
        )
        assert BRANCH in result.output

    def test_shows_warning_when_not_on_main(self, repo: Path):
        """main以外のブランチでは警告メッセージが表示される"""
        with (
            patch("gnbc_tools.cli.get_repo_root", return_value=repo),
            patch("gnbc_tools.cli.get_ldac_name", return_value=LDAC),
            patch("gnbc_tools.cli.get_current_branch", return_value="other-branch"),
            patch("gnbc_tools.cli.questionary.select") as mock_select,
            patch("gnbc_tools.cli.subprocess.run"),
        ):
            # 1回目: ブランチ選択の警告 → CHOICE_REBASE、2回目: 課題選択
            mock_select.return_value.ask.side_effect = [
                "mainブランチをベースにして作成する(推奨)",
                ASSIGNMENT,
            ]
            result = runner.invoke(app, ["branch", "--date", "0511"])

        assert "警告" in result.output

    def test_cancel_on_non_main_branch_exits_cleanly(self, repo: Path):
        """非mainブランチでキャンセルを選択するとexit_code=0で終了する"""
        with (
            patch("gnbc_tools.cli.get_repo_root", return_value=repo),
            patch("gnbc_tools.cli.get_ldac_name", return_value=LDAC),
            patch("gnbc_tools.cli.get_current_branch", return_value="other-branch"),
            patch("gnbc_tools.cli.questionary.select") as mock_select,
            patch("gnbc_tools.cli.subprocess.run"),
        ):
            mock_select.return_value.ask.return_value = "キャンセル"
            result = runner.invoke(app, ["branch", "--date", "0511"])

        assert result.exit_code == 0

    def test_rebase_and_pull_runs_checkout_and_pull(self, repo: Path):
        """'pullしてから作成'を選ぶとcheckout+pullが実行される"""
        with (
            patch("gnbc_tools.cli.get_repo_root", return_value=repo),
            patch("gnbc_tools.cli.get_ldac_name", return_value=LDAC),
            patch("gnbc_tools.cli.get_current_branch", return_value="other-branch"),
            patch("gnbc_tools.cli.questionary.select") as mock_select,
            patch("gnbc_tools.cli.subprocess.run") as mock_run,
        ):
            mock_select.return_value.ask.side_effect = [
                "mainブランチをベースに、pullしてから作成する",
                ASSIGNMENT,
            ]
            result = runner.invoke(app, ["branch", "--date", "0511"])

        assert result.exit_code == 0
        calls = mock_run.call_args_list
        assert call(["git", "checkout", "main"], check=True) in calls
        assert call(["git", "pull"], check=True) in calls

    def test_date_option_filters_assignments(self, repo: Path):
        """--dateオプションで課題がフィルタリングされる"""
        with (
            patch("gnbc_tools.cli.get_repo_root", return_value=repo),
            patch("gnbc_tools.cli.get_ldac_name", return_value=LDAC),
            patch("gnbc_tools.cli.get_current_branch", return_value="main"),
            patch("gnbc_tools.cli.questionary.select") as mock_select,
            patch("gnbc_tools.cli.subprocess.run"),
        ):
            captured_choices: list[str] = []

            def capture_select(prompt, choices, **kwargs):
                captured_choices.extend(choices)
                m = MagicMock()
                m.ask.return_value = choices[0]
                return m

            mock_select.side_effect = capture_select
            runner.invoke(app, ["branch", "--date", "0511"])

        assert all(c.startswith("0511") for c in captured_choices)
        assert "0420_old" not in captured_choices


# ---------------------------------------------------------------------------
# gnbc copy
# ---------------------------------------------------------------------------

class TestCopyCommand:
    """テンプレートコピーコマンドの統合テスト"""

    def test_copies_instructor_dir_to_ldac_dir(self, repo: Path):
        """講師ディレクトリがLDAC名のディレクトリにコピーされる"""
        with (
            patch("gnbc_tools.cli.get_repo_root", return_value=repo),
            patch("gnbc_tools.cli.get_ldac_name", return_value=LDAC),
            patch("gnbc_tools.cli.get_current_branch", return_value=BRANCH),
        ):
            result = runner.invoke(app, ["copy"])

        assert result.exit_code == 0
        dest = repo / ASSIGNMENT / LDAC
        assert dest.is_dir()
        assert (dest / "README.md").read_text() == "template"

    def test_error_when_dest_already_exists(self, repo: Path):
        """コピー先が既に存在する場合はexit_code=1で終了する"""
        (repo / ASSIGNMENT / LDAC).mkdir()
        with (
            patch("gnbc_tools.cli.get_repo_root", return_value=repo),
            patch("gnbc_tools.cli.get_ldac_name", return_value=LDAC),
            patch("gnbc_tools.cli.get_current_branch", return_value=BRANCH),
        ):
            result = runner.invoke(app, ["copy"])

        assert result.exit_code == 1
        assert "既に存在" in result.output

    def test_error_when_no_instructor_dir(self, repo: Path):
        """講師ディレクトリが存在しない場合はexit_code=1で終了する"""
        import shutil
        shutil.rmtree(repo / ASSIGNMENT / INSTRUCTOR)
        with (
            patch("gnbc_tools.cli.get_repo_root", return_value=repo),
            patch("gnbc_tools.cli.get_ldac_name", return_value=LDAC),
            patch("gnbc_tools.cli.get_current_branch", return_value=BRANCH),
        ):
            result = runner.invoke(app, ["copy"])

        assert result.exit_code == 1
        assert "講師ディレクトリが見つかりませんでした" in result.output

    def test_prompts_when_multiple_instructors(self, repo: Path):
        """講師が複数いる場合はquestionary.selectで選択させる"""
        (repo / ASSIGNMENT / "instructor-b").mkdir()
        with (
            patch("gnbc_tools.cli.get_repo_root", return_value=repo),
            patch("gnbc_tools.cli.get_ldac_name", return_value=LDAC),
            patch("gnbc_tools.cli.get_current_branch", return_value=BRANCH),
            patch("gnbc_tools.cli.questionary.select") as mock_select,
        ):
            mock_select.return_value.ask.return_value = INSTRUCTOR
            result = runner.invoke(app, ["copy"])

        assert result.exit_code == 0
        mock_select.assert_called_once()
        assert (repo / ASSIGNMENT / LDAC).is_dir()

    def test_uses_date_option_when_not_on_assignment_branch(self, repo: Path):
        """非課題ブランチのときは--dateオプションで課題を絞り込む"""
        with (
            patch("gnbc_tools.cli.get_repo_root", return_value=repo),
            patch("gnbc_tools.cli.get_ldac_name", return_value=LDAC),
            patch("gnbc_tools.cli.get_current_branch", return_value="main"),
            patch("gnbc_tools.cli.questionary.select") as mock_select,
        ):
            mock_select.return_value.ask.return_value = ASSIGNMENT
            result = runner.invoke(app, ["copy", "--date", "0511"])

        assert result.exit_code == 0
        assert (repo / ASSIGNMENT / LDAC).is_dir()


# ---------------------------------------------------------------------------
# gnbc cd
# ---------------------------------------------------------------------------

class TestCdCommand:
    """ディレクトリ移動コマンドの統合テスト"""

    def test_spawns_shell_in_ldac_dir(self, repo: Path):
        """LDACディレクトリが存在するとき、そのディレクトリでシェルを起動する"""
        (repo / ASSIGNMENT / LDAC).mkdir()
        with (
            patch("gnbc_tools.cli.get_repo_root", return_value=repo),
            patch("gnbc_tools.cli.get_ldac_name", return_value=LDAC),
            patch("gnbc_tools.cli.get_current_branch", return_value=BRANCH),
            patch("gnbc_tools.cli.os.chdir") as mock_chdir,
            patch("gnbc_tools.cli.os.execvp") as mock_execvp,
        ):
            result = runner.invoke(app, ["cd"])

        assert result.exit_code == 0
        mock_chdir.assert_called_once_with(repo / ASSIGNMENT / LDAC)
        mock_execvp.assert_called_once()

    def test_error_when_ldac_dir_missing(self, repo: Path):
        """LDACディレクトリが存在しない場合はexit_code=1で終了する"""
        with (
            patch("gnbc_tools.cli.get_repo_root", return_value=repo),
            patch("gnbc_tools.cli.get_ldac_name", return_value=LDAC),
            patch("gnbc_tools.cli.get_current_branch", return_value=BRANCH),
        ):
            result = runner.invoke(app, ["cd"])

        assert result.exit_code == 1
        assert "見つかりません" in result.output

    def test_selects_assignment_when_not_on_assignment_branch(self, repo: Path):
        """非課題ブランチのときはquestionary.selectで課題を選択させる"""
        (repo / ASSIGNMENT / LDAC).mkdir()
        with (
            patch("gnbc_tools.cli.get_repo_root", return_value=repo),
            patch("gnbc_tools.cli.get_ldac_name", return_value=LDAC),
            patch("gnbc_tools.cli.get_current_branch", return_value="main"),
            patch("gnbc_tools.cli.questionary.select") as mock_select,
            patch("gnbc_tools.cli.os.chdir"),
            patch("gnbc_tools.cli.os.execvp"),
        ):
            mock_select.return_value.ask.return_value = ASSIGNMENT
            result = runner.invoke(app, ["cd", "--date", "0511"])

        assert result.exit_code == 0
        mock_select.assert_called_once()


# ---------------------------------------------------------------------------
# gnbc pr
# ---------------------------------------------------------------------------

class TestPrCommand:
    """PR作成コマンドの統合テスト"""

    def test_opens_pr_url_when_branch_is_pushed(self, repo: Path):
        """ブランチがpush済みの場合、確認なしでPRページを開く"""
        (repo / ASSIGNMENT / INSTRUCTOR).mkdir(exist_ok=True)
        with (
            patch("gnbc_tools.cli.get_repo_root", return_value=repo),
            patch("gnbc_tools.cli.get_ldac_name", return_value=LDAC),
            patch("gnbc_tools.cli.get_current_branch", return_value=BRANCH),
            patch("gnbc_tools.cli.get_github_repo", return_value=GITHUB_REPO),
            patch("gnbc_tools.cli._is_branch_pushed", return_value=True),
            patch("gnbc_tools.cli.webbrowser.open") as mock_open,
        ):
            result = runner.invoke(app, ["pr"])

        assert result.exit_code == 0
        mock_open.assert_called_once()
        url = mock_open.call_args[0][0]
        assert GITHUB_REPO in url
        assert "quick_pull=1" in url
        assert "draft=true" in url

    def test_pushes_branch_when_not_pushed_and_confirmed(self, repo: Path):
        """未pushブランチでpushを承認するとgit pushが実行される"""
        with (
            patch("gnbc_tools.cli.get_repo_root", return_value=repo),
            patch("gnbc_tools.cli.get_ldac_name", return_value=LDAC),
            patch("gnbc_tools.cli.get_current_branch", return_value=BRANCH),
            patch("gnbc_tools.cli.get_github_repo", return_value=GITHUB_REPO),
            patch("gnbc_tools.cli._is_branch_pushed", return_value=False),
            patch("gnbc_tools.cli.questionary.confirm") as mock_confirm,
            patch("gnbc_tools.cli.subprocess.run") as mock_run,
            patch("gnbc_tools.cli.webbrowser.open"),
        ):
            mock_confirm.return_value.ask.return_value = True
            result = runner.invoke(app, ["pr"])

        assert result.exit_code == 0
        mock_run.assert_called_once_with(
            ["git", "push", "-u", "origin", BRANCH], check=True
        )

    def test_exits_when_push_cancelled(self, repo: Path):
        """未pushブランチでpushをキャンセルするとexit_code=0で終了する"""
        with (
            patch("gnbc_tools.cli.get_repo_root", return_value=repo),
            patch("gnbc_tools.cli.get_ldac_name", return_value=LDAC),
            patch("gnbc_tools.cli.get_current_branch", return_value=BRANCH),
            patch("gnbc_tools.cli.get_github_repo", return_value=GITHUB_REPO),
            patch("gnbc_tools.cli._is_branch_pushed", return_value=False),
            patch("gnbc_tools.cli.questionary.confirm") as mock_confirm,
            patch("gnbc_tools.cli.webbrowser.open"),
        ):
            mock_confirm.return_value.ask.return_value = False
            result = runner.invoke(app, ["pr"])

        assert result.exit_code == 0

    def test_pr_url_includes_assignee(self, repo: Path):
        """講師ディレクトリが存在する場合、PRのURLにassigneesが含まれる"""
        with (
            patch("gnbc_tools.cli.get_repo_root", return_value=repo),
            patch("gnbc_tools.cli.get_ldac_name", return_value=LDAC),
            patch("gnbc_tools.cli.get_current_branch", return_value=BRANCH),
            patch("gnbc_tools.cli.get_github_repo", return_value=GITHUB_REPO),
            patch("gnbc_tools.cli._is_branch_pushed", return_value=True),
            patch("gnbc_tools.cli.webbrowser.open") as mock_open,
        ):
            result = runner.invoke(app, ["pr"])

        url = mock_open.call_args[0][0]
        assert "assignees=" in url
        assert INSTRUCTOR in url

    def test_pr_url_has_no_assignee_when_instructor_missing(self, repo: Path):
        """講師ディレクトリがない場合、assigneesなしでURLを開き警告を出す"""
        import shutil
        shutil.rmtree(repo / ASSIGNMENT / INSTRUCTOR)
        with (
            patch("gnbc_tools.cli.get_repo_root", return_value=repo),
            patch("gnbc_tools.cli.get_ldac_name", return_value=LDAC),
            patch("gnbc_tools.cli.get_current_branch", return_value=BRANCH),
            patch("gnbc_tools.cli.get_github_repo", return_value=GITHUB_REPO),
            patch("gnbc_tools.cli._is_branch_pushed", return_value=True),
            patch("gnbc_tools.cli.webbrowser.open") as mock_open,
        ):
            result = runner.invoke(app, ["pr"])

        url = mock_open.call_args[0][0]
        assert "assignees=" not in url
        assert "警告" in result.output


# ---------------------------------------------------------------------------
# gnbc init
# ---------------------------------------------------------------------------

class TestInitCommand:
    """一括セットアップコマンドの統合テスト"""

    def test_runs_branch_copy_cd_in_sequence(self, repo: Path):
        """branch → copy → cd の順に実行される"""
        call_order: list[str] = []

        def track_checkout(cmd, **kwargs):
            if cmd[:2] == ["git", "checkout"]:
                call_order.append("checkout")

        def track_chdir(path):
            call_order.append("chdir")

        def track_execvp(*args, **kwargs):
            call_order.append("execvp")

        with (
            patch("gnbc_tools.cli.get_repo_root", return_value=repo),
            patch("gnbc_tools.cli.get_ldac_name", return_value=LDAC),
            patch("gnbc_tools.cli.get_current_branch", return_value="main"),
            patch("gnbc_tools.cli.questionary.select") as mock_select,
            patch("gnbc_tools.cli.subprocess.run", side_effect=track_checkout),
            patch("gnbc_tools.cli.os.chdir", side_effect=track_chdir),
            patch("gnbc_tools.cli.os.execvp", side_effect=track_execvp),
        ):
            mock_select.return_value.ask.return_value = ASSIGNMENT
            result = runner.invoke(app, ["init", "--date", "0511"])

        assert result.exit_code == 0
        assert (repo / ASSIGNMENT / LDAC).is_dir()
        assert call_order == ["checkout", "chdir", "execvp"]

    def test_creates_branch_and_copies_files(self, repo: Path):
        """ブランチが作成され、テンプレートがコピーされる"""
        with (
            patch("gnbc_tools.cli.get_repo_root", return_value=repo),
            patch("gnbc_tools.cli.get_ldac_name", return_value=LDAC),
            patch("gnbc_tools.cli.get_current_branch", return_value="main"),
            patch("gnbc_tools.cli.questionary.select") as mock_select,
            patch("gnbc_tools.cli.subprocess.run") as mock_run,
            patch("gnbc_tools.cli.os.chdir"),
            patch("gnbc_tools.cli.os.execvp"),
        ):
            mock_select.return_value.ask.return_value = ASSIGNMENT
            result = runner.invoke(app, ["init", "--date", "0511"])

        assert result.exit_code == 0
        mock_run.assert_called_once_with(
            ["git", "checkout", "-b", BRANCH], check=True
        )
        assert (repo / ASSIGNMENT / LDAC / "README.md").exists()
