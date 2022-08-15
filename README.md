# NoteVN CLI

A [notevn.com](https://notevn.com) command line interface


### Installing

```sh

pip install nvnc

```

# CLI Usage

To save content to https://notevn.com/urlpath

```bash

nvnc -lo file_path urlpath

```

To track file changes, use the flag `--watch` or `-w`

Ví dụ

```bash

nvnc -owl file_path urlpath

```


To save the contents of the `urlpath` note to a local file path, use the following command

```

nvnc -g file_path urlpath 

```

Note: Using other flags with g flag is redundant

## Contributor

Thank to those people who has contributed to our project:

- Vi, Le Song
- Diu, Truong

## Issue tracking

[NoteVN CLI Issues](https://github.com/lesongvi/NoteVN_CLI/issues)
