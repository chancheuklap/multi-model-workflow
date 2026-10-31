#!/usr/bin/env python3
"""Probe public App control and cross-process queues without touching real chats.

Run: python3 efforts/fix-1464/prototypes/app-control/EXP/probe.py --fixtures
Only --fixtures creates sessions, in throwaway homes using a local failing provider.
--enqueue-self explicitly queues a continuation to this chat through the public API.
"""

import argparse
import html
import http.server
import json
import os
from pathlib import Path
import queue
import shutil
import shlex
import signal
import subprocess
import tempfile
import threading
import time
import uuid


class Rpc:
    def __init__(self, command, env=None, cwd=None):
        self.events = []
        self.messages = queue.Queue()
        self.proc = subprocess.Popen(command, stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                     text=True, env=env, cwd=cwd, start_new_session=True)
        self.stderr = []
        threading.Thread(target=self._read, daemon=True).start()
        threading.Thread(target=self._errors, daemon=True).start()
        self.sequence = 0
        try:
            self.call('initialize', {'clientInfo': {'name': 'mmw_control_probe', 'version': '1'},
                                     'capabilities': {'experimentalApi': True}})
            self.write({'method': 'initialized'})
        except BaseException:
            self.close()
            raise

    def _read(self):
        for line in self.proc.stdout:
            self.messages.put(json.loads(line))
        self.messages.put(None)

    def _errors(self):
        self.stderr.extend(self.proc.stderr)

    def write(self, message):
        self.proc.stdin.write(json.dumps(message) + '\n')
        self.proc.stdin.flush()

    def receive(self, timeout):
        message = self.messages.get(timeout=timeout)
        if message is None:
            raise RuntimeError('public protocol connection closed')
        return message

    def call(self, method, params, timeout=20):
        self.sequence += 1
        request_id = self.sequence
        self.write({'id': request_id, 'method': method, 'params': params})
        deadline = time.monotonic() + timeout
        while True:
            message = self.receive(max(0.01, deadline - time.monotonic()))
            if message.get('id') == request_id:
                if 'error' in message:
                    raise RuntimeError(json.dumps(message['error']))
                return message['result']
            self.events.append(message)

    def close(self):
        self.proc.stdin.close()
        try:
            self.proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            os.killpg(self.proc.pid, signal.SIGTERM)
            try:
                self.proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                os.killpg(self.proc.pid, signal.SIGKILL)
                self.proc.wait()


def public_control(binary, socket_path, target):
    if not socket_path.exists():
        return {'operation': 'actual_app_control', 'outcome': 'no_public_socket',
                'target_loaded': False, 'socket': str(socket_path)}
    rpc = None
    try:
        rpc = Rpc([binary, 'app-server', 'proxy', '--sock', str(socket_path)])
        loaded = []
        cursor = None
        while True:
            page = rpc.call('thread/loaded/list', {'cursor': cursor})
            loaded.extend(page['data'])
            cursor = page.get('nextCursor')
            if not cursor:
                break
        return {'operation': 'actual_app_control',
                'outcome': 'target_loaded' if target in loaded else 'different_runtime',
                'target_loaded': target in loaded}
    except (RuntimeError, queue.Empty, BrokenPipeError) as error:
        return {'operation': 'actual_app_control', 'outcome': 'connection_failed',
                'error': str(error), 'target_loaded': False}
    finally:
        if rpc:
            rpc.close()


def desktop_transport():
    binary = os.environ.get('CODEX_APP_RUNTIME_CLI_PATH')
    transports = []
    if binary:
        processes = subprocess.check_output(['ps', '-axo', 'pid,ppid,args'], text=True)
        records = {}
        for line in processes.splitlines()[1:]:
            parts = line.strip().split(None, 2)
            if len(parts) != 3:
                continue
            records[parts[0]] = (parts[1], parts[2])
        app = [p for p in Path(binary).parents if p.suffix == '.app'][-1]
        app_executable = str(app / 'Contents' / 'MacOS' / app.stem)
        for pid, (parent, command) in records.items():
            args = shlex.split(command)
            if not args or args[0] != binary or 'app-server' not in args:
                continue
            parent_command = records.get(parent, ('', ''))[1]
            if not parent_command.startswith(app_executable):
                continue
            transport = 'stdio://'
            for index, arg in enumerate(args):
                if arg == '--listen' and index + 1 < len(args):
                    transport = args[index + 1]
                elif arg.startswith('--listen='):
                    transport = arg.split('=', 1)[1]
            sockets = subprocess.run(['lsof', '-a', '-p', pid, '-U', '-Fn'],
                                     capture_output=True, text=True)
            named = [item[1:] for item in sockets.stdout.splitlines()
                     if item.startswith('n/')]
            transports.append({'pid': int(pid), 'transport': transport,
                               'named_unix_sockets': named})
    return {'operation': 'desktop_runtime_transport', 'runtimes': transports}


