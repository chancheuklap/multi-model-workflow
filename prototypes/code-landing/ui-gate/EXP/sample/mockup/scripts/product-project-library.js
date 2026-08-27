  (function () {
    "use strict";

    var projects = {
      cleaner: {
        name: "山野净洗洁精",
        id: "PRJ-240716-C08",
        art: "art-cleaner",
        subjectCount: 2,
        taskCount: 4
      },
      lotion: {
        name: "绒雾身体乳",
        id: "PRJ-240629-D04",
        art: "art-bag",
        subjectCount: 1,
        taskCount: 3
      },
      tea: {
        name: "暮山冷泡茶",
        id: "PRJ-240618-F21",
        art: "art-kettle",
        subjectCount: 2,
        taskCount: 2
      },
      lamp: {
        name: "暖光护眼台灯",
        id: "PRJ-240805-A17",
        art: "art-lamp",
        subjectCount: 1,
        taskCount: 0
      }
    };

    var entryQuery = new URLSearchParams(window.location.search);
    var requestedScenario = entryQuery.get("scenario") || "";
    var requestedWorkspaceView = entryQuery.get("view") || "";
    var appReadyFixture = {
      signedIn: true,
      productDisplayName: "变色龙商品图助手",
      workspaceName: "商品项目库",
      walletBalance: 12480
    };
    var loginScenarios = {
      "app-checking": {
        state: "checking",
        tone: "progress",
        eyebrow: "登录变色龙商品图助手",
        title: "正在确认登录状态",
        description: "请稍候。确认完成后，应用会继续下一步。",
        detail: "检查期间不会显示商品项目、自由模式或鸭豆余额。"
      },
      "app-login-required": {
        state: "login-required",
        tone: "neutral",
        eyebrow: "需要登录",
        title: "登录变色龙商品图助手",
        description: "登录会在卡皮巴拉浏览器页面完成。这里不需要输入激活码、许可证或机器凭证。",
        detail: "卡皮巴拉会处理账号登录、许可证分配和当前电脑确认。",
        primaryLabel: "登录",
        primaryAction: "start-login"
      },
      "app-awaiting-browser": {
        state: "awaiting-browser",
        tone: "progress",
        eyebrow: "等待浏览器登录",
        title: "请在卡皮巴拉页面完成登录",
        description: "应用会自动检查登录结果。回到本窗口时会立即检查一次。",
        detail: "如果登录页面没有显示，可以重新打开当前登录页面。",
        primaryLabel: "重新打开登录页面",
        primaryAction: "reopen-login"
      },
      "app-capybara-unreachable": {
        state: "capybara-unreachable",
        tone: "danger",
        eyebrow: "无法连接卡皮巴拉",
        title: "登录页面暂时无法打开",
        description: "本机未能建立登录请求，或系统浏览器没有打开登录页面。",
        detail: "请检查网络连接后重试。当前不会显示任何客户组织数据。",
        primaryLabel: "重试",
        primaryAction: "start-login"
      },
      "app-login-failed": {
        state: "login-failed",
        tone: "danger",
        eyebrow: "登录失败",
        title: "这次登录没有完成",
        description: "本机启动或登录回调没有完成。当前登录结果不会进入商品项目库。",
        detail: "重新登录会建立新的登录请求，并打开新的卡皮巴拉页面。",
        primaryLabel: "重新登录",
        primaryAction: "restart-login"
      },
      "app-login-incomplete": {
        state: "login-incomplete",
        tone: "warning",
        eyebrow: "登录未完成",
        title: "登录等待已经结束",
        description: "原登录记录已经过期，或应用已经停止等待原登录结果。",
        detail: "重新登录会建立新的登录请求。应用不会静默停在当前页面。",
        primaryLabel: "重新登录",
        primaryAction: "restart-login"
      },
      "app-account-change-blocked": {
        state: "account-change-blocked",
        tone: "warning",
        eyebrow: "换号受阻",
        title: "暂时不能使用另一账号",
        description: "当前客户组织还有 3 笔账务没有收口。完成处理前，其他账号不能替换当前身份。",
        detail: "重新登录原账号不受这项门禁阻止。登录后可以继续处理原客户组织的账务。",
        primaryLabel: "重新登录原账号",
        primaryAction: "restore-original-account"
      },
      "app-upgrade-required": {
        state: "upgrade-required",
        tone: "warning",
        eyebrow: "需要更新应用",
        title: "请联系管理员更新应用",
        description: "当前版本是 0.9.4，最低支持版本是 1.0.0。这个版本无法使用当前服务配置。",
        detail: "请联系管理员获取新版安装包。更新完成前不能进入商品项目库。"
      }
    };
    var serviceStatusScenarios = {
      "app-service-unavailable": {
        state: "service-unavailable",
        tone: "error",
        label: "服务不可用",
        title: "服务配置不完整",
        detail: "变色龙暂时不能开始新的生成任务。已有商品项目和商品任务仍可查看。"
      },
      "app-service-config-sync": {
        state: "service-config-sync",
        tone: "warning",
        label: "服务配置同步中",
        title: "正在同步服务配置",
        detail: "应用正在重新获取服务配置。完成前不能开始新的生成任务。",
        recoverAutomatically: true
      }
    };
    loginScenarios["app-login-blocking"] = loginScenarios["app-login-required"];
    var globalFeedbackScenarios = {
      "ux-realtime-disconnected": {
        state: "realtime-disconnected",
        tone: "warning",
        label: "正在恢复连接",
        title: "正在恢复实时连接",
        detail: "当前仍显示最后一次可信的任务和图片状态。连接中断不会把任务标记为失败。"
      },
      "ux-realtime-consistent": {
        state: "realtime-consistent",
        tone: "ready",
        label: "服务正常",
        title: "实时状态已恢复",
        detail: "当前页面已经显示服务端最新的任务和图片状态。较早的状态不会覆盖当前结果。"
      },
      "ux-safe-error": {
        state: "safe-error",
        tone: "error",
        title: "这次操作没有完成",
        detail: "生成服务暂时无法处理这次请求。当前内容已经保留，请按页面中的原有入口重试。"
      }
    };
    var existingProjectId = entryQuery.get("project");
    var existingProjectKey = Object.keys(projects).find(function (key) { return projects[key].id === existingProjectId; });
    var existingProject = existingProjectKey ? projects[existingProjectKey] : null;
    var entryFlow = entryQuery.get("flow");
    if (!existingProject && entryFlow === "confirm-material" && existingProjectId) {
      existingProject = { name: entryQuery.get("name") || "新商品项目", id: existingProjectId, art: "art-cleaner", subjectCount: 0, taskCount: 0 };
    }
    var isExistingProjectMaterialFlow = entryFlow === "add-material" && Boolean(existingProject);
    var subjectConfirmationScenarios = [
      "subject-boundary-edit", "subject-boundary-missing", "subject-full-image", "subject-brand-boxes",
      "subject-confirm-one", "subject-multiple", "subject-last", "subject-abandon", "copy-back-subject"
    ];
    var analysisComplete = entryQuery.get("analysisComplete") === "1" || subjectConfirmationScenarios.indexOf(requestedScenario) >= 0;
    var isSubjectAnalysisFlow = entryFlow === "confirm-material" && Boolean(existingProject) && !analysisComplete;
    var isSubjectConfirmationFlow = entryFlow === "confirm-material" && Boolean(existingProject) && analysisComplete;
    var requestedMaterialFunction = entryQuery.get("materialFunction") || "marketing";
    var requestedSetCount = Number(entryQuery.get("setCount")) || 1;
    var requestedCopyTreatment = entryQuery.get("copyTreatment") || "";
    var requestedReferenceAdded = entryQuery.get("referenceAdded") === "1";
    var requestedReferenceAspects = entryQuery.get("referenceAspects") || "";
    var selectedProject = "cleaner";
    var library = document.getElementById("product-library");
    var createProject = document.getElementById("product-create");
    var subjectAnalysis = document.getElementById("product-subject-analysis");
    var subjectAnalysisHeading = document.getElementById("subject-analysis-heading");
    var subjectAnalysisTotal = document.getElementById("subject-analysis-total");
    var subjectAnalysisMaterialState = document.getElementById("subject-analysis-material-state");
    var subjectAnalysisProgress = document.querySelector(".subject-analysis-progress");
    var subjectAnalysisDetail = document.getElementById("subject-analysis-detail");
    var subjectAnalysisActions = document.getElementById("subject-analysis-actions");
    var subjectAbandonDialog = document.getElementById("subject-abandon-dialog");
    var subjectAbandonTitle = document.getElementById("subject-abandon-title");
    var subjectAbandonDescription = document.getElementById("subject-abandon-description");
    var keepSubjectTask = document.getElementById("keep-subject-task");
    var confirmAbandonSubjectTask = document.getElementById("confirm-abandon-subject-task");
    var subjectAbandonIsNewProject = false;
    var subjectConfirm = document.getElementById("product-subject-confirm");
    var freeMode = document.getElementById("product-free-mode");
    var settings = document.getElementById("product-settings");
    var defaultExportPath = document.getElementById("default-export-path");
    var settingsSavedState = document.getElementById("settings-saved-state");
    var titleContext = document.getElementById("product-title-context");
    var toast = document.getElementById("selection-toast");
    var toastTimer;
    var gatewayBillingResult = requestedScenario === "billing-debt-gate" ? "insufficient_balance" : "";
    var billingDebtGateActive = gatewayBillingResult === "insufficient_balance";
    var billingDebtDialog = document.getElementById("billing-debt-dialog");
    var billingDebtLater = document.getElementById("billing-debt-later");
    var billingDebtRecharge = document.getElementById("billing-debt-recharge");
    var dialogReturnFocus = new WeakMap();

    function openModal(dialog, initialFocus) {
      if (!dialog) return;
      if (!dialog.open) {
        dialogReturnFocus.set(dialog, document.activeElement);
        dialog.showModal();
      }
      window.requestAnimationFrame(function () {
        var target = initialFocus || dialog.querySelector("button:not([hidden]):not([disabled]), input:not([hidden]):not([disabled]), select:not([hidden]):not([disabled]), textarea:not([hidden]):not([disabled])");
        if (target) target.focus({ preventScroll: true });
      });
    }

    document.querySelectorAll("dialog").forEach(function (dialog) {
      dialog.addEventListener("close", function () {
        var target = dialogReturnFocus.get(dialog);
        dialogReturnFocus.delete(dialog);
        if (target && target.isConnected && !target.disabled) {
          window.requestAnimationFrame(function () { target.focus({ preventScroll: true }); });
        }
      });
    });

    function openBillingDebtGate() {
      if (!billingDebtGateActive || gatewayBillingResult !== "insufficient_balance") return false;
      openModal(billingDebtDialog, billingDebtLater);
      return true;
    }

    billingDebtLater.addEventListener("click", function () {
      billingDebtDialog.close();
    });

    billingDebtRecharge.addEventListener("click", function () {
      billingDebtGateActive = false;
      document.getElementById("wallet-balance").textContent = "12,480";
      billingDebtDialog.close();
      showToast("欠费已结清，可以继续生成。");
    });

    function setSubjectAnalysisFailed(failed) {
      subjectAnalysis.classList.toggle("failed", failed);
      subjectAnalysisHeading.textContent = failed ? "这张商品素材暂时无法分析" : "正在分析商品素材";
      subjectAnalysisTotal.textContent = failed ? "分析失败" : "进度 1 / 1";
      subjectAnalysisMaterialState.textContent = failed ? "分析失败" : "分析中";
      subjectAnalysisProgress.hidden = failed;
      subjectAnalysisDetail.textContent = failed
        ? "商品素材和生成任务设置已保留。你可以重新分析。"
        : "正在生成商品主体边界建议和去品牌标记框建议。";
      subjectAnalysisActions.hidden = !failed;
    }

    function openSubjectAbandonDialog(context) {
      subjectAbandonIsNewProject = entryQuery.get("projectOrigin") === "new" || (existingProject && existingProject.id === "PRJ-240806-N01");
      if (subjectAbandonIsNewProject) {
        subjectAbandonTitle.textContent = "放弃这次任务并删除新商品项目？";
        subjectAbandonDescription.textContent = "“" + existingProject.name + "”商品项目会被删除。";
        confirmAbandonSubjectTask.textContent = "放弃并删除项目";
      } else {
        subjectAbandonTitle.textContent = "放弃这次任务？";
        subjectAbandonDescription.textContent = context === "analysis"
          ? "当前生成任务设置和这张商品素材会被删除。商品主体图库不会改变。"
          : "当前生成任务设置和本次新增的商品主体图会被删除。任务开始前已有的商品主体图会继续保留。";
        confirmAbandonSubjectTask.textContent = "放弃这次任务";
      }
      keepSubjectTask.textContent = context === "analysis" ? "继续重新分析" : "继续确认商品主体";
      openModal(subjectAbandonDialog, keepSubjectTask);
    }

    document.getElementById("retry-subject-analysis").addEventListener("click", function () {
      setSubjectAnalysisFailed(false);
    });

    document.getElementById("abandon-subject-analysis").addEventListener("click", function () {
      openSubjectAbandonDialog("analysis");
    });

    keepSubjectTask.addEventListener("click", function () {
      subjectAbandonDialog.close();
    });

    confirmAbandonSubjectTask.addEventListener("click", function () {
      if (!existingProject) return;
      window.location.href = subjectAbandonIsNewProject
        ? "index.html?scenario=library-populated"
        : "product-workbench.html?project=" + encodeURIComponent(existingProject.id);
    });

    subjectAbandonDialog.addEventListener("click", function (event) {
      if (event.target === subjectAbandonDialog) subjectAbandonDialog.close();
    });

    function renderAppReadyScenario() {
      if (requestedScenario !== "app-ready" || !appReadyFixture.signedIn) return;
      document.body.dataset.appState = "ready";
      document.getElementById("product-display-name").textContent = appReadyFixture.productDisplayName;
      titleContext.textContent = appReadyFixture.workspaceName;
      document.getElementById("wallet-balance").textContent = appReadyFixture.walletBalance.toLocaleString("zh-CN");
    }

    var productApp = document.getElementById("product-app");
    var workspace = document.querySelector(".workspace");
    var loginGate = document.getElementById("login-gate");
    var loginGateCard = document.getElementById("login-gate-card");
    var loginGatePrimary = document.getElementById("login-gate-primary");
    var loginGateExit = document.getElementById("login-gate-exit");
    var loginGateFeedback = document.getElementById("login-gate-feedback");
    var serviceStatus = document.getElementById("service-status");
    var serviceStatusLabel = document.getElementById("service-status-label");
    var globalStatusBar = document.getElementById("global-status-bar");
    var globalStatusTitle = document.getElementById("global-status-title");
    var globalStatusDetail = document.getElementById("global-status-detail");
    var currentLoginScenario = null;

    function setServiceDependentControlsDisabled(disabled) {
      var controls = [document.getElementById("new-project-card")].concat(
        Array.from(document.querySelectorAll('[data-workspace-tab="free-mode"]'))
      );
      controls.forEach(function (control) {
        if (!control) return;
        control.disabled = disabled;
        if (disabled) {
          control.title = "服务恢复后可以使用";
        } else {
          control.removeAttribute("title");
        }
      });
    }

    function renderServiceStatusScenario(scenario) {
      document.body.dataset.appState = scenario.state;
      productApp.classList.add("service-status-visible");
      serviceStatus.className = "service-status " + scenario.tone;
      serviceStatusLabel.textContent = scenario.label;
      globalStatusBar.className = "global-status-bar " + scenario.tone;
      globalStatusTitle.textContent = scenario.title;
      globalStatusDetail.textContent = scenario.detail;
      globalStatusBar.hidden = false;
      setServiceDependentControlsDisabled(true);
      if (scenario.recoverAutomatically) {
        window.setTimeout(function () {
          document.body.dataset.appState = "ready";
          productApp.classList.remove("service-status-visible");
          serviceStatus.className = "service-status ready";
          serviceStatusLabel.textContent = "服务正常";
          globalStatusBar.hidden = true;
          setServiceDependentControlsDisabled(false);
          showToast("服务配置已同步，可以开始新的生成任务。");
        }, 2600);
      }
    }

    function renderGlobalFeedbackScenario(scenario) {
      document.body.dataset.appState = scenario.state;
      productApp.classList.add("service-status-visible");
      if (scenario.label) {
        serviceStatus.className = "service-status " + scenario.tone;
        serviceStatusLabel.textContent = scenario.label;
      }
      globalStatusBar.className = "global-status-bar " + scenario.tone;
      globalStatusTitle.textContent = scenario.title;
      globalStatusDetail.textContent = scenario.detail;
      globalStatusBar.hidden = false;
    }

    function renderLoginScenario(scenario) {
      currentLoginScenario = scenario;
      document.body.dataset.appState = scenario.state;
      productApp.classList.add("login-blocked");
      workspace.setAttribute("aria-hidden", "true");
      loginGate.hidden = false;
      loginGateCard.dataset.tone = scenario.tone;
      document.getElementById("login-gate-eyebrow").textContent = scenario.eyebrow;
      document.getElementById("login-gate-title").textContent = scenario.title;
      document.getElementById("login-gate-description").textContent = scenario.description;
      var detail = document.getElementById("login-gate-detail");
      detail.textContent = scenario.detail || "";
      detail.hidden = !scenario.detail;
      loginGateFeedback.hidden = true;
      loginGateFeedback.textContent = "";
      loginGatePrimary.hidden = !scenario.primaryLabel;
      loginGatePrimary.textContent = scenario.primaryLabel || "";
      loginGatePrimary.dataset.action = scenario.primaryAction || "";
      loginGateExit.disabled = false;
      loginGateExit.textContent = "退出应用";
      window.requestAnimationFrame(function () {
        (scenario.primaryLabel ? loginGatePrimary : loginGateExit).focus({ preventScroll: true });
      });
    }

    function showWaitingForBrowser(message) {
      var waiting = Object.assign({}, loginScenarios["app-awaiting-browser"]);
      if (message) waiting.detail = message;
      renderLoginScenario(waiting);
    }

    if (loginScenarios[requestedScenario]) {
      renderLoginScenario(loginScenarios[requestedScenario]);
    } else if (serviceStatusScenarios[requestedScenario]) {
      renderServiceStatusScenario(serviceStatusScenarios[requestedScenario]);
    } else if (globalFeedbackScenarios[requestedScenario]) {
      renderGlobalFeedbackScenario(globalFeedbackScenarios[requestedScenario]);
    } else {
      renderAppReadyScenario();
    }

    if (requestedScenario === "library-empty") {
      document.body.dataset.libraryState = "empty";
      document.querySelectorAll("#project-grid .project-card").forEach(function (card) {
        card.hidden = true;
      });
    }

    loginGatePrimary.addEventListener("click", function () {
      if (!currentLoginScenario) return;
      if (loginGatePrimary.dataset.action === "reopen-login") {
        loginGateFeedback.textContent = "已重新打开当前卡皮巴拉登录页面。";
        loginGateFeedback.hidden = false;
        return;
      }
      if (loginGatePrimary.dataset.action === "restore-original-account") {
        showWaitingForBrowser("已为原账号建立新的登录请求。请在卡皮巴拉页面完成登录。 ");
        return;
      }
      showWaitingForBrowser("已建立新的登录请求。请在卡皮巴拉页面完成登录。");
    });

    loginGateExit.addEventListener("click", function () {
      loginGateFeedback.textContent = "正式应用将在这里退出。Prototype 保留页面，便于继续走查。";
      loginGateFeedback.hidden = false;
      loginGateExit.textContent = "已请求退出";
      loginGateExit.disabled = true;
    });

    loginGate.addEventListener("keydown", function (event) {
      if (event.key === "Escape") {
        event.preventDefault();
        return;
      }
      if (event.key !== "Tab") return;
      var focusable = [loginGateExit, loginGatePrimary].filter(function (button) { return !button.hidden && !button.disabled; });
      if (!focusable.length) return;
      var first = focusable[0];
      var last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    });

    function showToast(message) {
      window.clearTimeout(toastTimer);
      toast.textContent = message;
      toast.classList.add("active");
      toastTimer = window.setTimeout(function () { toast.classList.remove("active"); }, 2400);
    }

    var freeHistoryGrid = document.getElementById("free-history-grid");
    var freeHistoryCount = document.getElementById("free-history-count");
    var freeImagePreviewDialog = document.getElementById("free-image-preview-dialog");
    var freeImagePreviewTitle = document.getElementById("free-image-preview-title");
    var freeImagePreviewLarge = document.getElementById("free-image-preview-large");
    var activeFreeImage = null;
    var freeRuns = [
      { id: "FREE-QUEUED", state: "queued", time: "今天 16:18", ratio: "3:4", requested: 2, prompt: "把商品放在清晨的厨房台面上，保留包装完整。", inputName: "商品图片_洗洁精.jpg", removeLogo: false, itemStates: ["pending", "pending"] },
      { id: "FREE-RUNNING", state: "running", time: "今天 15:42", ratio: "4:3", requested: 2, prompt: "深色书桌与暖色台灯，突出安静专注的夜间阅读氛围。", inputName: "暖光台灯.jpg", removeLogo: false, itemStates: ["delivered", "generating"] },
      { id: "FREE-COMPLETED", state: "completed", time: "今天 14:26", ratio: "3:4", requested: 4, prompt: "柔和晨光下的浴室台面，保留瓶身完整，背景干净并带少量水汽。", inputName: "身体乳.jpg", removeLogo: true, itemStates: ["delivered", "delivered", "delivered", "delivered"] },
      { id: "FREE-PARTIAL", state: "partial", time: "昨天 19:08", ratio: "1:1", requested: 4, prompt: "透明果汁瓶漂浮在冰块与柑橘切片之间，明亮夏日光线。", inputName: "透明果汁.jpg", removeLogo: false, failureKind: "service", itemStates: ["delivered", "delivered", "failed", "ungenerated"] },
      { id: "FREE-FAILED", state: "failed", time: "07-30 11:22", ratio: "1:1", requested: 2, prompt: "透明玻璃杯放在浅色石材桌面，午后侧光和简洁背景。", inputName: "玻璃杯.jpg", removeLogo: false, failureKind: "service", itemStates: ["failed", "failed"] }
    ];

    function escapeFreeHtml(value) {
      return String(value).replace(/[&<>"']/g, function (character) {
        return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[character];
      });
    }

    function freeRunStatus(state) {
      if (state === "queued") return { label: "排队中", className: "running" };
      if (state === "running") return { label: "进行中", className: "running" };
      if (state === "completed") return { label: "已完成", className: "done" };
      if (state === "partial") return { label: "部分完成", className: "failed" };
      return { label: "失败", className: "failed" };
    }

    function freeImageState(state) {
      if (state === "delivered") return { label: "已交付", className: "delivered", detail: "图片已经保存到当前电脑" };
      if (state === "generating") return { label: "生成中", className: "generating", detail: "完成后会自动显示" };
      if (state === "failed") return { label: "已失败", className: "failed", detail: "生成服务暂时不可用" };
      if (state === "ungenerated") return { label: "未生成", className: "ungenerated", detail: "本次记录结束前没有再次生成" };
      return { label: "待生成", className: "pending", detail: "轮到这张图片时自动开始" };
    }

    function renderFreeRunImage(run, itemState, index) {
      var state = freeImageState(itemState);
      var tone = index % 3 === 1 ? " warm" : index % 3 === 2 ? " cool" : "";
      var visual = itemState === "delivered"
        ? '<div class="free-run-image"><span class="free-history-image' + tone + '"></span></div>'
        : '<div class="free-run-placeholder ' + state.className + '"><strong>' + (itemState === "generating" ? "图片生成中" : state.label) + '</strong>' +
          (itemState === "generating" ? '<span class="free-run-progress" role="progressbar" aria-label="当前图片正在生成"><i></i></span>' : '') + '</div>';
      var actions = itemState === "delivered"
        ? '<div class="free-run-output-actions"><button type="button" data-free-preview="' + run.id + '" data-free-image-index="' + index + '">查看</button><button type="button" data-free-export="' + run.id + '" data-free-image-index="' + index + '">导出</button></div>'
        : '';
      return '<article class="free-run-output state-' + state.className + '">' + visual +
        '<div class="free-run-output-copy"><div><strong>成图 ' + (index + 1) + '</strong><span class="free-run-image-state ' + state.className + '">' + state.label + '</span></div><small>' + state.detail + '</small>' + actions + '</div></article>';
    }

    function renderFreeSettlement(run) {
      var delivered = run.itemStates.filter(function (state) { return state === "delivered"; }).length;
      var held = run.requested * 20;
      var terminal = ["completed", "partial", "failed"].indexOf(run.state) >= 0;
      return '<div class="free-run-settlement"><div><span>预扣额度</span><strong>' + run.requested + ' 张 · ' + held + ' 鸭豆</strong></div>' +
        '<div><span>实际结算</span><strong>' + (terminal ? delivered + ' 张 · ' + (delivered * 20) + ' 鸭豆' : "等待完成") + '</strong></div>' +
        '<div><span>已释放</span><strong>' + (terminal ? (run.requested - delivered) + ' 张 · ' + ((run.requested - delivered) * 20) + ' 鸭豆' : "等待完成") + '</strong></div></div>';
    }

    function renderFreeRun(run) {
      var status = freeRunStatus(run.state);
      var delivered = run.itemStates.filter(function (state) { return state === "delivered"; }).length;
      var failedCount = run.itemStates.filter(function (state) { return state === "failed" || state === "ungenerated"; }).length;
      var stateMessage = run.state === "queued"
        ? '<div class="free-run-message queued"><strong>轮到它时自动开始生成，不需要你再点一次。</strong><span>这条记录已经进入队列。你可以离开自由模式去做别的事。</span></div>'
        : run.state === "running"
          ? '<div class="free-run-message running"><strong>正在生成 ' + delivered + ' / ' + run.requested + '</strong><span>已交付图片会立即保留，其余图片继续生成。</span></div>'
          : run.state === "partial" || run.state === "failed"
            ? '<div class="free-run-message failed"><strong>生成服务暂时不可用。</strong><span>已交付图片继续保留，未交付图片不收费。</span></div>'
            : '';
      var retry = failedCount > 0 && run.failureKind === "service"
        ? '<div class="free-run-actions"><button class="btn-primary" type="button" data-free-retry="' + run.id + '">用相同设置再试一次 · ' + failedCount + ' 张</button></div>'
        : '';
      return '<article class="free-run-card" id="' + run.id + '" data-free-run-id="' + run.id + '">' +
        '<header class="free-run-head"><div><span class="free-run-time">' + run.time + '</span><h3>自由模式记录</h3><p>' + delivered + ' / ' + run.requested + ' 张已交付</p></div><span class="status ' + status.className + '">' + status.label + '</span></header>' +
        stateMessage +
        '<div class="free-run-output-grid">' + run.itemStates.map(function (itemState, index) { return renderFreeRunImage(run, itemState, index); }).join("") + '</div>' +
        '<dl class="free-run-facts"><div><dt>输入图片</dt><dd>' + escapeFreeHtml(run.inputName) + '</dd></div><div><dt>生成参数</dt><dd>' + run.ratio + ' · ' + run.requested + ' 张</dd></div><div><dt>去除商标与 Logo</dt><dd>' + (run.removeLogo ? "已开启" : "未开启") + '</dd></div><div class="wide"><dt>画面提示词</dt><dd>' + escapeFreeHtml(run.prompt) + '</dd></div></dl>' +
        renderFreeSettlement(run) + retry + '</article>';
    }

    function renderFreeRuns() {
      freeHistoryGrid.innerHTML = freeRuns.map(renderFreeRun).join("");
      freeHistoryCount.textContent = freeRuns.length + " 条记录";
    }

    function openFreeImagePreview(runId, imageIndex) {
      var run = freeRuns.find(function (item) { return item.id === runId; });
      if (!run) return;
      activeFreeImage = { run: run, imageIndex: imageIndex };
      freeImagePreviewTitle.textContent = "自由模式成图 " + (imageIndex + 1);
      var tone = imageIndex % 3 === 1 ? " warm" : imageIndex % 3 === 2 ? " cool" : "";
      freeImagePreviewLarge.innerHTML = '<span class="free-history-image' + tone + '"></span>';
      openModal(freeImagePreviewDialog, document.getElementById("free-image-preview-close"));
    }

    freeHistoryGrid.addEventListener("click", function (event) {
      var preview = event.target.closest("[data-free-preview]");
      if (preview) {
        openFreeImagePreview(preview.dataset.freePreview, Number(preview.dataset.freeImageIndex));
        return;
      }
      var exportButton = event.target.closest("[data-free-export]");
      if (exportButton) {
        showToast("图片已导出到设置页面中的默认导出路径。");
        return;
      }
      var retryButton = event.target.closest("[data-free-retry]");
      if (!retryButton) return;
      var sourceRun = freeRuns.find(function (run) { return run.id === retryButton.dataset.freeRetry; });
      if (!sourceRun) return;
      var retryCount = sourceRun.itemStates.filter(function (state) { return state === "failed" || state === "ungenerated"; }).length;
      openFreeGate("confirm", {
        count: retryCount,
        countText: retryCount + " 张",
        maxCredits: retryCount * 20,
        prompt: sourceRun.prompt,
        ratio: sourceRun.ratio,
        removeLogo: sourceRun.removeLogo,
        inputName: sourceRun.inputName,
        retrySourceId: sourceRun.id
      });
    });

    document.getElementById("free-image-preview-close").addEventListener("click", function () { freeImagePreviewDialog.close(); });
    document.getElementById("free-image-preview-export").addEventListener("click", function () {
      if (!activeFreeImage) return;
      freeImagePreviewDialog.close();
      showToast("图片已导出到设置页面中的默认导出路径。");
    });
    freeImagePreviewDialog.addEventListener("click", function (event) {
      if (event.target === freeImagePreviewDialog) freeImagePreviewDialog.close();
    });

    renderFreeRuns();

    document.querySelectorAll("#project-grid .project-card").forEach(function (card) {
      card.addEventListener("click", function () {
        selectedProject = card.dataset.project;
        window.location.href = "product-workbench.html?project=" + encodeURIComponent(projects[selectedProject].id);
      });
    });

    var newProjectName = document.getElementById("new-project-name");
    var newProjectNameError = document.getElementById("new-project-name-error");
    var newProjectMaterial = document.getElementById("new-project-material");
    var nextToSubject = document.getElementById("next-to-subject");
    var hasNewProjectMaterial = false;
    var selectedMaterialFunction = "";
    var confirmMaterialIndex = 0;
    var confirmMaterials = [];
    var confirmStateText = { done: "已确认", current: "确认中", pending: "待确认" };
    var boundaryDrag = null;
    var brandDrag = null;

    function clamp(value, minimum, maximum) {
      return Math.min(maximum, Math.max(minimum, value));
    }

    function makeConfirmMaterial(options) {
      var boundary = (options.boundary || [24, 11, 52, 80]).slice();
      return {
        name: options.name,
        dim: options.dim || "1024 × 1024",
        art: options.art || "art-cleaner",
        state: options.state || "pending",
        boundary: boundary,
        originalBoundary: boundary.slice(),
        boundaryMissing: Boolean(options.boundaryMissing),
        boundaryMode: options.boundaryMode === undefined ? "suggested" : options.boundaryMode,
        brands: (options.brands || []).map(function (brand) { return brand.slice(); }),
        brandSources: (options.brandSources || []).slice()
      };
    }

    function renderConfirmMaterials() {
      var list = document.getElementById("confirm-material-list");
      list.textContent = "";
      confirmMaterials.forEach(function (item, index) {
        var button = document.createElement("button");
        var state = index === confirmMaterialIndex ? "current" : item.state;
        button.type = "button";
        button.className = "confirm-material" + (index === confirmMaterialIndex ? " current" : "");
        button.innerHTML = '<span class="mini-art ' + item.art + '" style="--art-label:\'商品素材\'" aria-hidden="true"></span>' +
          '<span><b>' + item.name + '</b><span class="confirm-material-state ' + state + '">' + confirmStateText[state] + '</span></span>';
        button.addEventListener("click", function () {
          confirmMaterialIndex = index;
          renderConfirmFlow();
        });
        list.appendChild(button);
      });
    }

    function positionSubjectBoundary(item) {
      var boundary = document.getElementById("subject-boundary");
      var left = item.boundary[0];
      var top = item.boundary[1];
      var width = item.boundary[2];
      var height = item.boundary[3];
      boundary.style.left = left + "%";
      boundary.style.top = top + "%";
      boundary.style.width = width + "%";
      boundary.style.height = height + "%";
      document.querySelector(".subject-mask.top").style.height = top + "%";
      document.querySelector(".subject-mask.bottom").style.height = Math.max(0, 100 - top - height) + "%";
      document.querySelector(".subject-mask.left").style.top = top + "%";
      document.querySelector(".subject-mask.left").style.bottom = "auto";
      document.querySelector(".subject-mask.left").style.width = left + "%";
      document.querySelector(".subject-mask.left").style.height = height + "%";
      document.querySelector(".subject-mask.right").style.top = top + "%";
      document.querySelector(".subject-mask.right").style.bottom = "auto";
      document.querySelector(".subject-mask.right").style.width = Math.max(0, 100 - left - width) + "%";
      document.querySelector(".subject-mask.right").style.height = height + "%";
    }

    function renderConfirmStage(item) {
      document.getElementById("confirm-stage-name").textContent = item.name;
      document.getElementById("confirm-stage-dim").textContent = item.dim;
      var art = document.getElementById("confirm-art");
      art.className = "source-art " + item.art;
      art.style.setProperty("--art-label", '"' + item.name + '"');

      var boundary = document.getElementById("subject-boundary");
      positionSubjectBoundary(item);
      boundary.classList.toggle("confirm-layer-hidden", !item.boundaryMode);
      document.getElementById("confirm-mask-layer").classList.toggle("confirm-layer-hidden", !item.boundaryMode);
      document.getElementById("confirm-canvas").classList.toggle("full-image", item.boundaryMode === "full");
      document.getElementById("restore-subject").disabled = item.boundaryMissing;
      document.getElementById("restore-subject").title = item.boundaryMissing ? "当前素材没有系统建议" : "";
      document.getElementById("confirm-stage-hint").textContent = item.boundaryMode === "full"
        ? "当前使用整张商品素材，不裁切。"
        : item.boundaryMode
          ? "拖动控制点调整商品主体边界，框住整件商品和包装。"
          : "请先手动框选商品主体，或使用整图。";

      var brandLayer = document.getElementById("confirm-brand-layer");
      brandLayer.textContent = "";
      item.brands.forEach(function (brand, index) {
        var box = document.createElement("div");
        box.className = "confirm-brand-box";
        box.setAttribute("data-brand-index", index);
        box.style.left = brand[0] + "%";
        box.style.top = brand[1] + "%";
        box.style.width = brand[2] + "%";
        box.style.height = brand[3] + "%";
        box.innerHTML = "<span>" + (index + 1) + "</span><i class=\"brand-resize-handle\" aria-hidden=\"true\"></i>";
        box.tabIndex = 0;
        box.setAttribute("aria-label", "调整第 " + (index + 1) + " 个去品牌标记框");
        box.addEventListener("keydown", function (event) {
          if (["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"].indexOf(event.key) < 0) return;
          event.preventDefault();
          var current = item.brands[index].slice();
          var deltaX = event.key === "ArrowLeft" ? -1 : event.key === "ArrowRight" ? 1 : 0;
          var deltaY = event.key === "ArrowUp" ? -1 : event.key === "ArrowDown" ? 1 : 0;
          if (event.shiftKey) {
            current[2] = clamp(current[2] + deltaX, 6, 100 - current[0]);
            current[3] = clamp(current[3] + deltaY, 6, 100 - current[1]);
          } else {
            current[0] = clamp(current[0] + deltaX, 0, 100 - current[2]);
            current[1] = clamp(current[1] + deltaY, 0, 100 - current[3]);
          }
          item.brands[index] = current;
          box.style.left = current[0] + "%";
          box.style.top = current[1] + "%";
          box.style.width = current[2] + "%";
          box.style.height = current[3] + "%";
        });
        brandLayer.appendChild(box);
      });
      document.getElementById("confirm-brand-count").textContent = item.brands.length;
    }

    function renderConfirmPanel(item) {
      var markList = document.getElementById("confirm-mark-list");
      markList.textContent = "";
      var boundaryAlert = document.getElementById("confirm-boundary-alert");
      var useBoundary = document.getElementById("use-boundary");
      var useFullImage = document.getElementById("use-full-image");
      boundaryAlert.hidden = !item.boundaryMissing;
      useBoundary.classList.toggle("active", item.boundaryMode === "suggested" || item.boundaryMode === "manual");
      useFullImage.classList.toggle("active", item.boundaryMode === "full");
      document.getElementById("use-boundary-label").textContent = item.boundaryMode === "full"
        ? "恢复框选"
        : item.boundaryMissing
          ? "手动框选"
          : "框选商品";
      document.getElementById("full-image-note").hidden = item.boundaryMode !== "full";
      document.getElementById("confirm-brand-panel-count").textContent = item.brands.length ? item.brands.length + " 处" : "";
      if (!item.brands.length) {
        var empty = document.createElement("p");
        empty.textContent = "当前没有去品牌标记框。";
        markList.appendChild(empty);
      } else {
        var rows = document.createElement("div");
        rows.className = "confirm-mark-list";
        item.brands.forEach(function (_, index) {
          var row = document.createElement("div");
          row.className = "confirm-mark-row";
          row.innerHTML = '<span class="confirm-mark-index">' + (index + 1) + '</span><span class="confirm-mark-name">标记 ' + (index + 1) + '<em>　' + (item.brandSources[index] || "系统建议") + '</em></span><button class="confirm-mark-delete" type="button" aria-label="删除第 ' + (index + 1) + ' 个标记框">×</button>';
          row.addEventListener("mouseenter", function () {
            var box = document.querySelectorAll("#confirm-brand-layer .confirm-brand-box")[index];
            if (box) box.classList.add("hot");
          });
          row.addEventListener("mouseleave", function () {
            var box = document.querySelectorAll("#confirm-brand-layer .confirm-brand-box")[index];
            if (box) box.classList.remove("hot");
          });
          row.querySelector(".confirm-mark-delete").addEventListener("click", function () {
            item.brands.splice(index, 1);
            item.brandSources.splice(index, 1);
            renderConfirmFlow();
          });
          rows.appendChild(row);
        });
        markList.appendChild(rows);
      }
    }

    function findNextUnconfirmedMaterialIndex(fromIndex) {
      for (var offset = 1; offset < confirmMaterials.length; offset += 1) {
        var candidateIndex = (fromIndex + offset) % confirmMaterials.length;
        if (confirmMaterials[candidateIndex].state !== "done") return candidateIndex;
      }
      return -1;
    }

    function renderConfirmFlow() {
      var item = confirmMaterials[confirmMaterialIndex];
      var confirmedCount = confirmMaterials.filter(function (candidate) { return candidate.state === "done"; }).length;
      var nextUnconfirmedIndex = findNextUnconfirmedMaterialIndex(confirmMaterialIndex);
      renderConfirmMaterials();
      renderConfirmStage(item);
      renderConfirmPanel(item);
      document.getElementById("confirm-rail-count").textContent = confirmedCount + " / " + confirmMaterials.length;
      document.getElementById("confirm-progress").textContent = confirmedCount + " / " + confirmMaterials.length;
      document.getElementById("previous-material").disabled = confirmMaterialIndex === 0;
      document.getElementById("confirm-next-material").textContent = nextUnconfirmedIndex < 0 ? "保存商品主体图并确认文案" : "确认这张，下一张";
      document.getElementById("confirm-next-material").disabled = !item.boundaryMode;
    }

    function renderProjectNameValidation() {
      if (isExistingProjectMaterialFlow) return false;
      var name = newProjectName.value.trim();
      var duplicate = Boolean(name) && Object.keys(projects).some(function (key) {
        return projects[key].name === name;
      });
      newProjectName.setAttribute("aria-invalid", String(duplicate));
      newProjectNameError.hidden = !duplicate;
      newProjectNameError.textContent = duplicate ? "已经有一个叫“" + name + "”的商品项目。请换一个名称。" : "";
      return duplicate;
    }

    function updateCreateReady() {
      var duplicateName = renderProjectNameValidation();
      var nameReady = isExistingProjectMaterialFlow || (newProjectName.value.trim() && !duplicateName);
      document.querySelectorAll("[data-material-function]").forEach(function (button) {
        button.disabled = !hasNewProjectMaterial;
      });
      nextToSubject.disabled = !(hasNewProjectMaterial && selectedMaterialFunction && nameReady);
    }

    function addNewProjectMaterial() {
      hasNewProjectMaterial = true;
      newProjectMaterial.classList.add("added");
      document.getElementById("material-title").textContent = "商品素材_洗洁精.jpg";
      var selectedFunctionButton = selectedMaterialFunction ? document.querySelector('[data-material-function="' + selectedMaterialFunction + '"]') : null;
      document.getElementById("material-note").textContent = selectedFunctionButton
        ? "已添加 · 已选择" + selectedFunctionButton.querySelector("strong").textContent
        : "已添加 · 请选择要生成的功能图片";
    }

    function selectMaterialFunction(button) {
      selectedMaterialFunction = button.getAttribute("data-material-function");
      document.querySelectorAll("[data-material-function]").forEach(function (item) {
        item.setAttribute("aria-pressed", String(item === button));
      });
      if (hasNewProjectMaterial) {
        document.getElementById("material-note").textContent = "已添加 · 已选择" + button.querySelector("strong").textContent;
      }
    }

    function openCreateProject() {
      if (openBillingDebtGate()) return;
      library.classList.remove("active");
      createProject.classList.add("active");
      titleContext.textContent = "新建商品项目";
      newProjectName.focus({ preventScroll: true });
    }

    document.getElementById("new-project-card").addEventListener("click", openCreateProject);
    document.getElementById("back-from-create").addEventListener("click", function () {
      if (isExistingProjectMaterialFlow && existingProject) {
        window.location.href = "product-workbench.html?project=" + encodeURIComponent(existingProject.id);
        return;
      }
      createProject.classList.remove("active");
      library.classList.add("active");
      titleContext.textContent = "商品项目库";
    });
    newProjectName.addEventListener("input", updateCreateReady);
    newProjectMaterial.addEventListener("click", function () {
      addNewProjectMaterial();
      updateCreateReady();
    });
    document.querySelectorAll("[data-material-function]").forEach(function (button) {
      button.addEventListener("click", function () {
        selectMaterialFunction(button);
        updateCreateReady();
      });
    });
    updateCreateReady();
    nextToSubject.addEventListener("click", function () {
      if (nextToSubject.disabled) return;
      var projectId = isExistingProjectMaterialFlow && existingProject ? existingProject.id : "PRJ-240806-N01";
      var projectName = isExistingProjectMaterialFlow && existingProject ? existingProject.name : newProjectName.value.trim();
      window.location.href = "product-workbench.html?project=" + encodeURIComponent(projectId) + "&name=" + encodeURIComponent(projectName) + "&flow=new-material&materialFunction=" + encodeURIComponent(selectedMaterialFunction);
    });
    document.getElementById("use-boundary").addEventListener("click", function () {
      var item = confirmMaterials[confirmMaterialIndex];
      if (!item) return;
      if (item.boundaryMissing) {
        item.boundaryMode = "manual";
        if (!item.boundary) item.boundary = [12, 12, 76, 76];
      } else {
        item.boundaryMode = "suggested";
      }
      renderConfirmFlow();
    });
    document.getElementById("use-full-image").addEventListener("click", function () {
      var item = confirmMaterials[confirmMaterialIndex];
      if (!item) return;
      item.boundaryMode = "full";
      renderConfirmFlow();
    });
    document.getElementById("restore-subject").addEventListener("click", function () {
      var item = confirmMaterials[confirmMaterialIndex];
      if (!item || item.boundaryMissing) return;
      item.boundary = item.originalBoundary.slice();
      item.boundaryMode = "suggested";
      renderConfirmFlow();
    });
    document.getElementById("add-confirm-mark").addEventListener("click", function () {
      var item = confirmMaterials[confirmMaterialIndex];
      if (!item) return;
      item.brands.push([36, 36, 28, 14]);
      item.brandSources.push("手动添加");
      renderConfirmFlow();
    });
    document.getElementById("toggle-subject").addEventListener("click", function (event) {
      var isActive = event.currentTarget.classList.toggle("active");
      event.currentTarget.classList.toggle("muted", !isActive);
      document.getElementById("subject-boundary").classList.toggle("confirm-layer-hidden", !isActive);
      document.getElementById("confirm-mask-layer").classList.toggle("confirm-layer-hidden", !isActive);
    });
    document.getElementById("toggle-brand").addEventListener("click", function (event) {
      var isActive = event.currentTarget.classList.toggle("active");
      event.currentTarget.classList.toggle("muted", !isActive);
      document.getElementById("confirm-brand-layer").classList.toggle("confirm-layer-hidden", !isActive);
    });

    document.getElementById("subject-boundary").addEventListener("pointerdown", function (event) {
      var handle = event.target.closest("[data-boundary-handle]");
      var item = confirmMaterials[confirmMaterialIndex];
      if (!handle || !item || !item.boundaryMode || item.boundaryMode === "full") return;
      var canvasRect = document.getElementById("confirm-canvas").getBoundingClientRect();
      boundaryDrag = {
        direction: handle.getAttribute("data-boundary-handle"),
        startX: event.clientX,
        startY: event.clientY,
        canvasRect: canvasRect,
        item: item,
        boundary: item.boundary.slice()
      };
      event.preventDefault();
    });

    var boundaryHandleLabels = { nw: "左上", n: "上方", ne: "右上", e: "右侧", se: "右下", s: "下方", sw: "左下", w: "左侧" };
    Array.prototype.forEach.call(document.querySelectorAll("[data-boundary-handle]"), function (handle) {
      var direction = handle.getAttribute("data-boundary-handle");
      handle.tabIndex = 0;
      handle.setAttribute("aria-label", "调整商品主体边界" + boundaryHandleLabels[direction] + "控制点");
      handle.addEventListener("keydown", function (event) {
        if (["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"].indexOf(event.key) < 0) return;
        var item = confirmMaterials[confirmMaterialIndex];
        if (!item || !item.boundaryMode || item.boundaryMode === "full") return;
        event.preventDefault();
        var dx = event.key === "ArrowLeft" ? -1 : event.key === "ArrowRight" ? 1 : 0;
        var dy = event.key === "ArrowUp" ? -1 : event.key === "ArrowDown" ? 1 : 0;
        var left = item.boundary[0];
        var top = item.boundary[1];
        var right = item.boundary[0] + item.boundary[2];
        var bottom = item.boundary[1] + item.boundary[3];
        if (direction.indexOf("w") >= 0 && dx) left = clamp(left + dx, 2, right - 12);
        if (direction.indexOf("e") >= 0 && dx) right = clamp(right + dx, left + 12, 98);
        if (direction.indexOf("n") >= 0 && dy) top = clamp(top + dy, 2, bottom - 12);
        if (direction.indexOf("s") >= 0 && dy) bottom = clamp(bottom + dy, top + 12, 98);
        item.boundary = [left, top, right - left, bottom - top];
        item.boundaryMode = item.boundaryMissing ? "manual" : "suggested";
        positionSubjectBoundary(item);
      });
    });

    document.getElementById("confirm-brand-layer").addEventListener("pointerdown", function (event) {
      var box = event.target.closest(".confirm-brand-box");
      var item = confirmMaterials[confirmMaterialIndex];
      if (!box || !item) return;
      var brandIndex = Number(box.getAttribute("data-brand-index"));
      var canvasRect = document.getElementById("confirm-canvas").getBoundingClientRect();
      brandDrag = {
        mode: event.target.closest(".brand-resize-handle") ? "resize" : "move",
        startX: event.clientX,
        startY: event.clientY,
        canvasRect: canvasRect,
        item: item,
        brandIndex: brandIndex,
        brand: item.brands[brandIndex].slice(),
        box: box
      };
      event.preventDefault();
    });

    window.addEventListener("pointermove", function (event) {
      if (boundaryDrag) {
        var dx = (event.clientX - boundaryDrag.startX) / boundaryDrag.canvasRect.width * 100;
        var dy = (event.clientY - boundaryDrag.startY) / boundaryDrag.canvasRect.height * 100;
        var start = boundaryDrag.boundary;
        var left = start[0];
        var top = start[1];
        var right = start[0] + start[2];
        var bottom = start[1] + start[3];
        var direction = boundaryDrag.direction;
        if (direction.indexOf("w") >= 0) left = clamp(start[0] + dx, 2, right - 12);
        if (direction.indexOf("e") >= 0) right = clamp(right + dx, left + 12, 98);
        if (direction.indexOf("n") >= 0) top = clamp(start[1] + dy, 2, bottom - 12);
        if (direction.indexOf("s") >= 0) bottom = clamp(bottom + dy, top + 12, 98);
        boundaryDrag.item.boundary = [left, top, right - left, bottom - top];
        boundaryDrag.item.boundaryMode = boundaryDrag.item.boundaryMissing ? "manual" : "suggested";
        positionSubjectBoundary(boundaryDrag.item);
      }
      if (brandDrag) {
        var brandDx = (event.clientX - brandDrag.startX) / brandDrag.canvasRect.width * 100;
        var brandDy = (event.clientY - brandDrag.startY) / brandDrag.canvasRect.height * 100;
        var original = brandDrag.brand;
        var nextBrand = original.slice();
        if (brandDrag.mode === "move") {
          nextBrand[0] = clamp(original[0] + brandDx, 0, 100 - original[2]);
          nextBrand[1] = clamp(original[1] + brandDy, 0, 100 - original[3]);
        } else {
          nextBrand[2] = clamp(original[2] + brandDx, 6, 100 - original[0]);
          nextBrand[3] = clamp(original[3] + brandDy, 6, 100 - original[1]);
        }
        brandDrag.item.brands[brandDrag.brandIndex] = nextBrand;
        brandDrag.box.style.left = nextBrand[0] + "%";
        brandDrag.box.style.top = nextBrand[1] + "%";
        brandDrag.box.style.width = nextBrand[2] + "%";
        brandDrag.box.style.height = nextBrand[3] + "%";
      }
    });

    window.addEventListener("pointerup", function () {
      boundaryDrag = null;
      brandDrag = null;
    });

    document.getElementById("abandon-subject-confirmation").addEventListener("click", function () {
      openSubjectAbandonDialog("confirmation");
    });
    document.getElementById("previous-material").addEventListener("click", function () {
      if (confirmMaterialIndex > 0) {
        confirmMaterialIndex -= 1;
        renderConfirmFlow();
      }
    });
    document.getElementById("confirm-next-material").addEventListener("click", function () {
      if (document.getElementById("confirm-next-material").disabled) return;
      confirmMaterials[confirmMaterialIndex].state = "done";
      var nextUnconfirmedIndex = findNextUnconfirmedMaterialIndex(confirmMaterialIndex);
      if (nextUnconfirmedIndex >= 0) {
        showToast("商品主体图和去品牌标记图已保存。");
        confirmMaterialIndex = nextUnconfirmedIndex;
        renderConfirmFlow();
        return;
      }
      var nextParams = new URLSearchParams({
        project: existingProject.id,
        name: existingProject.name,
        flow: "copy-confirm",
        materialAdded: "1",
        materialFunction: requestedMaterialFunction,
        setCount: String(requestedSetCount)
      });
      if (requestedCopyTreatment) nextParams.set("copyTreatment", requestedCopyTreatment);
      if (requestedReferenceAdded) {
        nextParams.set("referenceAdded", "1");
        nextParams.set("referenceAspects", requestedReferenceAspects);
      }
      window.location.href = "product-workbench.html?" + nextParams.toString();
    });
    function switchWorkspaceView(view) {
      var showLibrary = view === "product-library";
      var showFreeMode = view === "free-mode";
      var showSettings = view === "settings";
      library.classList.toggle("active", showLibrary);
      freeMode.classList.toggle("active", showFreeMode);
      settings.classList.toggle("active", showSettings);
      titleContext.textContent = showFreeMode ? "自由模式" : showSettings ? "设置" : "商品项目库";
      document.querySelectorAll("[data-workspace-tab]").forEach(function (tab) {
        var selected = tab.dataset.workspaceTab === view;
        tab.setAttribute("aria-selected", String(selected));
        tab.setAttribute("tabindex", selected ? "0" : "-1");
        tab.setAttribute("aria-controls", tab.dataset.workspaceTab === "product-library" ? "product-library" : tab.dataset.workspaceTab === "free-mode" ? "product-free-mode" : "product-settings");
      });
      window.requestAnimationFrame(function () {
        var activePanel = showLibrary ? library : showFreeMode ? freeMode : settings;
        var selectedTab = activePanel.querySelector('[data-workspace-tab="' + view + '"]');
        if (selectedTab) selectedTab.focus({ preventScroll: true });
      });
    }

    document.querySelectorAll("[data-workspace-tab]").forEach(function (tab) {
      tab.addEventListener("click", function () {
        if (tab.dataset.workspaceTab === "free-mode" && openBillingDebtGate()) return;
        switchWorkspaceView(tab.dataset.workspaceTab);
      });
      tab.addEventListener("keydown", function (event) {
        if (["ArrowLeft", "ArrowRight", "Home", "End"].indexOf(event.key) < 0) return;
        event.preventDefault();
        var tabs = Array.from(tab.closest('[role="tablist"]').querySelectorAll("[data-workspace-tab]:not([disabled])"));
        var currentIndex = tabs.indexOf(tab);
        var nextIndex = event.key === "Home"
          ? 0
          : event.key === "End"
            ? tabs.length - 1
            : (currentIndex + (event.key === "ArrowRight" ? 1 : -1) + tabs.length) % tabs.length;
        switchWorkspaceView(tabs[nextIndex].dataset.workspaceTab);
      });
    });
    document.getElementById("choose-export-path").addEventListener("click", function () {
      defaultExportPath.textContent = "D:\\电商素材\\变色龙成图";
      settingsSavedState.textContent = "已保存";
      showToast("默认导出路径已更新。");
    });

    var freeImageInput = document.getElementById("free-image-input");
    var freeAddImage = document.getElementById("free-add-image");
    var freeImageEmpty = freeAddImage.querySelector(".free-drop-empty");
    var freeImageSelected = freeAddImage.querySelector(".free-drop-selected");
    var freeImageName = document.getElementById("free-image-name");
    var freeImageError = document.getElementById("free-image-error");
    var freePrompt = document.getElementById("free-prompt");
    var freePromptCount = document.getElementById("free-prompt-count");
    var freePromptError = document.getElementById("free-prompt-error");
    var freeGateDialog = document.getElementById("free-gate-dialog");
    var freeGateTitle = document.getElementById("free-gate-title");
    var freeGateDescription = document.getElementById("free-gate-description");
    var freeGateBody = document.getElementById("free-gate-body");
    var freeGateFootnote = document.getElementById("free-gate-footnote");
    var freeGateBack = document.getElementById("free-gate-back");
    var freeGateRecharge = document.getElementById("free-gate-recharge");
    var freeGateConfirm = document.getElementById("free-gate-confirm");
    var freeImageReady = false;
    var freeGateMode = "confirm";
    var freeGateContext = null;
    var freeGateSubmitTimer = null;
    var freeSelectedImageName = "";

    function setFreeImageError(message) {
      freeImageError.textContent = message;
      freeImageError.hidden = !message;
      freeAddImage.classList.toggle("has-error", Boolean(message));
      freeAddImage.setAttribute("aria-invalid", String(Boolean(message)));
    }

    function showFreeSelectedImage(file) {
      freeImageReady = true;
      freeSelectedImageName = file.name;
      freeImageName.textContent = file.name;
      freeImageEmpty.hidden = true;
      freeImageSelected.hidden = false;
      freeAddImage.classList.add("has-image");
      setFreeImageError("");
    }

    function setFreePromptError(message) {
      freePromptError.textContent = message;
      freePromptError.hidden = !message;
      freePrompt.setAttribute("aria-invalid", String(Boolean(message)));
    }

    function updateFreePromptCount() {
      freePromptCount.textContent = freePrompt.value.length + " / 2000";
      if (freePrompt.value.trim()) setFreePromptError("");
    }

    function validateFreeForm() {
      var firstInvalid = null;
      if (!freeImageReady) {
        setFreeImageError("请选择一张输入图片。");
        firstInvalid = freeAddImage;
      } else {
        setFreeImageError("");
      }

      if (!freePrompt.value.trim()) {
        setFreePromptError("请填写画面提示词。");
        if (!firstInvalid) firstInvalid = freePrompt;
      } else if (freePrompt.value.length > 2000) {
        setFreePromptError("画面提示词不能超过 2000 字。");
        if (!firstInvalid) firstInvalid = freePrompt;
      } else {
        setFreePromptError("");
      }

      if (firstInvalid) {
        firstInvalid.focus({ preventScroll: true });
        return false;
      }
      return true;
    }

    function currentWalletBalance() {
      return Number(document.getElementById("wallet-balance").textContent.replace(/[^\d]/g, "")) || 0;
    }

    function freeGateSummary(context) {
      return '<section class="free-gate-summary" aria-label="本次自由生成摘要">' +
        '<div><span>生成数量</span><strong>' + context.count + ' 张</strong></div>' +
        '<div><span>每张费用</span><strong>20 鸭豆</strong></div>' +
        '<div><span>最大预扣</span><strong>' + context.maxCredits.toLocaleString("zh-CN") + ' 鸭豆</strong></div>' +
        '<div><span>当前余额</span><strong>' + currentWalletBalance().toLocaleString("zh-CN") + ' 鸭豆</strong></div>' +
      '</section>';
    }

    function renderFreeGate(mode) {
      if (!freeGateContext) return;
      freeGateMode = mode;
      freeGateBack.hidden = false;
      freeGateRecharge.hidden = true;
      freeGateConfirm.hidden = false;
      freeGateConfirm.disabled = false;

      if (mode === "confirm") {
        var isRetry = Boolean(freeGateContext.retrySourceId);
        freeGateTitle.textContent = isRetry ? "确认并重新生成" : "确认并提交自由生成";
        freeGateDescription.textContent = isRetry ? "请核对未交付图片数量和最大鸭豆数。" : "请核对本次生成数量和最大鸭豆数。";
        freeGateBody.innerHTML = freeGateSummary(freeGateContext) +
          '<div class="free-gate-rules">' +
            '<section class="free-gate-rule"><strong>按实际成功生成的张数结算</strong><span>最多预扣 ' + freeGateContext.maxCredits.toLocaleString("zh-CN") + ' 鸭豆。没有成功生成的图片不会结算。</span></section>' +
            '<section class="free-gate-rule"><strong>' + (isRetry ? "沿用原记录的生成设置" : "提交后不能修改本次设置") + '</strong><span>' + (isRetry ? "输入图片、提示词、宽高比和去除商标选项保持不变。" : "输入图片、提示词、宽高比、生成数量和去除商标选项将按当前内容执行。") + '</span></section>' +
          '</div>';
        freeGateFootnote.textContent = isRetry ? "确认前可以返回原记录。" : "确认前仍然可以返回表单修改。";
        freeGateBack.textContent = isRetry ? "返回原记录" : "再看看";
        freeGateConfirm.textContent = "确认并提交";
        return;
      }

      if (mode === "confirming" || mode === "unknown") {
        var isUnknown = mode === "unknown";
        freeGateTitle.textContent = isUnknown ? "提交处理中" : "正在确认自由生成";
        freeGateDescription.textContent = isUnknown
          ? "提交结果暂时没有返回。系统正在继续核对这一次提交。"
          : "正在确认鸭豆预扣和记录创建结果，请稍候。";
        freeGateBody.innerHTML = freeGateSummary(freeGateContext) +
          '<section class="free-gate-status" role="status"><strong>' + (isUnknown ? "正在等待原提交结果" : "系统正在自动处理") + '</strong><span>' +
          (isUnknown ? "不会重复预扣，也不会建立第二条记录。" : "确认成功后会在独立历史中显示排队中记录。") +
          '</span><div class="free-gate-progress" aria-hidden="true"></div></section>';
        freeGateFootnote.textContent = isUnknown
          ? "结果返回前不能再次提交。"
          : "确认完成前，本次设置保持锁定。";
        freeGateBack.hidden = true;
        freeGateRecharge.hidden = true;
        freeGateConfirm.hidden = true;
        return;
      }

      if (mode === "rejected") {
        var missingCredits = Math.max(0, freeGateContext.maxCredits - currentWalletBalance());
        freeGateTitle.textContent = "鸭豆余额不足，本次没有提交";
        freeGateDescription.textContent = "提交前余额发生变化。当前余额不足以完成本次预扣。";
        freeGateBody.innerHTML =
          '<section class="free-gate-status rejected" role="alert"><strong>还差 ' + missingCredits.toLocaleString("zh-CN") + ' 鸭豆</strong><span>当前余额 ' + currentWalletBalance().toLocaleString("zh-CN") + ' 鸭豆，最多需要 ' + freeGateContext.maxCredits.toLocaleString("zh-CN") + ' 鸭豆。</span></section>' +
          '<section class="free-gate-rule"><strong>表单内容已经保留</strong><span>充值后可以继续提交，不需要重新选择图片或填写提示词。</span></section>';
        freeGateFootnote.textContent = "本次没有预扣鸭豆，也没有建立自由模式记录。";
        freeGateBack.textContent = "返回表单";
        freeGateRecharge.hidden = false;
        freeGateConfirm.hidden = true;
        return;
      }

      freeGateTitle.textContent = "余额已更新，可以重新提交";
      freeGateDescription.textContent = "当前余额足够。本次表单内容保持不变。";
      freeGateBody.innerHTML =
        '<section class="free-gate-status recovered" role="status"><strong>当前余额 ' + currentWalletBalance().toLocaleString("zh-CN") + ' 鸭豆</strong><span>最多需要 ' + freeGateContext.maxCredits.toLocaleString("zh-CN") + ' 鸭豆。</span></section>' +
        freeGateSummary(freeGateContext);
      freeGateFootnote.textContent = "重新提交前仍然可以返回表单。";
      freeGateBack.textContent = "返回表单";
      freeGateConfirm.textContent = "确认并提交";
    }

    function openFreeGate(mode, contextOverride) {
      var countText = document.getElementById("free-count").value;
      var count = Number.parseInt(countText, 10) || 1;
      freeGateContext = contextOverride || {
        count: count,
        countText: countText,
        maxCredits: count * 20,
        prompt: freePrompt.value.trim(),
        ratio: document.getElementById("free-ratio").value,
        removeLogo: document.getElementById("free-remove-logo").checked,
        inputName: freeSelectedImageName || "输入图片"
      };
      renderFreeGate(mode || "confirm");
      openModal(freeGateDialog, freeGateConfirm.hidden ? freeGateBack : freeGateConfirm);
      window.requestAnimationFrame(function () {
        if (!freeGateConfirm.hidden) freeGateConfirm.focus({ preventScroll: true });
      });
    }

    function clearFreeFormAfterSubmit() {
      freeImageReady = false;
      freeSelectedImageName = "";
      freeImageInput.value = "";
      freeImageEmpty.hidden = false;
      freeImageSelected.hidden = true;
      freeAddImage.classList.remove("has-image", "has-error");
      freeAddImage.setAttribute("aria-invalid", "false");
      freePrompt.value = "";
      updateFreePromptCount();
      document.getElementById("free-ratio").value = "1:1";
      document.getElementById("free-count").value = "1 张";
      document.getElementById("free-remove-logo").checked = false;
    }

    function finishFreeGate() {
      var context = freeGateContext;
      var newRun = {
        id: "FREE-NEW-" + Date.now(),
        state: "queued",
        time: "刚刚",
        ratio: context.ratio,
        requested: context.count,
        prompt: context.prompt,
        inputName: context.inputName || "输入图片",
        removeLogo: context.removeLogo,
        retrySourceId: context.retrySourceId || "",
        itemStates: Array(context.count).fill("pending")
      };
      freeRuns.unshift(newRun);
      renderFreeRuns();
      freeGateDialog.close();
      if (!context.retrySourceId) clearFreeFormAfterSubmit();
      document.getElementById(newRun.id).scrollIntoView({ behavior: "smooth", block: "start" });
    }

    freeAddImage.addEventListener("click", function () { freeImageInput.click(); });
    freeImageInput.addEventListener("change", function () {
      if (freeImageInput.files && freeImageInput.files[0]) showFreeSelectedImage(freeImageInput.files[0]);
    });
    freePrompt.addEventListener("input", updateFreePromptCount);

    freeGateBack.addEventListener("click", function () { freeGateDialog.close(); });
    freeGateRecharge.addEventListener("click", function () {
      document.getElementById("wallet-balance").textContent = "12,480";
      renderFreeGate("recovered");
    });
    freeGateConfirm.addEventListener("click", function () {
      window.clearTimeout(freeGateSubmitTimer);
      renderFreeGate("confirming");
      freeGateSubmitTimer = window.setTimeout(finishFreeGate, 900);
    });
    freeGateDialog.addEventListener("cancel", function (event) {
      if (freeGateMode === "confirming" || freeGateMode === "unknown") event.preventDefault();
    });
    freeGateDialog.addEventListener("click", function (event) {
      if (event.target === freeGateDialog && freeGateMode !== "confirming" && freeGateMode !== "unknown") freeGateDialog.close();
    });

    document.getElementById("free-submit").addEventListener("click", function () {
      if (openBillingDebtGate()) return;
      if (!validateFreeForm()) return;
      openFreeGate("confirm");
    });
    if (requestedScenario === "library-name-duplicate") {
      newProjectName.value = projects.cleaner.name;
      addNewProjectMaterial();
      selectMaterialFunction(document.querySelector('[data-material-function="marketing"]'));
      updateCreateReady();
      openCreateProject();
    }
    if (requestedScenario === "library-material-required") {
      newProjectName.value = "晨雾保温杯";
      updateCreateReady();
      openCreateProject();
    }
    if (requestedScenario === "library-function-required") {
      newProjectName.value = "晨雾保温杯";
      addNewProjectMaterial();
      updateCreateReady();
      openCreateProject();
    }
    if (isExistingProjectMaterialFlow && existingProject) {
      selectedProject = existingProjectKey;
      library.classList.remove("active");
      createProject.classList.add("active");
      titleContext.textContent = "商品项目库 · " + existingProject.name;
      document.getElementById("back-from-create").textContent = "返回商品项目";
      document.getElementById("create-project-heading").textContent = "添加商品素材";
      document.getElementById("create-project-description").textContent = "向“" + existingProject.name + "”添加新的商品素材。";
      document.getElementById("create-panel").setAttribute("aria-label", "向当前商品项目添加商品素材");
      document.getElementById("create-project-name-field").hidden = true;
      document.getElementById("create-project-footnote").textContent = "下一步先完成这张功能图片的生成设置。商品主体将在设置完成后确认。";
    }

    if (isSubjectConfirmationFlow && existingProject) {
      library.classList.remove("active");
      createProject.classList.remove("active");
      subjectConfirm.classList.add("active");
      document.getElementById("product-app").classList.add("confirming");
      titleContext.textContent = "商品项目工作台";
      document.getElementById("confirm-project-name").textContent = existingProject.name;
      var functionNames = { marketing: "营销图", macro1: "细节图", scene: "场景图", white: "白底图" };
      var primaryMaterial = makeConfirmMaterial({
        name: (functionNames[requestedMaterialFunction] || "功能图片") + " · 商品素材_洗洁精.jpg",
        art: existingProject.art,
        brands: [[38, 24, 24, 9]],
        brandSources: ["系统建议"]
      });
      if (requestedScenario === "subject-boundary-missing") {
        primaryMaterial.boundaryMissing = true;
        primaryMaterial.boundaryMode = null;
        primaryMaterial.brands = [];
        primaryMaterial.brandSources = [];
      }
      if (requestedScenario === "subject-full-image") primaryMaterial.boundaryMode = "full";
      if (requestedScenario === "subject-brand-boxes") {
        primaryMaterial.brands = [[38, 24, 24, 9], [31, 68, 38, 10]];
        primaryMaterial.brandSources = ["系统建议", "系统建议"];
      }
      confirmMaterials = [primaryMaterial];
      confirmMaterialIndex = 0;
      if (["subject-confirm-one", "subject-multiple", "subject-last"].indexOf(requestedScenario) >= 0) {
        confirmMaterials = [
          makeConfirmMaterial({ name: "营销图 · 商品素材_洗洁精.jpg", art: "art-cleaner", state: requestedScenario === "subject-confirm-one" ? "pending" : "done", brands: [[38, 24, 24, 9]], brandSources: ["系统建议"] }),
          makeConfirmMaterial({ name: "场景图 · 商品素材_使用场景.jpg", art: "art-lotion", brands: [[31, 68, 38, 10]], brandSources: ["系统建议"] })
        ];
        if (requestedScenario === "subject-multiple") {
          confirmMaterials.push(makeConfirmMaterial({ name: "白底图 · 商品素材_补充角度.jpg", art: "art-tea", brands: [], brandSources: [] }));
        }
        confirmMaterialIndex = requestedScenario === "subject-confirm-one" ? 0 : 1;
      }
      renderConfirmFlow();
      if (requestedScenario === "subject-abandon") {
        window.requestAnimationFrame(function () { openSubjectAbandonDialog("confirmation"); });
      }
    }

    if (isSubjectAnalysisFlow && existingProject) {
      library.classList.remove("active");
      createProject.classList.remove("active");
      subjectAnalysis.classList.add("active");
      document.getElementById("product-app").classList.add("confirming");
      titleContext.textContent = "商品项目工作台";
      var analysisName = "商品素材_洗洁精.jpg";
      document.getElementById("subject-analysis-rail-name").textContent = analysisName;
      document.getElementById("subject-analysis-current").textContent = analysisName;
      document.getElementById("subject-analysis-rail-art").className = "mini-art " + existingProject.art;
      var analysisArt = document.getElementById("subject-analysis-art");
      analysisArt.className = "source-art " + existingProject.art;
      analysisArt.style.setProperty("--art-label", '"' + analysisName + '"');
      setSubjectAnalysisFailed(requestedScenario === "subject-analysis-failed");
    }

    if (requestedScenario === "library-project-deleted") {
      var deletedProjectId = entryQuery.get("deleted");
      var deletedProjectKey = Object.keys(projects).find(function (key) {
        return projects[key].id === deletedProjectId;
      });
      if (deletedProjectKey) {
        var deletedProjectCard = document.querySelector('[data-project="' + deletedProjectKey + '"]');
        if (deletedProjectCard) deletedProjectCard.remove();
        window.requestAnimationFrame(function () {
          showToast("“" + projects[deletedProjectKey].name + "”已删除。");
        });
      }
    }

    var freeGateScenarioMode = {
      "free-gate": "confirm",
      "free-hold-rejected": "rejected",
      "free-hold-unknown": "unknown"
    }[requestedScenario];

    var freeRunScenarioId = {
      "free-queued": "FREE-QUEUED",
      "free-running": "FREE-RUNNING",
      "free-completed": "FREE-COMPLETED",
      "free-partial": "FREE-PARTIAL",
      "free-failed": "FREE-FAILED",
      "free-retry-failed-count": "FREE-PARTIAL"
    }[requestedScenario];

    if (!entryFlow && (requestedScenario === "free-form" || freeGateScenarioMode || freeRunScenarioId)) {
      switchWorkspaceView("free-mode");
    } else if (!entryFlow && ["product-library", "free-mode", "settings"].indexOf(requestedWorkspaceView) >= 0) {
      switchWorkspaceView(requestedWorkspaceView);
    }

    if (freeGateScenarioMode) {
      showFreeSelectedImage({ name: "商品图片_洗洁精.jpg" });
      freePrompt.value = "把商品放在清晨的厨房台面上，保留包装完整。";
      updateFreePromptCount();
      document.getElementById("free-ratio").value = "3:4";
      document.getElementById("free-count").value = "2 张";
      if (freeGateScenarioMode === "rejected") document.getElementById("wallet-balance").textContent = "20";
      window.requestAnimationFrame(function () { openFreeGate(freeGateScenarioMode); });
    }

    if (freeRunScenarioId) {
      window.requestAnimationFrame(function () {
        var targetRun = document.getElementById(freeRunScenarioId);
        if (!targetRun) return;
        targetRun.classList.add("walkthrough-focus");
        targetRun.scrollIntoView({ behavior: "instant", block: "start" });
      });
    }

    if (requestedScenario === "billing-debt-gate") {
      document.getElementById("wallet-balance").textContent = "20";
      window.requestAnimationFrame(openBillingDebtGate);
    }

  }());
