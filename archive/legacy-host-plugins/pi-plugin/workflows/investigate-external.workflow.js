export const meta = {
  name: 'investigate-external',
  description: '查外部方案:主线程传入 topics,每题一个只读 agent 并行查现有库/实现/最佳实践(web 搜索,locator=url),取证过滤后综合成带引用现状报告。只查外部,不碰仓库。适用:投查方向=外部资源(成熟案例/开源库/最佳实践),非必做;仓库现状另跑 investigate-internal。',
  phases: [
    { title: 'Investigate' },
    { title: 'Synthesize' },
  ],
}

// args.topics: [{ angle, question, skill? }]  —— 派几个 agent = 几个 topic,无上限,一题一 agent。
// args 可能以 JSON 字符串送达(Workflow 工具 args 编码差异),防御解析,不崩。
const A = (typeof args === 'string')
  ? (() => { try { return JSON.parse(args) } catch (e) { return {} } })()
  : (args || {})
const topicsInput = (typeof A.topics === 'string')
  ? (() => { try { return JSON.parse(A.topics) } catch (e) { return [] } })()
  : A.topics
const topics = Array.isArray(topicsInput) ? topicsInput : []
if (!topics.length) {
  throw new Error('investigate-external 需要 args.topics(非空),主线程先定好再传')
}

const TOPIC_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['topic', 'findings', 'summary', 'gaps'],
  properties: {
    topic: { type: 'string' },
    findings: {
      type: 'array',
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['claim', 'locator', 'confidence'],
        properties: {
          claim: { type: 'string', description: '一句话事实,不是判断/方案' },
          locator: { type: 'string', description: 'url。无凭据留空字符串' },
          confidence: { enum: ['high', 'medium', 'low'] },
        },
      },
    },
    summary: { type: 'string', description: '该专题现状,只摆事实不提方案' },
    gaps: { type: 'array', items: { type: 'string' }, description: '没查清/需用户补的缺口' },
  },
}

const REPORT_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['markdown', 'open_questions', 'spinoff_candidates'],
  properties: {
    markdown: { type: 'string', description: '带引用的现状报告(给 design 扎根用),只摆证据不拍方案' },
    open_questions: { type: 'array', items: { type: 'string' } },
    spinoff_candidates: {
      type: 'array',
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['tag', 'finding'],
        properties: {
          tag: { enum: ['bug', 'optimize', 'out-of-scope', 'needs-evaluation'] },
          finding: { type: 'string' },
        },
      },
      description: '查外部时撞到的旁路想法,候选 spinoff(主线程亲验后才登记)',
    },
  },
}

function topicPrompt(t) {
  const loadSkill = t.skill
    ? `先读该角度方法论 skill(用 read 读 ~/.agents/skills/${t.skill}/SKILL.md 并按其指引)再投查(引用,不照抄)。`
    : ''
  return [
    `你是 investigate 阶段的一名外部方案调查员,只查这一个专题,不查别的。`,
    `专题角度:${t.angle}`,
    `要回答:${t.question}`,
    loadSkill,
    `调查外部方案:现有库 / 已有实现 / 最佳实践。每条结论给 url;用 web 搜索/抓页工具取证。`,
    `红线:取证不判定——只摆事实和出处,绝不提方案、选 A/B、下设计结论(那是后面 design 的事)。`,
    `没查清的诚实写进 gaps,不要编。`,
    `返回结构化结果(schema 强制)。`,
  ].filter(Boolean).join('\n')
}

phase('Investigate')
const raw = await parallel(
  topics.map((t, i) => () =>
    agent(topicPrompt(t), {
      label: `external:${t.angle || ('topic-' + i)}`,
      phase: 'Investigate',
      schema: TOPIC_SCHEMA,
      // 模型对齐 agents-roster/investigate-topic.md(单一权威);pi 双厂商注册,取证用 GPT Sol
      model: 'openai-codex/gpt-5.6-sol:medium',
    })
  )
)

// 失败 topic 结构化留痕(可恢复失败已由 defaultAgentRetries 配置层重试;这里只收尸不重试):
// 主线程拿 skipped 里的 topic 原命令只传失败题重跑,成功题不再花 token。
const skipped = topics
  .map((t, i) => (raw[i] ? null : { angle: t.angle || ('topic-' + i), question: t.question, reason: 'agent 无结果(重试后仍失败)' }))
  .filter(Boolean)

// 取证过滤:机械丢无出处/低信心 claim(纯过滤,不让 agent 评判 agent)。被丢留痕进 dropped,不静默吞。
const verified = raw.filter(Boolean).map((r) => {
  const kept = r.findings.filter((f) => f.locator && f.locator.trim() && f.confidence !== 'low')
  const dropped = r.findings.filter((f) => !(f.locator && f.locator.trim()) || f.confidence === 'low')
  return { ...r, mode: 'external', findings: kept, dropped }
})

if (!verified.length) {
  return { topics: [], report: null, skipped, note: '所有专题 agent 都失败,无证据;主线程按 skipped 重跑或缩小范围' }
}

phase('Synthesize')
const synthPrompt = [
  '把下面各专题的外部方案调查证据综合成一份现状报告(markdown),供后续 design 扎根。',
  '规则:跨专题去重、把相关 finding 串起来、每条结论保留出处(url)。',
  '红线:只摆证据和现状,绝不替 design 拍方案、选路线。没查清的列进 open_questions。',
  '撞到的旁路想法提进 spinoff_candidates(候选,不是结论)。',
  '',
  '证据(JSON):',
  JSON.stringify(verified, null, 2),
].join('\n')

// 模型对齐 agents-roster/investigate-synthesizer.md(单一权威)
const report = await agent(synthPrompt, { label: 'synthesize', phase: 'Synthesize', schema: REPORT_SCHEMA, model: 'openai-codex/gpt-5.6-terra:high' })

// 返结构化证据 + 引用报告。主线程亲验承重事实(子代理是劳动力不是信源)后才写 docs/design/<slug>/investigating.md。
return { topics: verified, report, skipped }