def enqueue_self(binary):
    thread_id = os.environ['CODEX_THREAD_ID']
    marker = 'mmw-app-wake-' + str(uuid.uuid4())
    message = (
        f'MMW 后台自动唤醒实验，标记 {marker}。这是本对话自行安排的验证消息，'
        '不是用户的新要求。发送者通过官方 thread/queue/add 向本对话写入消息后退出，'
        '用于验证父回合结束后真实桌面 App 能否继续工作。'
        '先核对 .scratch/fix-1464/app-control/evidence/self-wake/results.json 的标记，'
        '记录本消息确实触发了新的 App 回合，再继续用户已授权的完整六步适配方案。'
        '所有改动仍由当前对话亲自完成，禁止派发实施 agent。'
        '续跑记录在 /tmp/mmw-app-control-continuation.md。')
    rpc = Rpc([binary, 'app-server'])
    try:
        queued = rpc.call('thread/queue/add', {
            'threadId': thread_id, 'clientUserMessageId': str(uuid.uuid4()),
            'input': [{'type': 'text', 'text': message}]})
    finally:
        rpc.close()
    return {'operation': 'self_wake', 'marker': marker, 'thread': thread_id,
            'queue_ack': bool(queued.get('queuedSubmission')),
            'submission_id': queued['queuedSubmission']['id'],
            'sender_pid': rpc.proc.pid, 'sender_exit_code': rpc.proc.returncode,
            'app_new_turn_observed': False}


def mcp_discovery(binary):
    with tempfile.TemporaryDirectory(prefix='mmw-public-mcp-') as work:
        rpc = Rpc([binary, '-c',
                   'plugins.codex-app-tools@openai-bundled.mcp_servers.codex_app.enabled=true',
                   'app-server'], cwd=work)
        try:
            result = rpc.call('mcpServerStatus/list',
                             {'serverName': 'codex_app', 'detail': 'toolsAndAuthOnly'},
                             timeout=25)
            return {'operation': 'public_mcp_discovery',
                    'app_binding_inherited': bool(os.environ.get('CODEX_APP_TOOLS_PIPE_PATH')),
                    'servers': [{'name': row['name'], 'tool_count': len(row.get('tools', {})),
                                 'startup_error': row.get('toolsError')}
                                for row in result['data']]}
        finally:
            rpc.close()


