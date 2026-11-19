/* Quiz widget: <div class="quiz" data-answer="2"> with buttons in .opts and a hidden .why.
   A click marks the chosen option right or wrong, marks the right one, and shows the explanation. */
document.querySelectorAll('.quiz').forEach(function (quiz) {
  var answer = Number(quiz.dataset.answer);
  var buttons = quiz.querySelectorAll('.opts button');
  var why = quiz.querySelector('.why');
  buttons.forEach(function (btn, i) {
    btn.type = 'button';
    btn.addEventListener('click', function () {
      buttons.forEach(function (b) { b.classList.remove('right', 'wrong'); });
      buttons[answer].classList.add('right');
      if (i !== answer) btn.classList.add('wrong');
      if (why) why.hidden = false;
    });
  });
});

/* Legend: <div class="legend" data-legend="mode playbook arrow …"> becomes one row of swatches;
   data-label-<key>="…" replaces one key's meaning where a figure uses the mark for something narrower.
   Each key has one drawing and one meaning for the whole course; the swatches use the same
   classes as the figures, so a swatch looks exactly like the mark it explains. */
(function () {
  var box = function (k) { return '<g class="k-' + k + '"><rect class="box" x="1" y="2" width="30" height="12" rx="2"/></g>'; };
  var line = function (cls) {
    return '<line class="ar ' + cls + '" x1="1" y1="8" x2="25" y2="8"/><polygon class="head" points="25,4 31,8 25,12"/>';
  };
  var KEYS = {
    mode: [box('mode'), 'mode 技能'],
    playbook: [box('playbook'), 'playbook'],
    principle: [box('principle'), 'principle（原则技能）'],
    skill: [box('skill'), '其他技能'],
    reference: [box('reference'), 'references/ 里的文件'],
    script: [box('script'), 'scripts/ 里的程序'],
    agent: [box('agent'), 'subagent（子代理定义）'],
    config: [box('config'), 'rule（配置）'],
    other: [box('other'), '不是给 agent 读的，或不在 pstack 里'],
    decision: ['<polygon class="dia" points="16,1 31,8 16,15 1,8"/>', '菱形：一个判断，出口旁写条件'],
    end: ['<rect class="pill" x="1" y="2" width="30" height="12" rx="6"/>', '圆角条：开始或结束'],
    arrow: [line(''), '实线箭头：执行、读取或写出，旁边写明是什么'],
    attach: ['<path class="att" d="M1,8 L31,8"/>', '细灰虚线：这一步会用到它'],
    human: [line('human'), '点线箭头：你做的'],
    zone: ['<rect class="zone" x="1" y="1" width="30" height="14" rx="3"/>', '灰底区域：一组，标题写明是什么']
  };
  document.querySelectorAll('.legend[data-legend]').forEach(function (el) {
    var wanted = el.dataset.legend.split(/\s+/);
    el.innerHTML = '<b>' + (el.dataset.title || '图例') + '</b>' +Object.keys(KEYS).filter(function (k) { return wanted.indexOf(k) >= 0; }).map(function (k) {
      var d = KEYS[k], label = el.getAttribute('data-label-' + k) || d[1];
      return '<span class="it"><svg viewBox="0 0 32 16" aria-hidden="true">' + d[0] + '</svg>' + label + '</span>';
    }).join('');
  });
})();
