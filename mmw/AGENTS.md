# mmw

上一代。冻结：不改、不加、不当事实。

- `mmw/install.sh` 没有 `--check`，跑了会把活的 `mmw-v2` 安装整个换成这一代。
- `bash mmw/test.sh` 已经跑不过（22 套里 4 套依赖的文件已删）；`mmw/skill-rebuilds/check-wiring.py` 启动即崩。
- agents-pi 与 codex/agents 两个目录是安装时渲染的产物，gitignore，不在树里。
