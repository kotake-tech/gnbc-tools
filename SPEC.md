## コマンド一覧

[README.md](./README.md) を参照

## データ定義

### GitHubリポジトリ

`git config --get remote.origin.url` で取得した origin URL をパースして、`owner/repo` 形式で抽出する

### LDAC名

`whoami` で取得する

### 課題名

bootcamp用リポジトリ内の `MMdd_講義名/` ディレクトリ名を課題名とする。
日付で絞り込んだ上で、`questionary` でユーザーに選択させる

### リポジトリルート

`git rev-parse --show-toplevel` で取得する。コマンドはリポジトリ内のサブディレクトリからも実行可能

### 講師名

`bootcamp用リポジトリ/MMdd_講義名/` にあるディレクトリのうち、LDAC名と異なるものを講師名と推測する

### ブランチ名

`MMdd_講義名/LDAC名` の形式

## コマンド仕様

### `gnbc branch` - ブランチ作成

課題名を選択させ、`MMdd_講義名/LDAC名` の形式でブランチを作成する。

現在のブランチが `main` ではない場合、`main` に `checkout` し `pull` することを推奨する警告を出す。その上で proceed するかどうかをユーザーに選ばせる。

### `gnbc copy` - テンプレートコピー

`bootcamp用リポジトリ/MMdd_講義名/講師名` をテンプレートとして `bootcamp用リポジトリ/MMdd_講義名/LDAC名` にコピーする。

複数候補がある場合は `questionary` でユーザーに選択させる。1つも候補がない場合はエラー終了する。

### `gnbc pr` - PR作成

以下の URL をブラウザで開く:

```
https://github.com/<owner/repo>/compare/main...<ブランチ名>?quick_pull=1&title=<PRタイトル>&assignees=<assignees>&draft=true
```

| パラメータ | 内容 |
|---|---|
| `owner/repo` | `git remote show origin` から取得 |
| `ブランチ名` | 現在のブランチ |
| `PRタイトル` | ブランチ名と同じ（`MMdd_講義名/LDAC名`） |
| `assignees` | 講師名。候補がない場合は警告を出し、`assignees` を指定せずに URL を開く |
