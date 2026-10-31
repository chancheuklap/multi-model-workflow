// This adapter executes inside the calling session's tool runtime. It has no model
// or scheduler. The shell protocol continues only after a native operation replies.
(async function execute(tools, command, options = {}) {
  const quote = value => "'" + String(value).replaceAll("'", "'\\''") + "'";
  const unpack = result => {
    if (result.isError) throw new Error(JSON.stringify(result.content));
    const item = result.content.find(item => item.type === "text");
    if (!item) throw new Error("native operation returned no readable receipt");
    return JSON.parse(item.text);
  };
  const inspect = async args => {
    const result = unpack(await tools.mcp__codex_app__read_thread({
      threadId: args.session, hostId: "local", turnLimit: 1,
      includeOutputs: false, maxOutputCharsPerItem: 500}));
    return {session: result.thread.id, cwd: result.thread.cwd,
      state: result.thread.status.type,
      turn: result.turns[0] ? {id: result.turns[0].id, status: result.turns[0].status} : null};
  };
  const operations = {
    start: async args => {
      const argv = ["python3", args.helper, "prepare", "--cwd", args.cwd,
        "--model", args.model, "--effort", args.effort, "--title", args.title];
      if (args.skip_approval) argv.push("--skip-approval");
      let opened = await tools.exec_command({
        cmd: argv.map(quote).join(" "),
        yield_time_ms: 1000, max_output_tokens: 1000});
      let prepared = opened.output;
      while (opened.session_id)
      {
        opened = await tools.write_stdin({session_id: opened.session_id,
          chars: "", yield_time_ms: 1000, max_output_tokens: 1000});
        prepared += opened.output;
      }
      if (opened.exit_code !== 0)
        throw new Error("App chat preparation failed: " + prepared);
      const chat = JSON.parse(prepared.trim().split("\n").at(-1));
      const request = {threadId: chat.session, hostId: "local", prompt: args.prompt};
      if (args.model && args.model !== "inherit") request.model = args.model;
      if (args.effort && args.effort !== "inherit") request.thinking = args.effort;
      const created = unpack(await tools.mcp__codex_app__send_message_to_thread(request));
      if (created.threadId !== chat.session)
        throw new Error("App did not confirm the prepared independent chat");
      return {session: chat.session, cwd: args.cwd, state: "active"};
    },
    state: inspect,
    stop: async args => {
      const receipt = unpack(await tools.mcp__codex_app__set_thread_archived({
        threadId: args.session, hostId: "local", archived: true}));
      if (receipt.threadId !== args.session || receipt.archived !== true)
        throw new Error("App did not confirm archival of the requested chat");
      const after = await inspect(args);
      if (after.state !== "notLoaded" || after.turn?.status === "inProgress")
        throw new Error("App has not confirmed that the chat stopped");
      return {...after, stopped: true};
    }
  };
  const shell = "exec 3>&1 4<&0; export MMW_NATIVE_TOOLS=1; exec \"$@\"";
  const launch = ["bash", "-c", shell, "mmw-native", "bash", "-c", command]
    .map(quote).join(" ");
  let run = await tools.exec_command({cmd: launch, cwd: options.cwd,
    tty: true, yield_time_ms: 1000, max_output_tokens: 8000});
  let partial = "";
  let output = "";
  const replies = new Set();
  while (true) {
    partial += run.output;
    const lines = partial.split("\n");
    partial = lines.pop();
    let response = null;
    for (const raw of lines) {
      const line = raw.replace(/\r$/, "");
      if (!line.startsWith("MMW_NATIVE_REQUEST ")) {
        if (!replies.has(line)) output += line + "\n";
        continue;
      }
      const request = JSON.parse(line.slice("MMW_NATIVE_REQUEST ".length));
      try {
        const operation = operations[request.operation];
        if (!operation) throw new Error("unknown native runner operation");
        response = {id: request.id, ok: true,
          result: await operation(request.arguments)};
      } catch (error) {
        response = {id: request.id, ok: false, error: String(error)};
      }
    }
    if (!run.session_id) return {exitCode: run.exit_code, output: output + partial};
    const answer = response ? JSON.stringify(response) : "";
    if (answer) replies.add(answer);
    run = await tools.write_stdin({session_id: run.session_id,
      chars: answer ? answer + "\n" : "", yield_time_ms: 1000,
      max_output_tokens: 8000});
  }
})
