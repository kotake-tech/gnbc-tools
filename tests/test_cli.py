"""gnbc-toolsのテスト

対象関数:
- get_github_repo(): GitHubのURLをowner/repo形式に変換する
- get_assignments(): 課題ディレクトリを日付でフィルタリングする
- get_instructor_dirs(): 講師ディレクトリ(LDAC名以外)を返す

使用した技法:
- 同値分割: get_github_repo()でURLの形式(https/http/ssh/.gitあり/なし)ごとに分類
- 境界値: get_assignments()で日付フィルタが一致/不一致の境界
- デシジョンテーブル: get_instructor_dirs()でLDAC名の一致/不一致 × ディレクトリ有無の組み合わせ
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from gnbc_tools.cli import get_assignments, get_github_repo, get_instructor_dirs


# ---------------------------------------------------------------------------
# get_github_repo(): 同値分割
# ---------------------------------------------------------------------------

class TestGetGithubRepo:
    """URLフォーマットごとに同値クラスを分割してテスト"""

    def _mock_url(self, url: str) -> str:
        with patch("gnbc_tools.cli.subprocess.check_output", return_value=url):
            return get_github_repo()

    def test_https_with_git_suffix(self):
        """httpsかつ.git付き → owner/repo形式に変換される"""
        result = self._mock_url("https://github.com/kotake-tech/gnbc-tools.git")
        assert result == "kotake-tech/gnbc-tools"

    def test_https_without_git_suffix(self):
        """httpsかつ.gitなし → そのままowner/repo形式"""
        result = self._mock_url("https://github.com/kotake-tech/gnbc-tools")
        assert result == "kotake-tech/gnbc-tools"

    def test_ssh_format(self):
        """SSH形式(git@github.com:) → owner/repo形式に変換される"""
        result = self._mock_url("git@github.com:kotake-tech/gnbc-tools.git")
        assert result == "kotake-tech/gnbc-tools"

    def test_http_format(self):
        """http(非SSL)形式 → owner/repo形式に変換される"""
        result = self._mock_url("http://github.com/kotake-tech/gnbc-tools.git")
        assert result == "kotake-tech/gnbc-tools"

    def test_unsupported_url_raises(self):
        """未対応のURLフォーマット → ValueErrorを送出"""
        with pytest.raises(ValueError, match="Unsupported"):
            self._mock_url("https://gitlab.com/kotake-tech/gnbc-tools.git")

    def test_org_with_multiple_slashes(self):
        """owner/repoにスラッシュが含まれない通常ケース"""
        result = self._mock_url("https://github.com/geniee-inc/bootcamp-workshop2026.git")
        assert result == "geniee-inc/bootcamp-workshop2026"


# ---------------------------------------------------------------------------
# get_assignments(): 境界値テスト
# ---------------------------------------------------------------------------

class TestGetAssignments:
    """日付フィルタの一致/不一致の境界をテスト"""

    def _make_dirs(self, tmp_path: Path, names: list[str]) -> Path:
        for name in names:
            (tmp_path / name).mkdir()
        return tmp_path

    def test_filter_matches_some(self, tmp_path):
        """日付フィルタに一致するディレクトリが存在する場合、そのみを返す"""
        self._make_dirs(tmp_path, ["0511_test", "0511_security", "0420_git"])
        result = get_assignments(tmp_path, date_filter="0511")
        assert result == ["0511_security", "0511_test"]

    def test_filter_matches_none_returns_all(self, tmp_path):
        """日付フィルタに一致するものが0件 → 全件返す(境界: 0件)"""
        self._make_dirs(tmp_path, ["0420_git", "0421_db"])
        result = get_assignments(tmp_path, date_filter="0511")
        assert result == ["0420_git", "0421_db"]

    def test_no_date_filter_uses_today(self, tmp_path):
        """日付フィルタ省略時 → 当日の日付(MMDD)で絞り込む"""
        from datetime import date
        today = date.today().strftime("%m%d")
        self._make_dirs(tmp_path, [f"{today}_lecture", "0101_old"])
        result = get_assignments(tmp_path)
        assert result == [f"{today}_lecture"]

    def test_non_assignment_dirs_excluded(self, tmp_path):
        """MMdd_名前 パターンに一致しないディレクトリは含まれない"""
        self._make_dirs(tmp_path, ["0511_test", "src", ".git", "kotake-tech"])
        result = get_assignments(tmp_path, date_filter="0511")
        assert result == ["0511_test"]

    def test_empty_root_returns_empty(self, tmp_path):
        """ディレクトリが1つもない場合 → 空リストを返す(境界: 0件)"""
        result = get_assignments(tmp_path, date_filter="0511")
        assert result == []

    def test_results_are_sorted(self, tmp_path):
        """返り値がソート済みであること"""
        self._make_dirs(tmp_path, ["0511_z_lecture", "0511_a_lecture"])
        result = get_assignments(tmp_path, date_filter="0511")
        assert result == ["0511_a_lecture", "0511_z_lecture"]


# ---------------------------------------------------------------------------
# get_instructor_dirs(): デシジョンテーブル
# ---------------------------------------------------------------------------
#
# | ディレクトリあり | LDAC名と一致 | 期待する動作              |
# |-----------------|-------------|--------------------------|
# | あり            | 一致しない   | 返す（講師ディレクトリ）  |
# | あり            | 一致する     | 返さない（自分のdir除外） |
# | なし            | -           | 返さない                  |

class TestGetInstructorDirs:
    """LDAC名の一致/不一致 × ディレクトリ有無のデシジョンテーブルテスト"""

    def _make_dirs(self, base: Path, names: list[str]) -> None:
        for name in names:
            (base / name).mkdir()

    def test_returns_dirs_not_matching_ldac(self, tmp_path):
        """LDAC名以外のディレクトリが講師ディレクトリとして返される"""
        self._make_dirs(tmp_path, ["instructor-a", "kotake-tech"])
        result = get_instructor_dirs(tmp_path, ldac="kotake-tech")
        assert [d.name for d in result] == ["instructor-a"]

    def test_excludes_ldac_own_dir(self, tmp_path):
        """LDAC名と同名のディレクトリは含まれない"""
        self._make_dirs(tmp_path, ["kotake-tech"])
        result = get_instructor_dirs(tmp_path, ldac="kotake-tech")
        assert result == []

    def test_multiple_instructors(self, tmp_path):
        """複数の講師ディレクトリが存在する場合、全て返す"""
        self._make_dirs(tmp_path, ["instructor-a", "instructor-b", "kotake-tech"])
        result = get_instructor_dirs(tmp_path, ldac="kotake-tech")
        names = {d.name for d in result}
        assert names == {"instructor-a", "instructor-b"}

    def test_no_dirs_returns_empty(self, tmp_path):
        """ディレクトリが存在しない場合 → 空リスト"""
        result = get_instructor_dirs(tmp_path, ldac="kotake-tech")
        assert result == []

    def test_files_are_excluded(self, tmp_path):
        """ファイルはディレクトリではないので除外される"""
        (tmp_path / "instructor-a").mkdir()
        (tmp_path / "README.md").touch()
        result = get_instructor_dirs(tmp_path, ldac="kotake-tech")
        assert [d.name for d in result] == ["instructor-a"]
