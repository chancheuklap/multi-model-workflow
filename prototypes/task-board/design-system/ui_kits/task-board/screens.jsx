// The task board's five regions, composed from the design system's components and fed
// by the product's own logic (lib/board.js, the page modules of mmw-v2/board/page) and
// example data (data/, built by prototypes/task-board/553/UI/build_scenes.py).
const C = window.MMWTaskBoard2_34b698;
const M = window.MMW;

function TopBar({payload, now, settingsOpen, ui = "顶栏"}) {
  const v = M.topbar.fromBoard({...payload, settingsOpen}, new Date(now));
  const hot = v.orangeN > 0;
  const read = v.readFailed
    ? {failed: true, text: `读 GitHub 失败 · 下面是 ${v.readClock} 的数据（${v.readAgo} 分钟前）`}
    : {failed: false, text: v.readClock ? `只读 · ${v.readClock} 读取` : ""};
  return (
    <header className="topbar board" data-screen="topbar">
      <C.Brand repo={payload.repo} data-ui={`${ui}.brand`} />
      <div className="counters">
        <C.Counter button hot={hot} lamp={hot ? "orange" : "hollow"} label="needs you" count={v.orangeN}
          title="跳到下一张 needs you 的 ticket" data-ui={`${ui}.needs-you`} />
        <C.Counter lamp="green" label="running" count={v.greenN} sub={v.waiting ? `waiting for a slot ${v.waiting}` : null} data-ui={`${ui}.running`} />
        <C.Counter lamp="hollow" label="queued" count={v.hollowN} data-ui={`${ui}.queued`} />
        <C.Counter lamp="ink" label="done" count={v.inkN} data-ui={`${ui}.done`} />
      </div>
      <C.ReadState failed={read.failed} text={read.text} data-ui={`${ui}.read-state`} />
      <C.IconButton icon="refresh" label="立刻重读 GitHub" title="立刻重读 GitHub（页面开着时每分钟自动读一次）" data-ui={`${ui}.refresh`} />
      <C.IconButton icon="settings" on={settingsOpen} label="本机配置" title="本机配置：每个 agent 跑在哪个 host、model、effort" data-ui={`${ui}.settings`} />
    </header>
  );
}

function TaskList({tasks, selected, ui = "任务列表"}) {
  const v = M.tasks.taskListView(tasks, selected);
  return (
    <nav className="tasks board" aria-label="The Night" data-screen="tasks">
      <C.ColumnEyebrow label="The Night" count={v.count} data-ui={`${ui}.eyebrow`} />
      {v.empty ? <C.TasksEmpty data-ui={`${ui}.empty`} /> : null}
      {v.rows.map(row => <C.TaskRow key={row.n} row={row} data-ui={`${ui}.task`} />)}
    </nav>
  );
}

function Canvas({task, sel, width = 864, height = 848, ui = "画布"}) {
  if (!task) return <main className="canvas board" data-screen="canvas"><C.CanvasEmpty data-ui={`${ui}.empty`} /></main>;
  const v = M.canvas.canvasView(task, sel, [...M.defaultExpanded(task)], true);
  const kFit = Math.min((width - 40) / v.layout.W, (height - 70) / v.layout.H);
  const view = {k: Math.min(1.6, Math.max(0.3, Math.max(0.9, Math.min(1, kFit)))), x: 20, y: 12};
  const b = sel != null ? v.layout.nodes.find(node => node.id === sel) : null;
  if (b) {
    if ((b.y + b.h) * view.k + view.y > height - 70) view.y = Math.min(12, height * 0.45 - (b.y + b.h / 2) * view.k);
    if ((b.x + b.w) * view.k + view.x > width - 24) view.x = Math.min(20, width - 24 - (b.x + b.w) * view.k);
  }
  return (
    <main className="canvas board" data-screen="canvas" style={{width, height}}>
      <div className="world" style={{...v.worldSize, transform: `translate(${view.x}px, ${view.y}px) scale(${view.k})`}}>
        <C.Edges svg={v.svg} />
        {v.labels.map((label, i) => <C.LaneLabel key={`l${i}`} label={label} data-ui={`${ui}.lane-label`} />)}
        {v.containers.map(item => <C.ContainerCard key={item.n} item={item} data-ui={`${ui}.container-card`} />)}
        {v.decisions.map(item => <C.DecisionCard key={item.n} item={item} data-ui={`${ui}.decision-card`} />)}
        {v.tickets.map(item => <C.TicketCard key={item.n} item={item} data-ui={`${ui}.ticket-card`} />)}
      </div>
      <C.Legend data-ui={`${ui}.legend`} />
      <C.ZoomBar level={`${Math.round(view.k * 100)}%`} data-ui={`${ui}.zoom`} />
    </main>
  );
}

