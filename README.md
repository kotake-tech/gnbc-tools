# gnbc-tools

GENIEEのbootcampで使う便利ツール

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

## 使用方法

> [!note]
> 以下のコマンドはbootcampのリポジトリ内（サブディレクトリも可）で実行してください。

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

## 仕様

[SPEC.md](./SPEC.md)
