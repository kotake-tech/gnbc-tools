# gnbc-tools

GENIEEのbootcampで使う便利ツールです。

## このツールが解決する課題

bootcampの課題の開始〜PR作成を手動で行うと、以下の手間や発生しがちなミスが存在します。

- **課題の絞り込みが面倒**: 数十の課題ディレクトリから、今日の課題を自分で日付で探し出す必要がある
- **コマンド実行の手間**: 毎回`MMdd_講義名/LDAC名`で`git checkout -b`、`cp -r`, `cd`するのが単純に面倒
- **ブランチ名のタイポ**: `MMdd_講義名/LDAC名` というフォーマットを毎回手で入力するため、スペルミスや日付の誤りが起きやすい
- **main以外からのブランチ作成**: 前の課題のブランチが残ったままの状態でブランチを切ってしまい、意図しない差分が混入する
- **pushし忘れによるPR作成失敗**: ローカルのブランチをpushせずにPRを作成しようとしてしまう
- **PRタイトルの自動置換を修正する手間**: GitHubのGUIからPRを作成するとアンダーバーなどが勝手にスペースに置換され、それを手動で元に戻す手間が生じる

`gnbc-tools`はこれらをインタラクティブなCLIで自動化します。
あらかじめ今日の日付で絞り込間れた中からターゲットを選ぶだけで、ブランチ作成からテンプレートコピーまで自動で実行できます。main以外からのブランチ作成には警告と選択肢を提示し、PR作成前にはリモートへのpushを確認・自動push、PRタイトルは正しい内容を自動設定します。

## 前提環境

- MacまたはLinux
- [uv](https://docs.astral.sh/uv/) がインストールされている
  ```sh
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
  or
  ```
  brew install uv
  ```

## インストール

```sh
uv tool install git+https://github.com/kotake-tech/gnbc-tools
```

### アップデート

```sh
uv tool update gnbc-tools
```


## 使用方法

> [!note]
> 以下のコマンドはbootcampのリポジトリ内（サブディレクトリも可）で実行してください。

- ブランチ作成(`branch`)・テンプレコピー(`copy`)・ディレクトリ移動(`cd`)を一括で行う
  ```sh
  gnbc init
  ```
  - 課題のブランチを作成する
    ```sh
    gnbc branch
    ````
  - テンプレをコピーする
    ```sh
    gnbc copy
    ```
  - 課題のディレクトリに移動する
    ```sh
    gnbc cd
    ```
    このコマンドは新しいシェルを起動します。ルートに戻るには`exit`を実行してください
- PRを作成する
  ```sh
  gnbc pr
  ```


> [!tip]
> `init`、`branch`、`copy`、`cd` コマンドは `--date`/`-d` オプションで課題の日付を指定できます。省略した場合は当日の日付で絞り込みます。
> ```sh
> gnbc init --date 0420
> gnbc branch -d 0420
> ``` 

## 仕様

[SPEC.md](./SPEC.md)