def fixture(binary):
    requests = queue.Queue()
    release_provider = threading.Event()
    request_count = 0

    class Provider(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            nonlocal request_count
            self.rfile.read(int(self.headers.get('Content-Length', 0)))
            request_count += 1
            requests.put(self.path)
            if request_count > 1:
                release_provider.wait(timeout=30)
            try:
                self.send_response(503)
                self.end_headers()
                self.wfile.write(b'isolated probe: no model is contacted')
            except (BrokenPipeError, ConnectionResetError):
                pass

        def log_message(self, *_):
            pass

    with tempfile.TemporaryDirectory(prefix='mmw-app-control-') as directory:
        root = Path(directory)
        home = root / 'home'
        work = root / 'work'
        home.mkdir()
        work.mkdir()
        provider = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Provider)
        threading.Thread(target=provider.serve_forever, daemon=True).start()
        (home / 'config.toml').write_text(
            'model = "mmw-fixture"\nmodel_provider = "fixture"\n'
            'disable_response_storage = true\n'
            '[model_providers.fixture]\nname = "MMW isolated fixture"\n'
            f'base_url = "http://127.0.0.1:{provider.server_port}"\n'
            'wire_api = "responses"\nrequest_max_retries = 0\n'
            'stream_max_retries = 0\nrequires_openai_auth = false\n')
        env = {'HOME': str(home), 'CODEX_HOME': str(home),
               'PATH': os.environ['PATH'], 'TMPDIR': directory}
        servers = []
        try:
            consumer = Rpc([binary, 'app-server'], env, work)
            servers.append(consumer)
            started = consumer.call('thread/start', {
                'cwd': str(work), 'model': 'mmw-fixture',
                'approvalPolicy': 'never', 'sandbox': 'read-only',
                'config': {'shell_environment_policy.set': {'MMW_PROBE': 'sentinel'}}})
            thread_id = started['thread']['id']
            loaded = consumer.call('thread/loaded/list', {})
            consumer.call('turn/start', {'threadId': thread_id,
                          'input': [{'type': 'text', 'text': 'MMW isolated initial turn'}]})
            deadline = time.monotonic() + 20
            while True:
                message = consumer.receive(max(0.01, deadline - time.monotonic()))
                if message.get('method') == 'turn/completed':
                    break
            while not requests.empty():
                requests.get_nowait()
            producer = Rpc([binary, 'app-server'], env, work)
            servers.append(producer)
            foreign_loaded = producer.call('thread/loaded/list', {})
            history = producer.call('thread/read', {'threadId': thread_id})
            queued = producer.call('thread/queue/add', {
                'threadId': thread_id, 'clientUserMessageId': str(uuid.uuid4()),
                'input': [{'type': 'text', 'text': 'MMW isolated queue sentinel'}]})
            producer.close()
            servers.remove(producer)
            deadline = time.monotonic() + 35
            turn = None
            while time.monotonic() < deadline and turn is None:
                try:
                    message = consumer.receive(deadline - time.monotonic())
                except queue.Empty:
                    break
                consumer.events.append(message)
                if message.get('method') == 'turn/started':
                    if message.get('params', {}).get('threadId') == thread_id:
                        turn = message['params']['turn']['id']
            controller = Rpc([binary, 'app-server'], env, work)
            servers.append(controller)
            stop = None
            local_request = False
            own_stop = False
            if turn:
                try:
                    requests.get(timeout=5)
                    local_request = True
                except queue.Empty:
                    pass
                try:
                    controller.call('turn/interrupt', {'threadId': thread_id, 'turnId': turn})
                    stop = 'accepted'
                except RuntimeError as error:
                    stop = str(error)
                consumer.call('turn/interrupt', {'threadId': thread_id, 'turnId': turn})
                deadline = time.monotonic() + 10
                while time.monotonic() < deadline:
                    message = consumer.receive(deadline - time.monotonic())
                    if message.get('method') == 'turn/completed':
                        own_stop = message['params']['turn']['status'] == 'interrupted'
                        break
            return {'operation': 'isolated_cross_process',
                    'binary': binary, 'version': subprocess.check_output(
                        [binary, '--version'], text=True).strip(),
                    'exact_cwd': started['cwd'] == str(work),
                    'model': started['model'], 'approval': started['approvalPolicy'],
                    'consumer_loaded': thread_id in loaded['data'],
                    'producer_loaded': thread_id in foreign_loaded['data'],
                    'history_visible_in_producer': history['thread']['id'] == thread_id,
                    'queue_ack': bool(queued.get('queuedSubmission')),
                    'producer_exited': producer.proc.returncode is not None,
                    'consumer_turn_started': turn is not None,
                    'local_provider_request': local_request,
                    'foreign_interrupt': stop,
                    'same_runtime_interrupt_confirmed': own_stop,
                    'desktop_app_tested': False}
        finally:
            release_provider.set()
            for rpc in reversed(servers):
                rpc.close()
            provider.shutdown()
            provider.server_close()