function Detail({payload, sel, ui = "详情"}) {
  const v = M.detail.fromBoard(payload, sel);
  if (v.empty) return <aside className="detail board" aria-label="详情"><C.DetailEmpty title={v.emptyTitle} text={v.emptyText} data-ui={`${ui}.empty`} /></aside>;
  if (v.kind === "ticket") {
    const held = rows => [...rows].sort((a, b) => Number(b.hold) - Number(a.hold));
    const blocks = v.phaseBlocks || [];
    return (
      <aside className="detail board" aria-label="详情">
        <div className="pv">
          <C.DetailHead ticket eyebrow={v.eyebrow} data-ui={`${ui}.head`} />
          <C.DetailTitle ticket title={v.title} data-ui={`${ui}.title`} />
          <C.Origin ticket num={v.num} links={v.links} data-ui={`${ui}.origin`} />
          <C.StatusLine ticket lamp={v.lamp} statusWord={v.statusWord} phase={v.phase} elapsed={v.elapsed} data-ui={`${ui}.status`} />
          <C.RunBox runtime={v.runtime} noRunText={v.noRunText} data-ui={`${ui}.runtime`} />
          {v.why.length ? <C.NeedsYou why={v.why} data-ui={`${ui}.why`} /> : null}
          {v.blockers.length ? <C.Section ticket title="Blocked by" note={v.blockers.length} data-ui={`${ui}.blocked-by`}>
            {held(v.blockers).map(row => <C.RelationRow ticket key={row.n} row={row} data-ui={`${ui}.blocker`} />)}</C.Section> : null}
          {v.blocks.length ? <C.Section ticket title="Blocking" note={v.blocks.length} data-ui={`${ui}.blocking`}>
            {held(v.blocks).map(row => <C.RelationRow ticket key={row.n} row={row} data-ui={`${ui}.blocks`} />)}</C.Section> : null}
          <C.Section ticket title="Events" note={v.eventCount} data-ui={`${ui}.events`}>
            {!(v.rawEvents.length || blocks.length) ? <C.NoneNote ticket text="no events yet" /> : null}
            {blocks.map((block, i) => (
              <C.EventBlock key={i} block={block} opened={block.openByDefault} data-ui={`${ui}.event-block`}>
                {block.items.map((item, j) => <C.EventRow key={j} item={item} data-ui={`${ui}.event`} />)}
              </C.EventBlock>
            ))}
          </C.Section>
          {v.kids.length ? <C.Section ticket title="Sub-issues" note={v.kids.length} data-ui={`${ui}.sub-issues`}>
            {v.kids.map((kid, i) => <C.SubIssueRow key={i} kid={kid} data-ui={`${ui}.sub-issue`} />)}</C.Section> : null}
        </div>
      </aside>
    );
  }
  const rows = (list, id) => list.map(row => <C.RelationRow key={row.n} row={row} data-ui={`${ui}.${id}`} />);
  return (
    <aside className="detail board" aria-label="详情">
      <div className="dp">
        <C.DetailHead eyebrow={v.eyebrow} data-ui={`${ui}.head`} />
        <C.Origin num={v.num} links={v.links} data-ui={`${ui}.origin`} />
        <C.DetailTitle title={v.title} data-ui={`${ui}.title`} />
        <C.StatusLine lamp={v.lamp} statusWord={v.statusWord} elapsed={v.elapsed} data-ui={`${ui}.status`} />
        {v.kind === "spec" || v.kind === "map" ? (
          <C.Section title={v.listTitle} note={v.listCount} data-ui={`${ui}.summary`}>
            <C.LampCounts lamps={v.lamps} data-ui={`${ui}.lamp-counts`} />
            <C.PhaseCounts phases={v.phases.map(p => ({phase: p.phase, label: p.label}))} data-ui={`${ui}.phase-counts`} />
          </C.Section>) : null}
        {v.kind === "spec" ? <C.Section title="By number" data-ui={`${ui}.by-number`}>{rows(v.ticketRows, "ticket-row")}</C.Section> : null}
        {v.kind === "map" ? <C.Section title="spec" note={v.specCount} data-ui={`${ui}.specs`}>{rows(v.specRows, "spec-row")}</C.Section> : null}
        {v.kind === "map" && v.decisionRows.length ? <C.Section title="Decision tickets" note={v.decisionCount} data-ui={`${ui}.decisions`}>{rows(v.decisionRows, "decision-row")}</C.Section> : null}
        {v.kind === "decision" ? [
          <C.Section key="a" title="Blocked by" note={v.blockers.length || null} data-ui={`${ui}.blocked-by`}>
            {rows(v.blockers, "blocker")}{!v.blockers.length ? <C.NoneNote text="none" /> : null}</C.Section>,
          <C.Section key="b" title="Blocking" note={v.blocks.length || null} data-ui={`${ui}.blocking`}>
            {rows(v.blocks, "blocks")}{!v.blocks.length ? <C.NoneNote text="none" /> : null}</C.Section>,
        ] : null}
        <C.GithubButton label={v.ghLabel} data-ui={`${ui}.github`} />
      </div>
    </aside>
  );
}

