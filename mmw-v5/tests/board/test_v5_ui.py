from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
import tempfile
import unittest

from playwright.sync_api import expect, sync_playwright

from board_process import RunningBoard
import test_board_data as data
import test_settings as settings


def plain_spec():
    first = data.leaf(61, 'Produce the output', state='CLOSED')
    first['stateReason'] = 'COMPLETED'
    second = data.leaf(62, 'Use the output', blocked=[
        {'number':61, 'state':'CLOSED', 'stateReason':'COMPLETED'}])
    tree = data.container(60, 'V5 migration proof', [first,second], ['mmw:spec'])
    at=(datetime.now(timezone.utc)-timedelta(minutes=2)).isoformat(timespec='seconds').replace('+00:00','Z')
    started = data.event('worker.started',61,id=1,at=at,session='worker-61',runner='paseo',
        machine='fixture-machine',host='codex',model='test-model',effort='high',
        grade='junior-worker',worktree='/repo/.worktrees/issue-61',branch='issue-61',
        base='a'*40,into='batch')
    passed = data.event('ticket.passed',61,id=2,at=at,commit='b'*40,into='batch')
    landed = data.event('ticket.landed',61,id=3,at=at,commit='b'*40,into='batch')
    return {'repo':'fixture/v5-board','maps':[],
        'specs':[{'number':60,'title':'V5 migration proof','state':'OPEN','labels':[{'name':'mmw:spec'}]}],
        'trees':[tree],'comments':{'61':[
            {'etag':'"pending"','comments':[started,passed]},
            {'etag':'"landed"','comments':[started,passed,landed]}],
            '62':[{'etag':'"empty"','comments':[]}]},'comment_active':{'61':0,'62':0}}


class V5UserPath(unittest.TestCase):
    def test_plain_spec_dependency_refresh_and_settings_save(self):
        fixture=plain_spec()
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);home=root/'home';home.mkdir()
            (home/'models.json').write_text(json.dumps({**settings.config(), 'max_workers':2}))
            catalog=root/'catalog.json';catalog.write_text(json.dumps(settings.CATALOG))
            environment={'MMW_HOME':str(home),'MMW_HOST_CATALOG':str(catalog)}
            with RunningBoard(environment=environment,fixture=fixture) as board, sync_playwright() as pw:
                browser=pw.chromium.launch(headless=True)
                context=browser.new_context(viewport={'width':1440,'height':1000})
                context.tracing.start(screenshots=True,snapshots=True,sources=True)
                page=context.new_page();errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
                evidence=Path(os.environ['MMW_BOARD_EVIDENCE_DIR']) if os.environ.get('MMW_BOARD_EVIDENCE_DIR') else None
                if evidence:evidence.mkdir(parents=True,exist_ok=True)
                try:
                    page.goto(board.origin,wait_until='networkidle')
                    expect(page.locator('[data-ui="顶栏.brand.repo"]')).to_have_text('fixture/v5-board')
                    expect(page.locator('[data-ui="画布.ticket-card"]')).to_have_count(2)
                    expect(page.locator('.e-block.blocked')).to_have_count(1)
                    page.get_by_role('button',name='#61 Produce the output',exact=True).click()
                    expect(page.locator('[data-ui="详情.title"]')).to_have_text('Produce the output')
                    expect(page.get_by_text('issue-61',exact=True)).to_be_visible()
                    expect(page.get_by_role('button',name='map #60',exact=True)).to_have_count(0)
                    expect(page.locator('[data-ui="详情.event.text"]',has_text='bbbbbbb')).to_be_visible()
                    self.assertNotIn('criteria met',page.locator('[data-screen="detail"]').inner_text())
                    page.keyboard.press('F')
                    expect(page.locator('[data-ui="画布.ticket-card"]')).to_have_count(2)
                    self.assertFalse(page.evaluate('document.documentElement.scrollWidth > innerWidth'))
                    if evidence:page.screenshot(path=str(evidence/'ticket.png'),full_page=True)
                    board.write_fixture({**fixture,'comment_active':{'61':1,'62':0}})
                    page.get_by_role('button',name='立刻重读 GitHub',exact=True).click()
                    expect(page.locator('.e-block.done')).to_have_count(1)
                    expect(page.locator('[data-ui="详情.status.phase"]')).to_have_text('landed')
                    board.write_fixture({**fixture,'fail_all':True})
                    page.get_by_role('button',name='立刻重读 GitHub',exact=True).click()
                    expect(page.locator('[data-ui="顶栏.read-state"]')).to_contain_text('读 GitHub 失败')
                    expect(page.locator('[data-ui="画布.ticket-card"]')).to_have_count(2)
                    board.write_fixture({**fixture,'comment_active':{'61':1,'62':0}})
                    page.get_by_role('button',name='立刻重读 GitHub',exact=True).click()
                    expect(page.locator('[data-ui="顶栏.read-state"]')).not_to_contain_text('失败')
                    page.get_by_role('button',name='本机配置',exact=True).click()
                    expect(page.get_by_role('dialog',name='本机配置',exact=True)).to_be_visible()
                    expect(page.locator('[data-ui="本机配置.sheet.intro"]')).to_contain_text(str(home/'models.json'))
                    page.get_by_label('reviewer 的 model',exact=True).select_option('sonnet 5')
                    with page.expect_response(lambda response: response.url.endswith('/api/settings') and response.request.method=='PUT') as written:
                        page.get_by_role('button',name='保存',exact=True).click()
                    self.assertEqual(written.value.status,200)
                    expect(page.locator('[data-ui="本机配置.sheet.status"]')).to_contain_text('已保存')
                    saved=json.loads((home/'models.json').read_text())
                    self.assertEqual(saved['rows']['reviewer']['model'],'sonnet 5')
                    self.assertEqual(saved['max_workers'],2)
                    if evidence:page.screenshot(path=str(evidence/'settings.png'),full_page=True)
                    page.reload(wait_until='networkidle')
                    page.get_by_role('button',name='本机配置',exact=True).click()
                    expect(page.get_by_label('reviewer 的 model',exact=True)).to_have_value('sonnet 5')
                    self.assertEqual(errors,[])
                finally:
                    context.tracing.stop(path=str(evidence/'user-path.zip') if evidence else None)
                    browser.close()

    def test_missing_config_displays_api_guidance_at_the_settings_action(self):
        with RunningBoard(fixture=plain_spec()) as board, sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True)
            try:
                page=browser.new_page(viewport={'width':1280,'height':800})
                page.goto(board.origin,wait_until='networkidle')
                page.get_by_role('button',name='本机配置',exact=True).click()
                expect(page.get_by_role('dialog',name='本机配置',exact=True)).to_be_visible()
                expect(page.get_by_role('alert')).to_contain_text('init')
                page.keyboard.press('Escape')
                expect(page.get_by_role('dialog',name='本机配置',exact=True)).to_have_count(0)
            finally:browser.close()


if __name__=='__main__':unittest.main()