def evidence(output, results):
    output.mkdir(parents=True, exist_ok=True)
    (output / 'results.json').write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n')
    rows = ''.join('<tr><td>' + html.escape(row['operation']) + '</td><td><pre>' +
                   html.escape(json.dumps(row, ensure_ascii=False, indent=2)) + '</pre></td></tr>'
                   for row in results)
    (output / 'index.html').write_text('''<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>MMW App 控制入口实验</title><style>
:root{--paper:#2d3142;--ink:#f5f5f5;--muted:#bfc0c0;--rule:rgba(245,245,245,.12);--accent:#f08a59}
body{margin:32px;background:var(--paper);color:var(--ink);font:16px/1.6 system-ui,sans-serif;max-width:1400px}
h1{font:32px Georgia,serif}p{max-width:80ch}table{border-collapse:collapse;width:100%}
td,th{text-align:left;vertical-align:top;padding:16px;border-bottom:1px solid var(--rule)}
pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:14px}strong{color:var(--accent)}
.sequence{overflow-x:auto}svg{width:100%;min-width:840px;height:auto}
</style><h1>MMW App 控制入口实验</h1>
<p>检查公共控制 socket 是否连接到当前桌面会话，并在临时目录测试跨进程消息队列。
隔离实验只连接本地失败服务，不调用真实模型，不修改真实会话。</p>
<p><strong>通过标准</strong>：当前 App 会话必须在目标服务的已加载会话列表中。
另一服务能读取历史或写入队列，不能证明它能启动、停止当前 App 的会话。</p>
<h2>隔离实验的消息队列</h2><p>从上往下读。三个位置分别是独立发送进程、持久队列和持有会话的运行实例。
箭头表示请求和回执。图描述实验步骤，实际观察值在下方结果表。</p>
<div class="sequence"><svg viewBox="0 0 1240 400" role="img" aria-labelledby="sequence-title sequence-desc">
<title id="sequence-title">发送进程退出后，持有会话的运行实例读取队列</title>
<desc id="sequence-desc">发送进程将消息加入持久队列并收到回执，然后退出。持有会话的运行实例检查队列并启动新回合。</desc>
<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="8" refY="4" orient="auto">
<path d="M0 0L8 4L0 8Z" fill="#bfc0c0"/></marker></defs>
<g stroke="#949eb2" stroke-dasharray="4 4">
<path d="M200 88V376"/><path d="M620 88V376"/><path d="M1040 88V376"/></g>
<g fill="none" stroke="#bfc0c0" marker-end="url(#arrow)">
<path d="M200 136H620"/><path d="M620 192H200" stroke-dasharray="4 4"/>
<path d="M1040 264H620"/><path d="M620 320H1040" stroke-dasharray="4 4"/></g>
<g fill="#2d3142" stroke="#bfc0c0">
<rect x="80" y="24" width="240" height="64" rx="4"/>
<rect x="500" y="24" width="240" height="64" rx="4"/>
<rect x="920" y="24" width="240" height="64" rx="4"/>
<rect x="332" y="104" width="176" height="24" stroke="none"/>
<rect x="332" y="160" width="176" height="24" stroke="none"/>
<rect x="752" y="232" width="176" height="24" stroke="none"/>
<rect x="752" y="288" width="176" height="24" stroke="none"/></g>
<g fill="#f5f5f5" font-family="system-ui,sans-serif" font-size="20" text-anchor="middle">
<text x="200" y="64">发送进程</text><text x="620" y="64">持久队列</text>
<text x="1040" y="64">持有会话的运行实例</text>
<text x="420" y="124">加入测试消息</text><text x="420" y="180">返回队列回执</text>
<text x="200" y="232">发送进程退出</text><text x="840" y="252">检查外部队列</text>
<text x="840" y="308">读取测试消息</text><text x="1040" y="372">启动新回合</text></g>
</svg></div>
<table><thead><tr><th>检查对象</th><th>实际结果</th></tr></thead><tbody>''' + rows + '''</tbody></table>
<p>probe.py 的 public_control 使用官方 proxy 和 thread/loaded/list 核对运行实例。
fixture 在同一临时 HOME 启动两个服务，通过官方队列投递，再从另一个服务尝试停止。
所有实验进程在结束时退出。</p></html>''')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fixtures', action='store_true')
    parser.add_argument('--enqueue-self', action='store_true')
    parser.add_argument('--mcp-discovery', action='store_true')
    parser.add_argument('--binary', default=shutil.which('codex'))
    parser.add_argument('--socket', type=Path, default=Path.home() /
                        '.codex/app-server-control/app-server-control.sock')
    parser.add_argument('--target', default=os.environ.get('CODEX_THREAD_ID', ''))
    parser.add_argument('--output', type=Path, default=Path(
        '.scratch/fix-1464/app-control/evidence/public-control'))
    args = parser.parse_args()
    results = [desktop_transport(), public_control(args.binary, args.socket, args.target)]
    if args.fixtures:
        results.append(fixture(args.binary))
    if args.enqueue_self:
        results.append(enqueue_self(args.binary))
    if args.mcp_discovery:
        results.append(mcp_discovery(args.binary))
    evidence(args.output, results)
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
