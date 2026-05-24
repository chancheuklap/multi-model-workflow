# review 规则

- Review scripts 对每条 lane 暴露稳定的 `submit/status/fetch/cancel` API。
- Baseline review 使用 native `codex exec review --json`，并把 Codex 返回的 `thread_id` 写入 job 文件。
- Targeted re-review 使用 `codex exec resume <thread_id>` 继续 baseline review session；找不到 completed baseline thread 时必须失败。
- 不保留 Claude Review lane；所有正式和 ad-hoc review 都走 Codex-native `review-lane.sh`。
- 文档 review 使用 `gpt-5.5` + `xhigh`。代码、bug、integration、final、release-risk review 使用 `gpt-5.4` + `xhigh`。
- `review-lane.sh` 统一负责模型路由；skill 正文不要另写一套临时模型选择。
