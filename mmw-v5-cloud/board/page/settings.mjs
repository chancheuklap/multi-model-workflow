import {el, hand} from './shared.mjs';
export const fromPayload = value => ({saved:structuredClone(value),draft:structuredClone(value)});
export function unmount(host) { if(host._settingsEsc) document.removeEventListener('keydown',host._settingsEsc,true);host.replaceChildren(); }
export function renderReadError(host,message,hooks={}) {
  host.replaceChildren(el('div',{class:'settings-root board', 'data-screen':'settings'},el('div',{class:'scrim board'},el('div',{class:'sheet'},el('h2',{},'无法读取用户配置'),el('p',{role:'alert'},message),el('button',{type:'button',onClick:()=>{unmount(host);hooks.onClose?.();}},'关闭')))));
}
export function render(host, model, api, hooks={}) {
  const draft=model.draft;const close=()=>{unmount(host);hooks.onClose?.();};
  const nativeHost=model.saved.host;
  const fields=nativeHost==='cursor'?['model','effort','context','fast']:['model','effort'];
  const rows=Object.entries(draft.rows[nativeHost]).map(([role,row])=>el('tr',{},el('th',{scope:'row'},role),...fields.map(field=>el('td',{},el('input',field==='fast'
      ?{type:'checkbox',checked:row.fast,'aria-label':nativeHost+' '+role+' fast',onChange:e=>row.fast=e.target.checked}
      :{value:row[field]??'','aria-label':nativeHost+' '+role+' '+field,onInput:e=>row[field]=e.target.value})))));
  const group=el('section',{},el('h3',{},nativeHost==='codex'?'Codex':'Cursor'),el('table',{class:'set-table'},
      el('thead',{},el('tr',{},...['角色',...fields].map(field=>el('th',{scope:'col'},field)))),el('tbody',{},rows)));
  const status=el('p',{'aria-live':'polite'},'保存到用户目录，供此环境的所有项目共用；已派发的 agent 保持原设置。');
  const save=async()=>{const response=await hand(()=>api.saveSettings({rows:{[nativeHost]:draft.rows[nativeHost]}}));if(!response){status.textContent='保存失败：无法连接本地 board';return;}const answer=await response.json();status.textContent=response.ok?'已保存用户配置，后续派发使用新设置。':answer.error||'保存失败';};
  const sheet=el('div',{class:'sheet',role:'dialog','aria-modal':'true','aria-label':'用户模型配置'},
    el('div',{class:'sheet-head'},el('h2',{class:'title'},'用户模型配置'),el('button',{class:'iconbtn close',type:'button',onClick:close,'aria-label':'关闭'},'×')),
    el('div',{class:'sheet-body'},el('p',{class:'set-note'},model.saved.store),el('p',{class:'set-note'},'填写宿主原生工具支持的值；inherit 沿用宿主设置，不扫描本机 CLI。'),
      group),
    el('div',{class:'sheet-foot'},status,el('button',{type:'button',class:'btn primary',onClick:save},'保存')));
  host.replaceChildren(el('div',{class:'settings-root board','data-screen':'settings'},el('div',{class:'scrim board'},sheet)));
  host._settingsEsc=e=>{if(e.key==='Escape')close();};document.addEventListener('keydown',host._settingsEsc,true);return sheet;
}
