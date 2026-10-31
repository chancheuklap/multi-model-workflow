## Problem
问题代号：retro-gather-replays-repository-history
角度：流程
发生了什么：独立票 #1480 的复盘 gather 为寻找旧收据和合并点，遍历全仓 mmw:spec/mmw:ticket 并逐张读取评论历史；同一 gather 的多个阶段还分别读取全仓 issue 列表。冻结版本 9e2c0f3e 的实现和当前产品副本均保留该路径。执行器观察到它读取不属于本票的 #1350、#1176 评论，最终成功完成。已有登记搜索未找到同因项；#1188 处理的是孤儿材料归属误报，#1219 处理的是常见词造成的相关登记误配，均不同于本项全仓历史读取成本。本次只证明一个 gather 会话的一次出现，保留为 candidate，不以循环中的多张历史票充当独立复发，不据此直接提案或改脚本。
证据：efforts/fix-641/retro/1480/gather-observation.md:7; efforts/fix-641/retro/1480/gather-observation.md:16; mmw-v4/skills/retro/scripts/retro.py:177; mmw-v4/skills/retro/scripts/retro.py:180; mmw-v4/skills/register-problem/scripts/register.py:100
代价：执行器记录这次单票收集耗时超过 12 分钟，最终两条流程材料仍是同一已解决合同事件。源码证实全仓历史与重复列表读取会随仓库历史增长而扩大；未记录总 HTTP 数，不能将全部耗时归因于该循环，也不能推出额度消耗或优化倍数。
该谁修：chancheuklap/multi-model-workflow
建议：未来单独按 Authoring or modifying a skill 检查 gather 中旧收据、合并点和统计的实际用途，先删除不改变本次复盘判断的历史遍历，再让保留阶段复用一次列表读取。保留当前运行材料完整性，不新增长期索引、守护流程或兜底层；本次只登记证据，不实施。