function Settings({scene = "mine", ui = "本机配置"}) {
  const model = M.settings.fromPayload(window.SETTINGS_SCENES[scene].payload);
  const v = M.settingsView(model.st, model.scan, model.catalog);
  return (
    <C.Sheet store={v.store} strong={v.strong} quiet={v.quiet} hatch={v.hatch} closeLabel={v.closeLabel}
      saveOff={v.saveOff} changed={v.changed} data-ui={ui}>
      {v.refused ? <C.RefusedBanner text={v.refusedText} data-ui={`${ui}.refused`} /> : null}
      <C.SetBlock title="本机的 host" data-ui={`${ui}.hosts`}
        aside={<C.ScanStatus scanning={v.scanning} scanningText={v.scanningText} scannedText={v.scannedText} data-ui={`${ui}.scan`} />}>
        <div className="hostscan">{v.chips.map(chip => <C.HostChip key={chip.host} chip={chip} data-ui={`${ui}.host`} />)}</div>
      </C.SetBlock>
      <C.SetBlock ruled data-ui={`${ui}.runner-block`}>
        <C.RunnerRow cls={v.runnerCls} value={v.runner} disabled={v.runnerOff} opts={v.runnerOpts} bads={v.runnerBads} data-ui={`${ui}.runner`} />
        <C.SetNote data-ui={`${ui}.runner-note`}>环境变量 <C.CodeText>MMW_RUNNER</C.CodeText> 设了时，它优先于这一格。「按所在环境判断」让 <C.CodeText>start</C.CodeText> 看自己跑在哪个 runner 里，判断不出时用 orca。runner 是 paseo 时，<C.CodeText>start</C.CodeText> 向 Paseo 要 model，所以换到 paseo 或从 paseo 换走，选项会重新扫描。</C.SetNote>
      </C.SetBlock>
      <C.SetBlock ruled title="一个 agent 一行" data-ui={`${ui}.roles-block`}>
        <C.RolesTable data-ui={`${ui}.roles`}>{v.rows.map(row => <C.RoleRow key={row.agent} row={row} data-ui={`${ui}.role`} />)}</C.RolesTable>
        <C.SetNote data-ui={`${ui}.initial-note`}>一台新机器第一次安装时，这里填的是 MMW 自带的初始值；之后只按这里选的跑，MMW 更新不会改它。</C.SetNote>
      </C.SetBlock>
    </C.Sheet>
  );
}

function Board({settingsOpen}) {
  const scene = window.BOARD_SCENES.morning;
  window.MMW_NOW = scene.now;
  const tasks = scene.payload.tasks;
  const task = tasks.find(t => t.n === scene.select.task);
  return (
    <main className="app-shell board" style={{height: 900}}>
      <div className="app-top"><TopBar payload={scene.payload} now={scene.now} settingsOpen={settingsOpen} /></div>
      <div className="app-slot"><TaskList tasks={tasks} selected={task.n} /></div>
      <div className="app-slot"><Canvas task={task} sel={scene.select.node} /></div>
      <div className="app-slot"><Detail payload={scene.payload} sel={scene.select.node} /></div>
      {settingsOpen ? <div className="app-sheet" style={{pointerEvents: "auto"}}><Settings /></div> : null}
    </main>
  );
}

function mount(element) {
  window.MMW_NOW = window.BOARD_SCENES.morning.now;
  ReactDOM.createRoot(document.getElementById("root")).render(element);
}

Object.assign(window, {TaskBoardScreens: {TopBar, TaskList, Canvas, Detail, Settings, Board, mount}});
