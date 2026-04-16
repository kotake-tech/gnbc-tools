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

- 課題のブランチを作成する
  ```sh
  gnbc branch
  ````
- テンプレをコピーする
  ```sh
  gnbc copy
  ```
- PRを作成する
  ```sh
  gnbc pr
  ```

## 仕様

[SPEC.md](./SPEC.md)
