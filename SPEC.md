## コマンド一覧

[README.md](./README.md) を参照

## 仕様

- GitHubリポジトリ: `git config --get remote.origin.url`で取得した origin URLをパースして、`owner/repo`形式で抽出する
- LDAC名: `whoami`で取得
- 課題名: `bootcamp用リポジトリ/MMdd_講義名/`でディレクトリに分けて置いてある。`MMdd_講義名`が課題名。日付で絞り込んだ上で、`questionary`でユーザーに選択させる
- ブランチ名: `MMdd_講義名/LDAC名`
- テンプレート作成: `bootcamp用リポジトリ/MMdd_講義名/講師名`がテンプレートとして存在する。それを`bootcamp用リポジトリ/MMdd_講義名/LDAC名`にコピーする
  複数候補がある場合は`questionary`でユーザーに選択させる。1つも候補がない場合はエラー終了する
- PR作成
  以下をブラウザーで開く
  `https://github.com/<owner/repo>/compare/main...<ブランチ名>?quick_pull=1&title=<PRタイトル>&assignees=<asignees>&draft=true`
  - owner/repo: `git remote show origin` から取得
  - ブランチ名: 現在のブランチ
  - PRタイトル: `MMdd_講義名/LDAC名` ブランチ名と同じ
  - asignees: 講師名 `bootcamp用リポジトリ/MMdd_講義名/`にあるディレクトリのうち、LDAC名と違うものを講師名と推測する。候補がない場合は警告を出すとともに、asigneesを指定せずにURLを開く
