    (function () {
      "use strict";

      var projects = [
        { id: "PRJ-240716-C08", name: "山野净洗洁精", file: "商品素材_洗洁精.jpg", thumb: "thumb-cleaner", sideThumb: "thumb-cleaner-alt", subjectCount: 2, count: 3, unresolvedBillingCount: 2 },
        { id: "PRJ-240629-D04", name: "绒雾身体乳", file: "商品素材_身体乳.png", thumb: "thumb-lotion", sideThumb: "thumb-lotion", subjectCount: 1, count: 4, unresolvedBillingCount: 0 },
        { id: "PRJ-240618-F21", name: "暮山冷泡茶", file: "商品素材_冷泡茶.jpg", thumb: "thumb-tea", sideThumb: "thumb-night", subjectCount: 2, count: 3, unresolvedBillingCount: 0 },
        { id: "PRJ-240805-A17", name: "暖光护眼台灯", file: "商品素材_台灯.jpg", thumb: "thumb-warm", sideThumb: "thumb-warm", subjectCount: 1, count: 1, unresolvedBillingCount: 0 }
      ];

      var initialQuery = new URLSearchParams(window.location.search);
      var requestedProjectId = initialQuery.get("project");
      var requestedProjectName = initialQuery.get("name");
      var entryFlow = initialQuery.get("flow") || "";
      var materialFunction = initialQuery.get("materialFunction") || "marketing";
      var requestedSetCount = Number(initialQuery.get("setCount")) || 0;
      var requestedCopyTreatment = initialQuery.get("copyTreatment") || "";
      var requestedReferenceAdded = initialQuery.get("referenceAdded") === "1";
      var requestedReferenceAspects = (initialQuery.get("referenceAspects") || "").split(",").filter(Boolean);
      var requestedScenario = initialQuery.get("scenario") || "";
      var serviceGateScenarios = {
        "app-service-unavailable": {
          tone: "error",
          label: "服务不可用",
          title: "服务配置不完整",
          detail: "变色龙暂时不能开始新的生成任务。已有商品项目、商品任务和成图仍可查看。"
        },
        "app-service-config-sync": {
          tone: "warning",
          label: "服务配置同步中",
          title: "正在同步服务配置",
          detail: "应用正在重新获取服务配置。完成前不能开始新的生成任务。",
          recoverAutomatically: true
        }
      };
      var serviceGateScenario = serviceGateScenarios[requestedScenario] || null;
      var serviceGateActive = Boolean(serviceGateScenario);
      var gatewayBillingResult = requestedScenario === "billing-debt-gate" ? "insufficient_balance" : "";
      var billingDebtGateActive = gatewayBillingResult === "insufficient_balance";
      var gateTwoScenarios = ["gate-two-open", "gate-two-settlement-rule", "gate-two-lock-rule", "gate-two-actions", "gate-two-submitting", "gate-two-rejected", "gate-two-unknown", "gate-two-duplicate", "gate-two-accepted"];
      var isGateTwoScenario = gateTwoScenarios.indexOf(requestedScenario) >= 0;
      var isNewMaterialFlow = entryFlow === "new-material";
      var isCopyConfirmFlow = entryFlow === "copy-confirm";
      var materialAdded = initialQuery.get("materialAdded") === "1" || ["library-material-promoted", "copy-ready"].indexOf(requestedScenario) >= 0 || isGateTwoScenario;
      var safetyFailureScenarios = ["task-failed-safety", "reentry-content-safety-reason"];
      var serviceFailureScenarios = ["task-failed", "reentry-exclusive-actions", "reentry-original-ledger-unchanged", "reentry-same-settings", "reentry-same-settings-confirm"];
      if (requestedProjectId && requestedProjectName && !projects.some(function (project) { return project.id === requestedProjectId; })) {
        projects.push({
          id: requestedProjectId,
          name: requestedProjectName,
          file: "商品素材_洗洁精.jpg",
          thumb: "thumb-cleaner",
          sideThumb: "thumb-cleaner-alt",
          subjectCount: 0,
          count: 1,
          isNew: true
        });
      }

      var detailSizes = [
        { id: "d1", ratio: "1:1", px: "1024x1024", shape: "square" },
        { id: "d2", ratio: "3:4", px: "1024x1536", shape: "tall" },
        { id: "d3", ratio: "3:4", px: "900x1200", shape: "tall" },
        { id: "d4", ratio: "4:3", px: "1536x1024", shape: "wide" }
      ];

      var detailStyles = ["简约白底", "轻奢暖调", "科技深色", "清新自然", "现代商务", "复古质感", "潮流撞色", "国风雅韵", "自定义"];

      var mainShots = [
        { id: "marketing", name: "营销图", desc: "带文案的营销头图", copy: "rewrite" },
        { id: "macro1", name: "细节图一", desc: "细节特写 · 配置一", copy: "rewrite" },
        { id: "macro2", name: "细节图二", desc: "细节特写 · 配置二", copy: "rewrite" },
        { id: "scene", name: "场景图", desc: "真实使用场景", copy: "rewrite" },
        { id: "white", name: "白底图", desc: "纯白背景无阴影" }
      ];

      var detailSections = [
        { id: "hero", name: "首屏主张图", desc: "产品大图 + 核心主张大标题，有冲击力的首屏头图", copy: "rewrite" },
        { id: "points", name: "核心卖点图", desc: "产品图 + 3-4 个核心卖点图文", copy: "rewrite" },
        { id: "scene", name: "使用场景图", desc: "产品放进真实使用场景，生活化氛围", copy: "rewrite" },
        { id: "macro", name: "细节特写图", desc: "局部微距特写，突出材质 / 工艺", copy: "rewrite" },
        { id: "spec", name: "规格参数图", desc: "图示呈现规格 / 尺寸 / 参数", copy: "keep" },
        { id: "brand", name: "品牌保障图", desc: "品牌背书 / 售后 / 质保信任收尾", copy: "rewrite" }
      ];

      function originalItems(items) {
        return items.map(function (item, index) {
          return { id: item.id, name: item.name, desc: item.desc, copy: item.copy || null, on: index === 0, subjectId: null, ref: false, referenceAspects: [] };
        });
      }

      function initializeProject(project) {
        project.main = { setCount: project.count, items: originalItems(mainShots) };
        project.detail = { size: "d2", style: detailStyles[0], setCount: project.count, items: originalItems(detailSections) };
        return project;
      }

      projects.forEach(initializeProject);

      var state = {
        tab: "main",
        projectIndex: 0,
        workbenchMode: "edit",
        selectedTaskId: null,
        continueSource: null,
        createdContinuation: false,
        createdContinuationName: "场景图",
        createdContinuationTotalImages: 1,
        createdContinuationSetCount: 1,
        submissionNotice: null,
        failedTaskKind: safetyFailureScenarios.indexOf(requestedScenario) >= 0 ? "safety" : requestedScenario === "recovery-task-failed" ? "recovery-not-started" : "service",
        restartedTasks: [],
        restartedTaskSequence: 0,
        copySource: isNewMaterialFlow || isCopyConfirmFlow ? "material" : "none",
        copyFunctionId: null,
        copyDrafts: {},
        copyConfirmed: {},
        copyDraftingFailed: requestedScenario === "copy-drafting-failed",
        firstGateConfirmed: isCopyConfirmFlow,
        copyReturnTarget: materialAdded ? "subject" : "settings"
      };

      var view = document.getElementById("view");
      var navNote = document.getElementById("nav-note");
      var tabs = Array.prototype.slice.call(document.querySelectorAll(".tab"));
      var subjectPicker = document.getElementById("subject-picker");
      var draftSaveToast = document.getElementById("draft-save-toast");
      var draftSaveToastTitle = document.getElementById("draft-save-toast-title");
      var draftSaveToastDetail = document.getElementById("draft-save-toast-detail");
      var draftSaveRetry = document.getElementById("draft-save-retry");
      var draftSaveTimer = null;
      var draftToastHideTimer = null;
      var draftReplaceDialog = document.getElementById("draft-replace-dialog");
      var pendingDraftReplacement = null;
      var taskAbandonDialog = document.getElementById("task-abandon-dialog");
      var taskAbandonTitle = document.getElementById("task-abandon-title");
      var taskAbandonDescription = document.getElementById("task-abandon-description");
      var keepCurrentTask = document.getElementById("keep-current-task");
      var confirmAbandonTask = document.getElementById("confirm-abandon-task");
      var pendingTaskAbandonment = null;
      var projectDeleteDialog = document.getElementById("project-delete-dialog");
      var projectDeleteTitle = document.getElementById("project-delete-title");
      var projectDeleteDescription = document.getElementById("project-delete-description");
      var cancelProjectDelete = document.getElementById("cancel-project-delete");
      var confirmProjectDelete = document.getElementById("confirm-project-delete");
      var pendingProjectDeletion = null;
      var projectDeleteMode = "";
      var referenceBoundaryDialog = document.getElementById("reference-boundary-dialog");
      var closeReferenceBoundary = document.getElementById("close-reference-boundary");
      var gateOneDialog = document.getElementById("gate-one-dialog");
      var gateOneBody = document.getElementById("gate-one-body");
      var gateOneBack = document.getElementById("gate-one-back");
      var gateOneConfirm = document.getElementById("gate-one-confirm");
      var gateOneRecharge = document.getElementById("gate-one-recharge");
      var gateOneRecheck = document.getElementById("gate-one-recheck");
      var gateOneFootnote = document.getElementById("gate-one-footnote");
      var gateOneContinue = null;
      var gateOneContext = null;
      var gateTwoDialog = document.getElementById("gate-two-dialog");
      var gateTwoStep = document.getElementById("gate-two-step");
      var gateTwoTitle = document.getElementById("gate-two-title");
      var gateTwoIntro = document.getElementById("gate-two-intro");
      var gateTwoBody = document.getElementById("gate-two-body");
      var gateTwoFootnote = document.getElementById("gate-two-footnote");
      var gateTwoBack = document.getElementById("gate-two-back");
      var gateTwoRecharge = document.getElementById("gate-two-recharge");
      var gateTwoConfirm = document.getElementById("gate-two-confirm");
      var gateTwoContext = null;
      var gateTwoMode = "confirm";
      var gateTwoSubmitTimer = null;
      var submissionNoticeTimer = null;
      var walletBalance = 12480;
      var walletBalanceLabel = document.getElementById("wallet-balance");
      var mainImageUnitPrice = 30;
      var taskPreviewDialog = document.getElementById("task-preview-dialog");
      var taskPreviewTitle = document.getElementById("task-preview-title");
      var taskPreviewBody = document.getElementById("task-preview-body");
      var taskPreviewExport = document.getElementById("task-preview-export");
      var taskPreviewContinue = document.getElementById("task-preview-continue");
      var activeTaskOutput = null;
      var billingDebtDialog = document.getElementById("billing-debt-dialog");
      var billingDebtLater = document.getElementById("billing-debt-later");
      var billingDebtRecharge = document.getElementById("billing-debt-recharge");
      var productWorkbenchApp = document.getElementById("product-workbench-app");
      var serviceStatus = document.getElementById("service-status");
      var serviceStatusLabel = document.getElementById("service-status-label");
      var globalStatusBar = document.getElementById("global-status-bar");
      var globalStatusTitle = document.getElementById("global-status-title");
      var globalStatusDetail = document.getElementById("global-status-detail");
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

      function renderServiceGate() {
        if (!serviceGateScenario) return;
        productWorkbenchApp.classList.add("service-status-visible");
        serviceStatus.className = "service-status " + serviceGateScenario.tone;
        serviceStatus.setAttribute("aria-label", "应用状态：" + serviceGateScenario.label);
        serviceStatusLabel.textContent = serviceGateScenario.label;
        globalStatusBar.className = "global-status-bar " + serviceGateScenario.tone;
        globalStatusTitle.textContent = serviceGateScenario.title;
        globalStatusDetail.textContent = serviceGateScenario.detail;
        globalStatusBar.hidden = false;
        if (serviceGateScenario.recoverAutomatically) {
          window.setTimeout(function () {
            serviceGateActive = false;
            serviceGateScenario = null;
            productWorkbenchApp.classList.remove("service-status-visible");
            serviceStatus.className = "service-status ready";
            serviceStatus.setAttribute("aria-label", "应用状态：服务正常");
            serviceStatusLabel.textContent = "服务正常";
            globalStatusBar.hidden = true;
            navNote.textContent = "服务配置已同步，可以开始新的生成任务";
            renderSubjectPicker(projects[state.projectIndex]);
            renderWorkbench();
          }, 2600);
        }
      }

      function blockNewGeneration() {
        if (!serviceGateActive) return false;
        navNote.textContent = serviceGateScenario.title + "；已有内容仍可查看";
        globalStatusBar.focus({ preventScroll: true });
        return true;
      }

      function applyServiceGateToControls() {
        if (!serviceGateActive) return;
        [
          "#add-material-from-workbench", "#new-task", "#begin-task", "#submit-confirmed-copy",
          "[data-task-output-continue]", "[data-restart-task]"
        ].forEach(function (selector) {
          document.querySelectorAll(selector).forEach(function (control) {
            control.disabled = true;
            control.title = "服务恢复后可以使用";
          });
        });
      }

      renderServiceGate();

      if (billingDebtGateActive) {
        walletBalance = 20;
        walletBalanceLabel.textContent = walletBalance.toLocaleString("zh-CN");
      }

      function openBillingDebtGate() {
        if (!billingDebtGateActive || gatewayBillingResult !== "insufficient_balance") return false;
        openModal(billingDebtDialog, billingDebtLater);
        return true;
      }

      billingDebtLater.addEventListener("click", function () {
        billingDebtDialog.close();
      });

      billingDebtRecharge.addEventListener("click", function () {
        walletBalance = 12480;
        walletBalanceLabel.textContent = walletBalance.toLocaleString("zh-CN");
        billingDebtGateActive = false;
        billingDebtDialog.close();
        navNote.textContent = "欠费已结清，可以继续生成";
      });

      function clearSubmissionNotice() {
        window.clearTimeout(submissionNoticeTimer);
        submissionNoticeTimer = null;
        state.submissionNotice = null;
      }

      function showSubmissionNotice(notice) {
        clearSubmissionNotice();
        state.submissionNotice = notice;
        submissionNoticeTimer = window.setTimeout(function () {
          state.submissionNotice = null;
          submissionNoticeTimer = null;
          if (state.workbenchMode === "task-detail") renderWorkbench();
        }, 2600);
      }

      function showDraftSaveToast(title, detail, tone) {
        window.clearTimeout(draftToastHideTimer);
        draftSaveToast.className = "draft-save-toast" + (tone ? " " + tone : "");
        draftSaveToastTitle.textContent = title;
        draftSaveToastDetail.textContent = detail || "";
        draftSaveRetry.hidden = tone !== "failed";
        draftSaveToast.hidden = false;
        if (tone === "saved" || !tone) {
          draftToastHideTimer = window.setTimeout(function () {
            draftSaveToast.hidden = true;
          }, 1800);
        }
      }

      function scheduleDraftSave() {
        window.clearTimeout(draftSaveTimer);
        showDraftSaveToast("正在保存生成任务设置", "继续修改不会打断保存。", "saving");
        draftSaveTimer = window.setTimeout(function () {
          draftSaveTimer = null;
          showDraftSaveToast("生成任务设置已保存到本机", "返回当前商品项目时会直接恢复。", "saved");
        }, 2000);
      }

      function flushDraftSave() {
        if (!draftSaveTimer) return;
        window.clearTimeout(draftSaveTimer);
        draftSaveTimer = null;
        showDraftSaveToast("生成任务设置已保存到本机", "返回当前商品项目时会直接恢复。", "saved");
      }

      function retryDraftSave() {
        window.clearTimeout(draftSaveTimer);
        showDraftSaveToast("正在重新保存生成任务设置", "可以继续修改。", "saving");
        draftSaveTimer = window.setTimeout(function () {
          draftSaveTimer = null;
          showDraftSaveToast("生成任务设置已保存到本机", "返回当前商品项目时会直接恢复。", "saved");
        }, 900);
      }

      draftSaveRetry.addEventListener("click", retryDraftSave);

      function hasDraftSettings(config) {
        return config.items.some(function (item) {
          return item.on || item.subjectId || item.pendingMaterial || item.ref;
        });
      }

      function openDraftReplaceDialog(project, isDetail, config) {
        pendingDraftReplacement = { project: project, isDetail: isDetail, config: config };
        openModal(draftReplaceDialog, document.getElementById("keep-current-draft"));
      }

      function resetDraftSettings(project, isDetail, config) {
        config.setCount = 1;
        config.items.forEach(function (item) {
          item.on = false;
          item.subjectId = null;
          item.pendingMaterial = false;
          item.ref = false;
          item.referenceAspects = [];
        });
        state.workbenchMode = "edit";
        state.selectedTaskId = null;
        state.continueSource = null;
        state.copySource = "none";
        state.copyFunctionId = null;
        state.copyDrafts = {};
        state.copyConfirmed = {};
        state.firstGateConfirmed = false;
        navNote.textContent = "正在配置新的" + (isDetail ? "商品详情图" : "商品主图") + "生成任务";
        renderWorkbench();
        scheduleDraftSave();
      }

      function clearAbandonedTaskSettings(isDetail, config) {
        window.clearTimeout(draftSaveTimer);
        draftSaveTimer = null;
        draftSaveToast.hidden = true;
        config.setCount = 1;
        config.items.forEach(function (item) {
          item.on = false;
          item.subjectId = null;
          item.pendingMaterial = false;
          item.ref = false;
          item.referenceAspects = [];
        });
        state.workbenchMode = "edit";
        state.selectedTaskId = null;
        state.continueSource = null;
        state.copySource = "none";
        state.copyFunctionId = null;
        state.copyDrafts = {};
        state.copyConfirmed = {};
        state.firstGateConfirmed = false;
        navNote.textContent = "从上方商品主体图库拖入各功能图片设置";
        renderWorkbench();
      }

      function openTaskAbandonDialog(project, isDetail, config, entry) {
        var isNewProject = Boolean(project.isNew) || requestedScenario === "library-abandon-new";
        pendingTaskAbandonment = { project: project, isDetail: isDetail, config: config, isNewProject: isNewProject };
        taskAbandonTitle.textContent = isNewProject
          ? "放弃这次任务并删除新商品项目？"
          : entry === "return-to-settings"
            ? "要修改设置，先放弃这次任务"
            : "放弃这次任务？";
        taskAbandonDescription.textContent = isNewProject
          ? "“" + project.name + "”会被删除。"
          : project.hasAddedSubject
            ? "当前未提交的设置和本次新增的商品主体图会被删除。任务开始前已有的 " + project.originalSubjectCount + " 张商品主体图会继续保留。"
            : "当前未提交的设置会被删除。商品主体图库不会改变。";
        keepCurrentTask.textContent = entry === "return-to-settings" ? "继续确认文案" : "继续这次任务";
        confirmAbandonTask.textContent = isNewProject ? "放弃并删除项目" : "放弃这次任务";
        openModal(taskAbandonDialog, keepCurrentTask);
      }

      function bindTaskAbandonControl(project, isDetail, config) {
        var button = document.getElementById("abandon-task");
        if (!button) return;
        button.addEventListener("click", function () {
          openTaskAbandonDialog(project, isDetail, config);
        });
      }

      document.getElementById("keep-current-draft").addEventListener("click", function () {
        pendingDraftReplacement = null;
        draftReplaceDialog.close();
      });
      document.getElementById("discard-current-draft").addEventListener("click", function () {
        if (!pendingDraftReplacement) return;
        var replacement = pendingDraftReplacement;
        pendingDraftReplacement = null;
        draftReplaceDialog.close();
        resetDraftSettings(replacement.project, replacement.isDetail, replacement.config);
      });
      draftReplaceDialog.addEventListener("click", function (event) {
        if (event.target !== draftReplaceDialog) return;
        pendingDraftReplacement = null;
        draftReplaceDialog.close();
      });
      draftReplaceDialog.addEventListener("close", function () {
        pendingDraftReplacement = null;
      });
      keepCurrentTask.addEventListener("click", function () {
        pendingTaskAbandonment = null;
        taskAbandonDialog.close();
      });
      confirmAbandonTask.addEventListener("click", function () {
        if (!pendingTaskAbandonment) return;
        var abandonment = pendingTaskAbandonment;
        pendingTaskAbandonment = null;
        taskAbandonDialog.close();
        if (abandonment.isNewProject) {
          window.location.href = "index.html?scenario=library-populated";
          return;
        }
        if (abandonment.project.hasAddedSubject) {
          abandonment.project.hasAddedSubject = false;
          abandonment.project.subjectCount = abandonment.project.originalSubjectCount;
          renderSubjectPicker(abandonment.project);
        }
        clearAbandonedTaskSettings(abandonment.isDetail, abandonment.config);
      });
      taskAbandonDialog.addEventListener("click", function (event) {
        if (event.target !== taskAbandonDialog) return;
        pendingTaskAbandonment = null;
        taskAbandonDialog.close();
      });
      taskAbandonDialog.addEventListener("close", function () {
        pendingTaskAbandonment = null;
      });

      function openProjectDeleteDialog(project) {
        pendingProjectDeletion = project;
        var unresolvedBillingCount = project.unresolvedBillingCount || 0;
        confirmProjectDelete.hidden = false;
        if (unresolvedBillingCount > 0) {
          projectDeleteMode = "blocked";
          projectDeleteTitle.textContent = "暂时不能删除商品项目";
          projectDeleteDescription.textContent = "“" + project.name + "”还有 " + unresolvedBillingCount + " 笔账务没有收口。处理完成后才能删除。";
          cancelProjectDelete.textContent = "返回商品项目";
          confirmProjectDelete.className = "btn primary";
          confirmProjectDelete.textContent = "查看账务状态";
        } else {
          projectDeleteMode = "confirm";
          projectDeleteTitle.textContent = "删除“" + project.name + "”？";
          projectDeleteDescription.textContent = "商品主体图、生成任务和项目设置会从本机删除。此操作无法恢复。已导出的图片不会删除。";
          cancelProjectDelete.textContent = "取消";
          confirmProjectDelete.className = "btn danger";
          confirmProjectDelete.textContent = "删除商品项目";
        }
        openModal(projectDeleteDialog, cancelProjectDelete);
      }

      cancelProjectDelete.addEventListener("click", function () {
        projectDeleteDialog.close();
      });

      confirmProjectDelete.addEventListener("click", function () {
        if (!pendingProjectDeletion) return;
        if (projectDeleteMode === "blocked") {
          projectDeleteMode = "billing-status";
          projectDeleteTitle.textContent = pendingProjectDeletion.unresolvedBillingCount + " 笔账务正在处理";
          projectDeleteDescription.textContent = "系统会自动处理。全部收口后，你才能删除这个商品项目。";
          confirmProjectDelete.hidden = true;
          return;
        }
        var deletedProject = pendingProjectDeletion;
        window.location.href = "index.html?scenario=library-project-deleted&deleted=" + encodeURIComponent(deletedProject.id);
      });

      projectDeleteDialog.addEventListener("click", function (event) {
        if (event.target === projectDeleteDialog) projectDeleteDialog.close();
      });

      projectDeleteDialog.addEventListener("close", function () {
        pendingProjectDeletion = null;
        projectDeleteMode = "";
      });

      closeReferenceBoundary.addEventListener("click", function () {
        referenceBoundaryDialog.close();
      });

      referenceBoundaryDialog.addEventListener("click", function (event) {
        if (event.target === referenceBoundaryDialog) referenceBoundaryDialog.close();
      });

      var draftSettingControlSelector = [
        "[data-original-size]", "[data-original-style]", "[data-original-pick]", "[data-original-remove]",
        "[data-original-reference-add]", "[data-original-reference-replace]", "[data-original-reference-remove]",
        "[data-reference-aspect]", "[data-original-copy]", "[data-set-count]",
        "[data-copy-field]", "[data-copy-point]", "[data-copy-remove-point]", "[data-copy-add-point]",
        "[data-copy-confirm-set]"
      ].join(",");

      view.addEventListener("click", function (event) {
        if (event.target.closest(draftSettingControlSelector)) scheduleDraftSave();
      });
      view.addEventListener("input", function (event) {
        if (event.target.closest(draftSettingControlSelector)) scheduleDraftSave();
      });
      view.addEventListener("change", function (event) {
        if (event.target.closest(draftSettingControlSelector)) scheduleDraftSave();
      });
      view.addEventListener("drop", function (event) {
        if (event.target.closest("[data-subject-drop]")) scheduleDraftSave();
      });
      window.addEventListener("pagehide", flushDraftSave);
      document.addEventListener("visibilitychange", function () {
        if (document.visibilityState === "hidden") flushDraftSave();
      });

      function thumb(cls) {
        return '<div class="product-thumb ' + cls + '" aria-hidden="true"></div>';
      }

      function escapeHtml(value) {
        return String(value).replace(/[&<>"]/g, function (char) {
          return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[char];
        });
      }

      function gateSubjectView(project, item) {
        if (item.pendingMaterial) {
          return '<span class="gate-one-subject">' + thumb(project.thumb) + '<span><b>' + escapeHtml(project.file) + '</b><small>待确认商品主体</small></span></span>';
        }
        var subject = projectSubjects(project).find(function (candidate) { return candidate.id === item.subjectId; });
        if (!subject) return '<span class="gate-one-subject-missing">尚未选择商品主体图</span>';
        return '<span class="gate-one-subject">' + thumb(subject.thumb) + '<span><b>已选择商品主体图</b><small>由当前配置项绑定</small></span></span>';
      }

      function continueAfterFirstGate(project, isDetail, config) {
        state.firstGateConfirmed = true;
        var pendingItem = config.items.find(function (item) { return item.on && item.pendingMaterial; });
        if (pendingItem) {
          var nextParams = new URLSearchParams({
            flow: "confirm-material",
            project: project.id,
            name: project.name,
            materialFunction: pendingItem.id,
            setCount: String(config.setCount)
          });
          if (pendingItem.copy) nextParams.set("copyTreatment", pendingItem.copy);
          if (pendingItem.ref) {
            nextParams.set("referenceAdded", "1");
            nextParams.set("referenceAspects", (pendingItem.referenceAspects || []).join(","));
          }
          window.location.href = "index.html?" + nextParams.toString();
          return;
        }
        state.workbenchMode = "copy-confirm";
        state.copyFunctionId = null;
        navNote.textContent = "确认文案后开始生成任务";
        renderWorkbench();
      }

      function openFirstGate(project, isDetail, config) {
        if (blockNewGeneration()) return;
        var selectedItems = config.items.filter(function (item) { return item.on; });
        var totalImages = selectedItems.length * config.setCount;
        var maxCredits = totalImages * mainImageUnitPrice;
        var hasEnoughBalance = walletBalance >= maxCredits;
        var missingCredits = Math.max(0, maxCredits - walletBalance);
        var itemRows = selectedItems.map(function (item) {
          return '<li class="gate-one-source"><span><b>' + escapeHtml(item.name) + '</b><small>' + escapeHtml(item.desc) + '</small></span>' + gateSubjectView(project, item) + '</li>';
        }).join("");
        gateOneBody.innerHTML =
          '<section class="gate-one-section" aria-labelledby="gate-one-source-title"><div class="gate-one-section-head"><h3 id="gate-one-source-title">商品主体来源</h3><span>' + selectedItems.length + ' 个功能图片配置项</span></div><ul class="gate-one-source-list">' + itemRows + '</ul></section>' +
          '<section class="gate-one-metrics" aria-label="生成数量和费用上限">' +
            '<div><span>生成套数</span><strong>' + config.setCount + ' 套</strong></div>' +
            '<div><span>每套功能图片</span><strong>' + selectedItems.length + ' 张</strong></div>' +
            '<div><span>总图片张数</span><strong>' + totalImages + ' 张</strong></div>' +
            '<div><span>最大鸭豆数</span><strong>' + maxCredits.toLocaleString("zh-CN") + '</strong><small>' + mainImageUnitPrice + ' 鸭豆／张</small></div>' +
          '</section>' +
          (hasEnoughBalance
            ? '<section class="gate-one-balance sufficient" aria-label="余额足够"><div><b>当前鸭豆余额足够</b><span>余额 ' + walletBalance.toLocaleString("zh-CN") + ' 鸭豆，最多需要 ' + maxCredits.toLocaleString("zh-CN") + ' 鸭豆。</span></div></section>'
            : '<section class="gate-one-balance insufficient" aria-label="余额不足"><div><b>还差 ' + missingCredits.toLocaleString("zh-CN") + ' 鸭豆</b><span>当前余额 ' + walletBalance.toLocaleString("zh-CN") + ' 鸭豆，最多需要 ' + maxCredits.toLocaleString("zh-CN") + ' 鸭豆。</span></div></section>') +
          '<section class="gate-one-no-hold"><div><b>当前不会扣费</b><span>这一步只确认任务设置。完成文案确认并通过第二道门后，系统才会预扣鸭豆。</span></div></section>';
        gateOneContinue = function () { continueAfterFirstGate(project, isDetail, config); };
        gateOneContext = { project: project, isDetail: isDetail, config: config, maxCredits: maxCredits };
        gateOneConfirm.hidden = !hasEnoughBalance;
        gateOneRecharge.hidden = hasEnoughBalance;
        gateOneRecheck.hidden = hasEnoughBalance;
        gateOneRecharge.disabled = false;
        gateOneRecharge.textContent = "充值鸭豆";
        gateOneFootnote.textContent = hasEnoughBalance
          ? "按 Esc 也可以返回修改。本次确认不会预扣鸭豆。"
          : "余额不足时不能继续。本次检查不会预扣鸭豆。";
        openModal(gateOneDialog, hasEnoughBalance ? gateOneConfirm : gateOneRecharge);
      }

      gateOneBack.addEventListener("click", function () {
        gateOneContinue = null;
        gateOneContext = null;
        gateOneDialog.close("back");
        navNote.textContent = "已返回任务设置，可以继续修改";
      });

      gateOneRecharge.addEventListener("click", function () {
        if (!gateOneContext) return;
        walletBalance = gateOneContext.maxCredits + 80;
        walletBalanceLabel.textContent = walletBalance.toLocaleString("zh-CN");
        gateOneRecharge.disabled = true;
        gateOneRecharge.textContent = "已打开充值页面";
        gateOneFootnote.textContent = "完成充值后，请重新检查余额。";
      });

      gateOneRecheck.addEventListener("click", function () {
        if (!gateOneContext) return;
        var context = gateOneContext;
        gateOneDialog.close("recheck");
        openFirstGate(context.project, context.isDetail, context.config);
      });

      gateOneConfirm.addEventListener("click", function () {
        var next = gateOneContinue;
        gateOneContinue = null;
        gateOneContext = null;
        gateOneDialog.close("confirm");
        if (next) next();
      });

      gateOneDialog.addEventListener("cancel", function () {
        gateOneContinue = null;
        gateOneContext = null;
        navNote.textContent = "已返回任务设置，可以继续修改";
      });

      function gateTwoSummary(context) {
        return '<section class="gate-one-metrics gate-two-metrics" aria-label="提交数量和最大预扣鸭豆数">' +
          '<div><span>本次总图片张数</span><strong>' + context.totalImages + ' 张</strong><small>' + context.config.setCount + ' 套 × 每套 ' + context.selectedItems.length + ' 张</small></div>' +
          '<div><span>最多预扣鸭豆数</span><strong>' + context.maxCredits.toLocaleString("zh-CN") + '</strong><small>' + mainImageUnitPrice + ' 鸭豆／张</small></div>' +
        '</section>';
      }

      function renderSecondGate(mode) {
        if (!gateTwoContext) return;
        var isRestart = Boolean(gateTwoContext.restartSourceTask);
        gateTwoMode = mode;
        gateTwoStep.textContent = "第二道门";
        gateTwoRecharge.hidden = true;
        gateTwoRecharge.disabled = false;
        gateTwoRecharge.textContent = "充值鸭豆";
        gateTwoBack.hidden = false;
        gateTwoBack.disabled = false;
        gateTwoConfirm.hidden = false;
        gateTwoConfirm.disabled = false;

        if (mode === "confirm") {
          gateTwoTitle.textContent = isRestart ? "确认重新发起任务" : "确认并提交生成任务";
          gateTwoIntro.textContent = isRestart ? "请核对原失败任务的图片数量和最大鸭豆数。确认后会建立一个新任务。" : "请核对本次图片数量和最大鸭豆数。确认后将提交任务。";
          gateTwoBody.innerHTML = gateTwoSummary(gateTwoContext) +
            '<section class="gate-two-rule"><strong>按实际生成成功的张数结算</strong><span>最多预扣 ' + gateTwoContext.maxCredits.toLocaleString("zh-CN") + ' 鸭豆。没有成功生成的图片不会结算。</span></section>' +
            (isRestart
              ? '<section class="gate-two-rule lock"><strong>沿用原失败任务设置</strong><span>原失败任务和原结算保持不变。确认后会按相同设置建立新任务。</span></section>'
              : '<section class="gate-two-rule lock"><strong>提交后不能修改设置</strong><span>商品主体图、文案、功能图片和生成套数将按当前确认内容执行。</span></section>');
          gateTwoFootnote.textContent = isRestart ? "确认前可以返回原失败任务。" : "提交后不能修改本次任务设置。";
          gateTwoBack.textContent = isRestart ? "返回失败任务" : "再看看";
          gateTwoConfirm.textContent = isRestart ? "确认并重新发起" : "确认并提交";
          return;
        }

        if (mode === "confirming") {
          gateTwoTitle.textContent = isRestart ? "正在确认新任务" : "正在确认任务";
          gateTwoIntro.textContent = "正在确认鸭豆预扣和任务创建结果，请稍候。";
          gateTwoBody.innerHTML = gateTwoSummary(gateTwoContext) +
            '<section class="gate-two-status confirming" role="status"><span class="gate-two-spinner" aria-hidden="true"></span><div><strong>系统正在自动处理</strong><span>确认完成后会自动打开生成任务，不需要再次操作。</span></div></section>';
          gateTwoFootnote.textContent = "确认完成前，本次设置保持锁定。";
          gateTwoBack.hidden = true;
          gateTwoConfirm.textContent = "正在确认…";
          gateTwoConfirm.disabled = true;
          return;
        }

        if (mode === "rejected") {
          var missingCredits = Math.max(0, gateTwoContext.maxCredits - walletBalance);
          gateTwoTitle.textContent = "鸭豆余额不足，任务没有提交";
          gateTwoIntro.textContent = "提交前余额发生变化。当前余额不足以完成本次预扣。";
          gateTwoBody.innerHTML =
            '<section class="gate-two-status rejected" role="alert"><div><strong>还差 ' + missingCredits.toLocaleString("zh-CN") + ' 鸭豆</strong><span>当前余额 ' + walletBalance.toLocaleString("zh-CN") + ' 鸭豆，最多需要 ' + gateTwoContext.maxCredits.toLocaleString("zh-CN") + ' 鸭豆。</span></div></section>' +
            (isRestart
              ? '<section class="gate-two-rule"><strong>原失败任务保持不变</strong><span>充值后可以继续使用相同设置重新发起。</span></section>'
              : '<section class="gate-two-rule"><strong>文案和设置已经保留</strong><span>充值后可以继续提交，不需要重新填写。</span></section>');
          gateTwoFootnote.textContent = "本次没有预扣鸭豆，也没有创建生成任务。";
          gateTwoBack.textContent = isRestart ? "返回失败任务" : "返回文案确认";
          gateTwoRecharge.hidden = false;
          gateTwoConfirm.hidden = true;
          return;
        }

        gateTwoTitle.textContent = isRestart ? "余额已更新，可以重新发起" : "余额已更新，可以重新提交";
        gateTwoIntro.textContent = isRestart ? "当前余额足够。原失败任务的设置保持不变。" : "当前余额足够。本次文案和设置保持不变。";
        gateTwoBody.innerHTML =
          '<section class="gate-two-status recovered" role="status"><div><strong>当前余额 ' + walletBalance.toLocaleString("zh-CN") + ' 鸭豆</strong><span>最多需要 ' + gateTwoContext.maxCredits.toLocaleString("zh-CN") + ' 鸭豆。</span></div></section>' +
          gateTwoSummary(gateTwoContext);
        gateTwoFootnote.textContent = isRestart ? "重新发起前仍然可以返回原失败任务。" : "重新提交前仍然可以返回文案确认。";
        gateTwoBack.textContent = isRestart ? "返回失败任务" : "返回文案确认";
        gateTwoConfirm.textContent = isRestart ? "确认并重新发起" : "重新提交";
      }

      function openSecondGate(project, isDetail, config, mode) {
        if (blockNewGeneration()) return;
        var selectedItems = config.items.filter(function (item) { return item.on; });
        var totalImages = selectedItems.length * config.setCount;
        gateTwoContext = {
          project: project,
          isDetail: isDetail,
          config: config,
          selectedItems: selectedItems,
          selectedNames: selectedItems.map(function (item) { return item.name; }),
          totalImages: totalImages,
          maxCredits: totalImages * mainImageUnitPrice
        };
        renderSecondGate(mode || "confirm");
        openModal(gateTwoDialog, gateTwoConfirm.hidden ? gateTwoBack : gateTwoConfirm);
      }

      function openSecondGateForRestart(project, failedTask, mode) {
        if (blockNewGeneration()) return;
        var setCount = failedTask.setCount || 1;
        var itemCount = Math.max(1, Math.ceil(failedTask.total / setCount));
        gateTwoContext = {
          project: project,
          isDetail: false,
          config: { setCount: setCount },
          selectedItems: Array.from({ length: itemCount }, function (_, index) { return { name: "功能图片 " + (index + 1) }; }),
          selectedNames: [failedTask.name],
          totalImages: failedTask.total,
          maxCredits: failedTask.total * mainImageUnitPrice,
          restartSourceTask: failedTask
        };
        renderSecondGate(mode || "confirm");
        openModal(gateTwoDialog, gateTwoConfirm.hidden ? gateTwoBack : gateTwoConfirm);
      }

      function finishSecondGate(context) {
        window.clearTimeout(gateTwoSubmitTimer);
        gateTwoSubmitTimer = null;
        gateTwoContext = null;
        if (gateTwoDialog.open) gateTwoDialog.close("accepted");
        if (context.restartSourceTask) {
          state.restartedTaskSequence += 1;
          var failedTask = context.restartSourceTask;
          var restartedTask = {
            taskId: "restarted-service-" + state.restartedTaskSequence,
            projectId: context.project.id,
            name: failedTask.name,
            meta: "刚刚 · 0 / " + failedTask.total + " 张",
            total: failedTask.total,
            itemStates: Array(failedTask.total).fill("pending"),
            setCount: failedTask.setCount || 1,
            state: "wait",
            stateText: "排队中",
            thumb: failedTask.thumb
          };
          state.restartedTasks.unshift(restartedTask);
          state.workbenchMode = "task-detail";
          state.selectedTaskId = restartedTask.taskId;
          showSubmissionNotice({ tone: "accepted", title: "已建立新的生成任务", detail: "已使用相同设置预扣 " + restartedTask.total + " 张图片额度，共 " + context.maxCredits.toLocaleString("zh-CN") + " 鸭豆。新任务正在排队。" });
          navNote.textContent = "新任务正在排队；原失败任务和原结算保持不变";
          renderWorkbench();
          return;
        }
        state.createdContinuation = true;
        state.createdContinuationName = context.selectedNames.join("、");
        state.createdContinuationTotalImages = context.totalImages;
        state.createdContinuationSetCount = context.config.setCount;
        state.selectedTaskId = "continued-scene";
        state.workbenchMode = "task-detail";
        showSubmissionNotice({ tone: "accepted", title: "生成任务已提交", detail: "已预扣 " + context.totalImages + " 张图片额度，共 " + context.maxCredits.toLocaleString("zh-CN") + " 鸭豆。任务正在排队。" });
        navNote.textContent = "生成任务已进入排队中，轮到它时自动开始";
        renderWorkbench();
      }

      function submitSecondGate() {
        if (!gateTwoContext) return;
        var context = gateTwoContext;
        renderSecondGate("confirming");
        gateTwoSubmitTimer = window.setTimeout(function () {
          finishSecondGate(context);
        }, 900);
      }

      gateTwoBack.addEventListener("click", function () {
        if (["confirm", "rejected", "recovered"].indexOf(gateTwoMode) < 0) return;
        var wasRestart = Boolean(gateTwoContext && gateTwoContext.restartSourceTask);
        gateTwoContext = null;
        gateTwoDialog.close("back");
        navNote.textContent = wasRestart ? "已返回原失败任务；原任务和原结算没有改变" : "可以继续检查已确认文案";
      });

      gateTwoRecharge.addEventListener("click", function () {
        if (!gateTwoContext) return;
        walletBalance = gateTwoContext.maxCredits + 40;
        walletBalanceLabel.textContent = walletBalance.toLocaleString("zh-CN");
        renderSecondGate("recovered");
      });

      gateTwoConfirm.addEventListener("click", function () {
        if (gateTwoMode === "confirm" || gateTwoMode === "recovered") submitSecondGate();
      });

      gateTwoDialog.addEventListener("cancel", function (event) {
        if (["confirm", "rejected", "recovered"].indexOf(gateTwoMode) < 0) {
          event.preventDefault();
          return;
        }
        var wasRestart = Boolean(gateTwoContext && gateTwoContext.restartSourceTask);
        gateTwoContext = null;
        navNote.textContent = wasRestart ? "已返回原失败任务；原任务和原结算没有改变" : "可以继续检查已确认文案";
      });

      function taskQueueData(project) {
        var tasks = project.isNew ? [] : [
          { taskId: "running-main", name: "商品主图生成任务", meta: "今天 16:18 · 3 / 5 张", total: 5, itemStates: ["delivered", "delivered", "delivered", "generating", "pending"], state: "running", stateText: "进行中", thumb: project.thumb },
          { taskId: "completed-main", name: "商品主图生成任务", meta: "07-16 10:42 · 3 套 · 3 张成图", total: 3, itemStates: ["delivered", "delivered", "delivered"], state: "ready", stateText: "已完成", thumb: project.thumb },
          { taskId: "partial-main", name: "商品主图生成任务", meta: "07-12 19:07 · 1 / 3 张已交付", total: 3, itemStates: ["delivered", "failed-safety", "ungenerated"], state: "partial", stateText: "部分完成", thumb: project.sideThumb },
          { taskId: "failed-main", name: "商品主图生成任务", meta: "07-11 14:22 · 0 / 3 张已交付", total: 3, itemStates: state.failedTaskKind === "recovery-not-started" ? ["ungenerated", "ungenerated", "ungenerated"] : [state.failedTaskKind === "safety" ? "failed-safety" : "failed-service", "ungenerated", "ungenerated"], failureKind: state.failedTaskKind, state: "failed", stateText: "失败", thumb: project.sideThumb },
          { taskId: "completed-main-old", name: "商品主图生成任务", meta: "07-09 09:31 · 2 套 · 2 张成图", total: 2, itemStates: ["delivered", "delivered"], state: "ready", stateText: "已完成", thumb: project.thumb }
        ];
        if (requestedScenario === "recovery-task-running") {
          tasks[0].meta = "今天 16:18 · 3 / 5 张";
        }
        if (requestedScenario === "recovery-task-partial") {
          tasks[2].meta = "今天 16:31 · 3 / 5 张已交付";
          tasks[2].total = 5;
          tasks[2].itemStates = ["delivered", "delivered", "delivered", "failed-service", "ungenerated"];
        }
        if (requestedScenario === "recovery-task-failed") {
          tasks[3].failureKind = "recovery-not-started";
        }
        if (requestedScenario === "billing-settlement-pending") {
          tasks[1].billingState = "pending";
        }
        if (state.createdContinuation) {
          tasks.unshift({ taskId: "continued-scene", name: state.createdContinuationName + "生成任务", meta: "刚刚 · 0 / " + state.createdContinuationTotalImages + " 张", total: state.createdContinuationTotalImages, itemStates: Array(state.createdContinuationTotalImages).fill("pending"), setCount: state.createdContinuationSetCount, state: "wait", stateText: "排队中", thumb: project.thumb });
        }
        return state.restartedTasks.filter(function (task) { return task.projectId === project.id; }).concat(tasks);
      }

      function taskQueueItems(project) {
        var tasks = taskQueueData(project);
        if (!tasks.length) return '<div class="queue-empty">还没有生成任务</div>';
        return tasks.map(function (task) {
          return '<button type="button" class="queue-item' + (state.selectedTaskId === task.taskId ? " current" : "") + '" data-task-id="' + task.taskId + '" aria-label="查看' + escapeHtml(task.name) + '">' +
            thumb(task.thumb) +
            '<span class="item-copy"><span class="item-name">' + escapeHtml(task.name) + '</span><span class="item-id">' + escapeHtml(task.meta) + '</span><span class="item-state ' + task.state + '">' + escapeHtml(task.stateText) + '</span></span>' +
          '</button>';
        }).join("");
      }

      function taskOutputs(project, task) {
        var outputs = [
          { id: "OUT-MARKETING", name: "营销图 · 柔润留香", functionName: "营销图", setName: "第 1 套", visualPlan: "视觉方案 VS-0629-A2", subjectId: "front", subject: "商品主体图 1", thumb: project.thumb },
          { id: "OUT-DETAIL", name: "细节图 · 乳霜质感", functionName: "细节图", setName: "第 2 套", visualPlan: "视觉方案 VS-0629-B1", subjectId: "front", subject: "商品主体图 1", thumb: "thumb-paper", usedReference: true },
          { id: "OUT-WHITE", name: "白底图 · 标准展示", functionName: "白底图", setName: "第 3 套", visualPlan: "视觉方案 VS-0629-C4", subjectId: "front", subject: "商品主体图 1", thumb: project.sideThumb },
          { id: "OUT-SCENE", name: "场景图 · 厨房晨光", functionName: "场景图", setName: "第 4 套", visualPlan: "视觉方案 VS-0629-D3", subjectId: "front", subject: "商品主体图 1", thumb: "thumb-warm" },
          { id: "OUT-MACRO", name: "细节图 · 泡沫特写", functionName: "细节图", setName: "第 5 套", visualPlan: "视觉方案 VS-0629-E2", subjectId: "front", subject: "商品主体图 1", thumb: "thumb-night" }
        ];
        var total = task && task.total ? task.total : 3;
        return Array.from({ length: total }, function (_, index) {
          var copy = Object.assign({}, outputs[index % outputs.length]);
          copy.id = copy.id + "-" + (index + 1);
          copy.setName = "第 " + (index + 1) + " 张";
          copy.itemState = task && task.itemStates ? task.itemStates[index] : "delivered";
          return copy;
        });
      }

      function taskStatus(task) {
        if (task.state === "ready") return { className: "complete", label: "已完成" };
        if (task.state === "partial") return { className: "failed", label: "部分完成" };
        if (task.state === "failed") return { className: "failed", label: "失败" };
        if (task.state === "wait") return { className: "wait", label: "排队中" };
        return { className: "running", label: "进行中" };
      }

      function taskSetCount(task) {
        if (task.setCount) return task.setCount + " 套";
        var match = task.meta.match(/(\d+) 套/);
        return match ? match[1] + " 套" : "按任务保存";
      }

      function taskItemStateMeta(itemState) {
        if (itemState === "delivered") return { label: "已交付", className: "delivered" };
        if (itemState === "generating") return { label: "生成中", className: "generating" };
        if (itemState === "failed-safety") return { label: "已失败", reason: "未通过内容安全检查", className: "failed" };
        if (itemState === "failed-service") return { label: "已失败", reason: "生成服务暂时不可用", className: "failed" };
        if (itemState === "ungenerated") return { label: "未生成", className: "ungenerated" };
        return { label: "待生成", className: "pending" };
      }

      function renderTaskOutput(output) {
        var itemStatus = taskItemStateMeta(output.itemState);
        var placeholderText = output.itemState === "generating" ? "图片生成中" : output.itemState === "pending" ? "等待前序图片" : output.itemState === "ungenerated" ? "未生成" : itemStatus.reason;
        var visual = output.itemState === "delivered"
          ? thumb(output.thumb)
          : '<span class="generation-placeholder ' + itemStatus.className + '"><strong>' + escapeHtml(placeholderText) + '</strong>' + (output.itemState === "generating" ? '<span class="generation-placeholder-progress" role="progressbar" aria-label="当前图片正在生成" aria-valuetext="生成中"><i></i></span>' : '') + '</span>';
        var detail = output.itemState === "generating" ? "完成后会自动显示" : output.itemState === "pending" ? "轮到这张图片时自动开始" : output.itemState === "ungenerated" ? "任务结束前没有再次发起生成" : output.itemState.indexOf("failed") === 0 ? itemStatus.reason : output.setName + " · " + output.visualPlan;
        var continueAction = output.usedReference ? '' : '<button type="button" data-task-output-continue="' + output.id + '">继续生成</button>';
        var actions = output.itemState === "delivered" ? '<div class="task-output-actions"><button type="button" data-task-output-preview="' + output.id + '">查看</button><button type="button" data-task-output-export="' + output.id + '">导出</button>' + continueAction + '</div>' : '';
        return '<article class="task-output state-' + itemStatus.className + '">' + visual + '<div class="task-output-copy"><div class="task-output-name"><b>' + escapeHtml(output.name) + '</b><span class="image-state ' + itemStatus.className + '">' + itemStatus.label + '</span></div><span class="task-output-meta">' + escapeHtml(detail) + '</span>' + actions + '</div></article>';
      }

      function renderSettlement(task, outputs) {
        if (task.billingState === "pending") {
          return '<div class="task-settlement-pending" role="status"><span class="task-settlement-pending-mark" aria-hidden="true">…</span><span><strong>结算处理中</strong><span>图片已经保存。网络恢复后会自动处理，不影响查看和导出。</span></span></div>';
        }
        var delivered = outputs.filter(function (output) { return output.itemState === "delivered"; }).length;
        var held = task.total * mainImageUnitPrice;
        var charged = delivered * mainImageUnitPrice;
        return '<div class="task-settlement"><div><span>预扣额度</span><strong>' + task.total + ' 张 · ' + held + ' 鸭豆</strong></div><div><span>实际结算</span><strong>' + delivered + ' 张 · ' + charged + ' 鸭豆</strong></div><div><span>已释放</span><strong>' + (task.total - delivered) + ' 张 · ' + (held - charged) + ' 鸭豆</strong></div></div>';
      }

      function renderTaskDetail(project, task) {
        var status = taskStatus(task);
        var currentOutputs = taskOutputs(project, task);
        var eventTitle = task.state === "ready" ? "生成完成" : task.state === "partial" ? "部分完成" : task.state === "failed" ? "任务已经失败" : task.state === "wait" ? "排队中" : "正在生成";
        var eventClass = task.state === "ready" ? "complete" : task.state === "partial" || task.state === "failed" ? "failed" : task.state === "wait" ? "wait" : "running";
        var eventBody = '';
        if (task.state === "wait") eventBody += '<div class="queue-wait-note">这台电脑同时只生成一个任务。轮到它时自动开始。离开本页不会中断任务。</div>';
        if (task.state === "failed") {
          var failureCopy = task.failureKind === "safety"
            ? "画面要求没有通过内容审核。任务已经结束，未交付图片的预扣额度已经释放。"
            : task.failureKind === "recovery-not-started"
              ? "应用关闭前，本次任务尚未开始生成。任务已经结束，预扣额度已经释放。"
              : "生成服务暂时不可用。任务已停止，未交付图片的预扣额度已经释放。";
          eventBody += '<div class="failure">' + failureCopy + '</div>';
          if (task.failureKind !== "safety") eventBody += '<div class="task-level-actions"><button class="btn primary" type="button" data-restart-task>用相同设置重新发起</button></div>';
        }
        eventBody += '<div class="task-results-head"><h3>本次任务图片</h3><span>每张承诺图片都保留明确状态</span></div><div class="task-output-grid">' + currentOutputs.map(renderTaskOutput).join("") + '</div>';
        if (["ready", "partial", "failed"].indexOf(task.state) >= 0) eventBody += renderSettlement(task, currentOutputs);
        var latestEvent = '<article class="task ' + eventClass + '"><div class="task-head"><div class="task-title"><h3>' + eventTitle + '</h3><p>' + escapeHtml(task.meta) + '</p></div><span class="status ' + status.className + '">' + status.label + '</span></div>' + eventBody + '</article>';
        var submissionNotice = state.submissionNotice
          ? '<aside class="submission-notice ' + state.submissionNotice.tone + '" role="status"><span class="submission-notice-icon" aria-hidden="true"><svg viewBox="0 0 16 16"><path d="m4 8 2.5 2.5L12 5"/></svg></span><span class="submission-notice-copy"><strong>' + escapeHtml(state.submissionNotice.title) + '</strong><span>' + escapeHtml(state.submissionNotice.detail) + '</span></span><small>刚刚</small></aside>'
          : '';
        return '<div class="task-detail">' + submissionNotice +
          '<header class="task-detail-head"><div class="task-detail-title"><h2>' + escapeHtml(task.name) + '</h2><p>' + escapeHtml(task.meta) + '</p></div><span class="status ' + status.className + '">' + status.label + '</span></header>' +
          '<div class="task-detail-timeline-head"><h3>任务时间线</h3><span>最新进度在前</span></div>' +
          '<div class="timeline task-result-timeline">' + latestEvent +
            '<article class="task complete"><div class="task-head"><div class="task-title"><h3>已提交生成设置</h3><p>图片尺寸、生成套数和功能图片配置已经写入任务</p></div><span class="status complete">已保存</span></div><div class="task-parameter-list" aria-label="本次任务参数"><div class="task-parameter"><span>商品主体图</span><strong>按功能图片分别使用</strong></div><div class="task-parameter"><span>图片尺寸</span><strong>3:4 · 1024×1536</strong></div><div class="task-parameter"><span>生成套数</span><strong>' + taskSetCount(task) + '</strong></div><div class="task-parameter"><span>视觉设计</span><strong>每套独立保存</strong></div></div></article>' +
            '<article class="task complete"><div class="task-head"><div class="task-title"><h3>已创建生成任务</h3><p>本次任务的商品主体图和生成参数已保存在当前商品项目</p></div><span class="status complete">已保存</span></div></article>' +
          '</div>' +
        '</div>';
      }

      function continueFromTaskOutput(project, source) {
        if (blockNewGeneration()) return;
        if (!source || source.usedReference) return;
        if (taskPreviewDialog.open) taskPreviewDialog.close();
        activeTaskOutput = null;
        state.continueSource = source;
        state.workbenchMode = "continue-edit";
        state.copySource = "history";
        state.copyFunctionId = null;
        state.copyDrafts = {};
        state.copyConfirmed = {};
        state.selectedTaskId = null;
        project.main.items.forEach(function (item) { item.on = false; });
        project.main.setCount = 1;
        state.tab = "main";
        tabs.forEach(function (tabButton) { tabButton.setAttribute("aria-selected", String(tabButton.getAttribute("data-tab") === "main")); });
        navNote.textContent = "请选择要继续生成的功能图片";
        renderWorkbench();
      }

      function openTaskPreview(output) {
        activeTaskOutput = output;
        taskPreviewTitle.textContent = output.name;
        taskPreviewBody.innerHTML = '<div class="task-preview-image">' + thumb(output.thumb) + '</div><div class="task-preview-facts"><div><span>功能图片</span><strong>' + escapeHtml(output.functionName) + '</strong></div><div><span>生成套数</span><strong>' + escapeHtml(output.setName) + '</strong></div><div><span>视觉设计</span><strong>' + escapeHtml(output.visualPlan) + '</strong></div><div><span>商品主体图</span><strong>' + escapeHtml(output.subject) + '</strong></div></div>';
        taskPreviewContinue.hidden = Boolean(output.usedReference);
        openModal(taskPreviewDialog, document.querySelector('[data-close-task-dialog="task-preview-dialog"]'));
      }

      function openTaskExport(output) {
        activeTaskOutput = output;
        showDraftSaveToast("图片已导出", "已保存到设置页面中的默认导出路径。", "saved");
      }

      taskPreviewExport.addEventListener("click", function () {
        if (!activeTaskOutput) return;
        taskPreviewDialog.close();
        openTaskExport(activeTaskOutput);
      });

      taskPreviewContinue.addEventListener("click", function () {
        continueFromTaskOutput(projects[state.projectIndex], activeTaskOutput);
      });

      document.addEventListener("click", function (event) {
        var closeButton = event.target.closest("[data-close-task-dialog]");
        if (closeButton) {
          var dialog = document.getElementById(closeButton.getAttribute("data-close-task-dialog"));
          if (dialog && dialog.open) dialog.close();
          return;
        }
      });

      function renderContinueSource() {
        if (!state.continueSource) return "";
        var source = state.continueSource;
        return '<aside class="continue-source" aria-label="继续生成来源">' + thumb(source.thumb) + '<div class="continue-source-copy"><strong>基于“' + escapeHtml(source.name) + '”继续生成</strong><span>已沿用 ' + escapeHtml(source.subject) + ' 和所选成图的视觉设计</span></div><div class="continue-source-rule">在下方选择要新增的功能图片。<br>新参考图只会替换你勾选的视觉内容。</div></aside>';
      }

      function projectSubjects(project) {
        var subjects = [];
        var originalCount = typeof project.originalSubjectCount === "number" ? project.originalSubjectCount : project.subjectCount;
        if (originalCount > 0) subjects.push({ id: "front", name: "商品主体图 1", origin: "已保存到当前商品项目", thumb: project.thumb });
        if (originalCount > 1) subjects.push({ id: "side", name: "商品主体图 2", origin: "已保存到当前商品项目", thumb: project.sideThumb });
        if (project.hasAddedSubject) subjects.push({ id: "added", name: "商品主体图 " + (originalCount + 1), origin: "由刚确认的商品素材保存", thumb: project.sideThumb });
        return subjects;
      }

      function renderSubjectPicker(project) {
        var subjects = projectSubjects(project);
        subjectPicker.innerHTML =
          '<div class="subject-picker-copy"><h2 id="subject-picker-title">商品主体图库</h2><div class="subject-picker-meta"><span class="subject-picker-guide">拖到下方使用，或在功能图片中直接选择</span><span class="subject-picker-count">已保存 ' + project.subjectCount + ' 张</span></div></div>' +
          subjects.map(function (subject) {
            return '<div class="subject-option" draggable="true" data-subject="' + subject.id + '" role="listitem" aria-label="' + escapeHtml(subject.name) + '，可拖拽到功能图片设置，也可以在功能图片中直接选择">' + thumb(subject.thumb) + '<span><b>' + escapeHtml(subject.name) + '</b><span>' + escapeHtml(subject.origin) + ' · 可拖拽</span></span></div>';
          }).join("") +
          '<button type="button" class="subject-add" id="add-material-from-workbench"><span><b>添加新的商品素材</b><span>先选择要生成的功能图片，再完成设置和商品主体确认。</span></span></button>';

        Array.prototype.forEach.call(subjectPicker.querySelectorAll("[data-subject]"), function (subjectCard) {
          subjectCard.addEventListener("dragstart", function (event) {
            event.dataTransfer.effectAllowed = "copy";
            event.dataTransfer.setData("text/product-subject-id", subjectCard.getAttribute("data-subject"));
            subjectCard.classList.add("dragging");
          });
          subjectCard.addEventListener("dragend", function () {
            subjectCard.classList.remove("dragging");
          });
        });

        document.getElementById("add-material-from-workbench").addEventListener("click", function () {
          if (blockNewGeneration()) return;
          window.location.href = "index.html?flow=add-material&project=" + encodeURIComponent(project.id);
        });
        applyServiceGateToControls();
      }

      function renderOriginalSizes(sizes, selected) {
        return sizes.map(function (size) {
          var glyph = size.shape === "custom"
            ? '<span class="original-size-glyph custom" aria-hidden="true">☷</span>'
            : '<span class="original-size-glyph ' + size.shape + '" aria-hidden="true"></span>';
          return '<button type="button" class="original-size' + (selected === size.id ? " on" : "") + '" data-original-size="' + size.id + '" aria-pressed="' + (selected === size.id) + '">' +
            glyph + '<span class="original-size-copy"><span class="original-size-ratio">' + size.ratio + '</span><span class="original-size-px">' + size.px + '</span></span></button>';
        }).join("");
      }

      function renderOriginalStyles(selected) {
        return detailStyles.map(function (style) {
          return '<button type="button" class="original-style' + (selected === style ? " on" : "") + '" data-original-style="' + escapeHtml(style) + '" aria-pressed="' + (selected === style) + '">' + escapeHtml(style) + '</button>';
        }).join("");
      }

      function renderSetCounts(selected) {
        return '<div class="original-set-counts" role="group" aria-label="生成套数">' + [1, 2, 3, 4].map(function (count) {
          return '<button type="button" class="original-set-count' + (selected === count ? " on" : "") + '" data-set-count="' + count + '" aria-pressed="' + (selected === count) + '">' + count + ' 套</button>';
        }).join("") + '<span class="original-set-help">每套按当前选择生成对应数量的功能图片</span></div>';
      }

      function renderOriginalPicks(items, isDetail) {
        return '<div class="original-picks ' + (isDetail ? "sections" : "shots") + '">' + items.map(function (item, index) {
          return '<button type="button" class="original-pick' + (item.on ? " on" : "") + '" data-original-pick="' + index + '" aria-pressed="' + item.on + '"' + (item.pendingMaterial ? " disabled" : "") + '>' +
            '<span class="original-pick-box" aria-hidden="true">✓</span><span><span class="original-pick-name">' + escapeHtml(item.name) + '</span><span class="original-pick-desc">' + escapeHtml(item.desc) + '</span></span></button>';
        }).join("") + '</div>';
      }

      function renderSubjectDrop(item, index, project) {
        if (item.pendingMaterial) {
          return '<div class="original-config-label">商品素材 <span>待确认商品主体</span></div><div class="original-subject-drop pending-material">' + thumb(project.thumb) + '<span class="original-subject-drop-copy"><b>商品素材_洗洁精.jpg</b><span>下一步统一识别并确认商品主体</span></span></div>';
        }
        var subjectOptions = projectSubjects(project).map(function (candidate) {
          return '<option value="' + candidate.id + '"' + (candidate.id === item.subjectId ? " selected" : "") + '>' + escapeHtml(candidate.name) + '</option>';
        }).join("");
        var subjectSelect = '<label class="original-subject-select"><span>直接选择商品主体图</span><select data-subject-select="' + index + '"><option value="">请选择</option>' + subjectOptions + '</select></label>';
        var subject = projectSubjects(project).find(function (candidate) { return candidate.id === item.subjectId; });
        if (!subject) {
          return '<div class="original-config-label">商品主体图 <span>必选</span></div><div class="original-subject-drop" data-subject-drop="' + index + '"><span class="original-subject-drop-icon" aria-hidden="true">↓</span><span class="original-subject-drop-copy"><b>从上方拖入商品主体图</b><span>也可以使用下方选择框</span></span></div>' + subjectSelect;
        }
        return '<div class="original-config-label">商品主体图 <span>已绑定</span></div><div class="original-subject-drop has-subject" data-subject-drop="' + index + '">' + thumb(subject.thumb) + '<span class="original-subject-drop-copy"><b>' + escapeHtml(subject.name) + '</b><span>' + escapeHtml(subject.origin) + ' · 拖入其他主体图可替换</span></span></div>' + subjectSelect;
      }

      function renderReferenceControl(item, index) {
        if (!item.ref) {
          return '<button type="button" class="original-reference-empty" data-original-reference-add="' + index + '"><span class="original-reference-add-icon" aria-hidden="true">+</span><span><b>添加参考图</b><span>从本机选择一张图片</span></span></button>';
        }
        var referenceName = item.referenceName || item.name + '_参考图.jpg';
        return '<div class="original-reference-selected"><span class="original-reference-thumb" aria-hidden="true"></span><span class="original-reference-file"><b>' + escapeHtml(referenceName) + '</b><span>已添加 1 张参考图</span></span><span class="original-reference-actions"><button type="button" data-original-reference-replace="' + index + '">更换</button><button type="button" class="remove" data-original-reference-remove="' + index + '">移除</button></span></div>';
      }

      function renderOriginalConfig(item, index, project) {
        var referenceAspects = [
          { id: "composition", label: "画面构图" },
          { id: "scene", label: "场景与道具" },
          { id: "typography", label: "字体与文字样式" },
          { id: "color", label: "色彩体系" }
        ];
        var selectedReferenceAspects = item.referenceAspects || [];
        var keepCopyLabel = state.copySource === "material" ? "使用素材原文" : "沿用所选成图文案";
        var keepCopyNote = state.copySource === "material"
          ? "把商品素材中识别到的文案按原有层级填入每一套"
          : "把所选成图已经确认的文案填入当前任务";
        var rewriteCopyNote = state.copySource === "material"
          ? "根据商品素材中识别到的文案草拟新文案"
          : "根据所选成图已经确认的文案草拟新文案";
        var referenceBasis = '<div class="original-reference-basis"><div class="original-reference-basis-head">参考这张图的<span>' + (item.ref ? "至少选择一项" : "上传后可选") + '</span></div><div class="original-reference-basis-grid">' + referenceAspects.map(function (aspect) {
              var checked = selectedReferenceAspects.indexOf(aspect.id) >= 0;
              return '<label class="original-reference-basis-option"><input type="checkbox" data-reference-aspect="' + aspect.id + '" data-original-index="' + index + '"' + (checked ? " checked" : "") + (item.ref ? "" : " disabled") + '><span>' + aspect.label + '</span></label>';
            }).join("") + '</div></div>';
        var copyControl = item.copy
          ? (state.copySource === "none"
            ? '<div class="original-config-row">文案<span class="original-no-copy">下一步自行填写</span></div><div class="original-copy-note">新建任务没有旧文案来源</div>'
            : '<div class="original-config-row">文案<div class="original-segment" role="group" aria-label="文案处理"><button type="button" class="' + (item.copy === "rewrite" ? "on" : "") + '" data-original-copy="rewrite" data-original-index="' + index + '">AI 改写</button><button type="button" class="' + (item.copy === "keep" ? "on" : "") + '" data-original-copy="keep" data-original-index="' + index + '">' + keepCopyLabel + '</button></div></div><div class="original-copy-note">' + (item.copy === "keep" ? keepCopyNote : rewriteCopyNote) + '</div>')
          : '<div class="original-config-row">文案<span class="original-no-copy">画面上不放文字</span></div>';
        return '<article class="original-config">' +
          '<div class="original-config-head"><div class="original-config-title"><span class="original-config-name">' + escapeHtml(item.name) + '</span><span class="original-config-desc">' + escapeHtml(item.desc) + '</span></div>' + (item.pendingMaterial ? "" : '<button type="button" class="original-remove" data-original-remove="' + index + '" aria-label="移除' + escapeHtml(item.name) + '">×</button>') + '</div>' +
          '<div class="original-config-divider"></div>' + renderSubjectDrop(item, index, project) + '<div class="original-config-divider"></div><div class="original-config-label">参考图 <span>选填 · 最多一张</span><button type="button" class="original-reference-help" data-reference-help>使用说明</button></div>' +
          renderReferenceControl(item, index) +
          '<div class="original-reference-note">' + (item.ref ? (selectedReferenceAspects.length ? "已选择 " + selectedReferenceAspects.length + " 项，未选内容由系统设计" : "请选择要从这张图参考的内容") : "不添加参考图时，由系统完成视觉设计") + '</div>' + referenceBasis + copyControl + '</article>';
      }

      function renderOriginalSettings(project, isDetail) {
        var config = isDetail ? project.detail : project.main;
        var selectedItems = config.items.filter(function (item) { return item.on; });
        var hasPendingMaterial = selectedItems.some(function (item) { return item.pendingMaterial; });
        return '<div class="original-section-head"><div class="original-section-title">功能图片</div><div class="original-section-hint">' + (hasPendingMaterial ? "新商品素材已占据对应配置项，下一步确认商品主体" : "为每张功能图片拖入或选择商品主体图") + '</div><div class="original-section-count">' + (selectedItems.length ? "每套 " + selectedItems.length + " 张" : "还没选择功能图片") + '</div></div>' +
          (isDetail ? '<div class="original-option-row"><div class="original-option-label">详情尺寸</div><div class="original-option-items">' + renderOriginalSizes(detailSizes, config.size) + '</div></div>' : "") +
          '<div class="original-option-row"><div class="original-option-label">生成套数</div>' + renderSetCounts(config.setCount) + '</div>' +
          (isDetail ? '<div class="original-option-row"><div class="original-option-label">详情风格</div><div class="original-option-items">' + renderOriginalStyles(config.style) + '</div></div>' : "") +
          renderOriginalPicks(config.items, isDetail) +
          '<div class="original-configs">' + (selectedItems.length ? config.items.map(function (item, index) { return item.on ? renderOriginalConfig(item, index, project) : ""; }).join("") : '<div class="original-empty">选择上方任意一种功能图片，开始配置当前生成任务</div>') + '</div>';
      }

      function renderCopyConfirm(project, isDetail) {
        var config = isDetail ? project.detail : project.main;
        var copyItems = config.items.filter(function (item) { return item.on && item.copy; });
        var headlines = ["清透去油", "厨房净澈", "一抹洁净", "洁净焕新"];
        var subtitles = ["深入瓦解油污", "轻松清洁多区域", "泡沫绵密易冲洗", "日常清洁更省心"];
        var points = [
          ["强力去油", "清洁力强", "不伤厨具", "气味清新"],
          ["乳化油污", "洗完亮洁", "清洁彻底", "清新柠檬"],
          ["泡沫细腻", "轻松冲净", "适用多处", "洁净清爽"],
          ["快速瓦解", "一冲即净", "厨房适用", "清香不腻"]
        ];
        function sourceLabel(item) {
          if (state.copySource === "material") return item.copy === "keep" ? "使用素材原文" : "AI 改写文案";
          if (state.copySource === "history") return item.copy === "keep" ? "沿用所选成图文案" : "根据所选成图再次改写";
          return "自行填写文案";
        }
        function ensureDrafts(item) {
          var drafts = state.copyDrafts[item.id] || [];
          var confirmed = state.copyConfirmed[item.id] || [];
          while (drafts.length < config.setCount) {
            var index = drafts.length;
            var sourceIndex = item.copy === "keep" ? 0 : index % headlines.length;
            drafts.push({
              headline: state.copySource === "none" ? "" : headlines[sourceIndex],
              subtitle: state.copySource === "none" ? "" : subtitles[sourceIndex],
              sellingPoints: state.copySource === "none" ? [] : points[sourceIndex].slice()
            });
            confirmed.push(false);
          }
          state.copyDrafts[item.id] = drafts;
          state.copyConfirmed[item.id] = confirmed;
          return drafts;
        }
        function draftError(draft) {
          var badPunctuation = /[!-/:-@[-`{-~]/;
          if (!draft.headline.trim()) return "主标题不能空着";
          if (draft.headline.length > 8) return "主标题最多 8 个字";
          if (badPunctuation.test(draft.headline)) return "主标题不能用半角标点";
          if (!draft.subtitle.trim()) return "副标题不能空着";
          if (draft.subtitle.length > 8) return "副标题最多 8 个字";
          if (badPunctuation.test(draft.subtitle)) return "副标题不能用半角标点";
          for (var pointIndex = 0; pointIndex < draft.sellingPoints.length; pointIndex += 1) {
            var point = draft.sellingPoints[pointIndex];
            if (!point.trim()) return "第 " + (pointIndex + 1) + " 条卖点不能空着";
            if (point.length > 6) return "第 " + (pointIndex + 1) + " 条卖点最多 6 个字";
            if (badPunctuation.test(point)) return "第 " + (pointIndex + 1) + " 条卖点不能用半角标点";
            if (draft.sellingPoints.slice(0, pointIndex).some(function (earlier) { return earlier.trim() === point.trim(); })) return "卖点不能重复";
          }
          return "";
        }
        copyItems.forEach(ensureDrafts);
        var current = copyItems.find(function (item) { return item.id === state.copyFunctionId; }) || copyItems[0] || null;
        state.copyFunctionId = current ? current.id : null;
        var totalCopySets = copyItems.length * config.setCount;
        var confirmedCopySets = copyItems.reduce(function (total, item) {
          return total + state.copyConfirmed[item.id].slice(0, config.setCount).filter(Boolean).length;
        }, 0);
        var allConfirmed = totalCopySets === confirmedCopySets;
        var pendingCopyGroups = copyItems.map(function (item) {
          var setNumbers = state.copyConfirmed[item.id].slice(0, config.setCount).reduce(function (numbers, isConfirmed, index) {
            if (!isConfirmed) numbers.push(index + 1);
            return numbers;
          }, []);
          return { item: item, setNumbers: setNumbers };
        }).filter(function (group) { return group.setNumbers.length > 0; });
        var nextPendingCopy = pendingCopyGroups.length ? pendingCopyGroups[0] : null;
        var pendingCopyText = pendingCopyGroups.map(function (group) {
          return group.item.name + "：第 " + group.setNumbers.join("、") + " 套";
        }).join("；");
        var rail = copyItems.map(function (item) {
          var bound = projectSubjects(project).find(function (candidate) { return candidate.id === item.subjectId; });
          var count = state.copyConfirmed[item.id].slice(0, config.setCount).filter(Boolean).length;
          var functionState = count === config.setCount ? "已确认" : item.id === (current && current.id) ? "确认中" : "待确认";
          return '<button type="button" class="copy-function-button' + (current && item.id === current.id ? " current" : "") + '" data-copy-function="' + item.id + '">' + thumb(bound ? bound.thumb : project.thumb) + '<span><b>' + escapeHtml(item.name) + '</b><span>' + (bound ? escapeHtml(bound.name) : "新商品主体") + '</span><span class="copy-function-state' + (count === config.setCount ? " done" : "") + '">' + functionState + ' · ' + count + '/' + config.setCount + '</span></span></button>';
        }).join("");
        var subject = current ? projectSubjects(project).find(function (candidate) { return candidate.id === current.subjectId; }) : null;
        var sourceNote = current && current.copy === "keep"
          ? '<section class="copy-source-note" aria-label="素材原文说明"><strong>已填入素材原文</strong><span>主标题、副标题和卖点来自你上传的商品素材。系统按识别到的层级填入每一套。请检查识别结果，你可以分别修改。</span></section>'
          : '';
        var cards = current ? state.copyDrafts[current.id].slice(0, config.setCount).map(function (draft, index) {
          var confirmed = Boolean(state.copyConfirmed[current.id][index]);
          var error = draftError(draft);
          var sellingPoints = draft.sellingPoints.map(function (point, pointIndex) {
            return '<div class="copy-point-row"><button type="button" class="copy-point-remove" data-copy-remove-point="' + pointIndex + '" data-copy-set-index="' + index + '" aria-label="删除第 ' + (pointIndex + 1) + ' 条卖点">−</button><input value="' + escapeHtml(point) + '" data-copy-point="' + pointIndex + '" data-copy-set-index="' + index + '" aria-label="第 ' + (index + 1) + ' 套第 ' + (pointIndex + 1) + ' 条卖点"><span class="copy-point-count">' + point.length + '/6</span></div>';
          }).join("");
          return '<article class="copy-set-card' + (confirmed ? " confirmed" : "") + '"><header class="copy-set-head"><h3>第 ' + (index + 1) + ' 套文案</h3>' + (confirmed ? '<span class="copy-set-confirmed">已确认</span>' : "") + '</header><div class="copy-set-body"><div class="copy-field"><div class="copy-field-head"><label>主标题</label><span class="copy-field-count">' + draft.headline.length + '/8</span></div><input value="' + escapeHtml(draft.headline) + '" data-copy-field="headline" data-copy-set-index="' + index + '" aria-label="第 ' + (index + 1) + ' 套主标题"></div><div class="copy-field"><div class="copy-field-head"><label>副标题</label><span class="copy-field-count">' + draft.subtitle.length + '/8</span></div><input value="' + escapeHtml(draft.subtitle) + '" data-copy-field="subtitle" data-copy-set-index="' + index + '" aria-label="第 ' + (index + 1) + ' 套副标题"></div><div class="copy-field"><div class="copy-field-head"><label>卖点</label><span class="copy-field-count">' + draft.sellingPoints.length + '/8</span></div><div class="copy-point-list">' + sellingPoints + '</div><button type="button" class="copy-add-point" data-copy-add-point data-copy-set-index="' + index + '"' + (draft.sellingPoints.length >= 8 ? " disabled" : "") + '>＋ 加一条卖点</button></div></div>' + (error ? '<p class="copy-card-error" role="alert">' + escapeHtml(error) + '</p>' : "") + '<footer class="copy-set-foot"><button type="button" class="copy-set-confirm" data-copy-confirm-set="' + index + '"' + (error ? " disabled" : "") + '>' + (confirmed ? "已确认，可继续修改" : "确认这套") + '</button></footer></article>';
        }).join("") : '<div class="copy-empty"><strong>当前任务不需要文案</strong><p>所选功能图片不会在画面上放置文字。</p></div>';
        var copyFlowStatus = allConfirmed
          ? '<div class="copy-flow-status ready" role="status"><strong>所有文案已确认</strong><span>可以进入提交确认。</span></div>'
          : '<div class="copy-flow-status" role="status"><strong>还有 ' + (totalCopySets - confirmedCopySets) + ' 套文案未确认</strong><span>' + escapeHtml(pendingCopyText) + '</span></div>';
        var copyFlowAction = allConfirmed
          ? '<button class="btn primary" type="button" id="submit-confirmed-copy">进入提交确认</button>'
          : '<button class="btn primary" type="button" id="next-unconfirmed-copy" data-copy-function="' + escapeHtml(nextPendingCopy.item.id) + '" data-copy-set-index="' + (nextPendingCopy.setNumbers[0] - 1) + '">查看下一套</button>';
        var copyReturnLabel = state.copyReturnTarget === "subject" ? "返回商品主体确认" : "返回设置";
        return '<section class="copy-flow" aria-label="文案确认"><div class="copy-flow-body"><aside class="copy-flow-rail"><header class="copy-flow-rail-head"><strong>功能图片</strong><span>' + confirmedCopySets + ' / ' + totalCopySets + '</span></header><div class="copy-flow-rail-list">' + rail + '</div><div class="copy-flow-rail-foot">每张带文案的功能图片都有 ' + config.setCount + ' 套文案。逐套确认后开始生成。</div></aside><main class="copy-flow-work"><header class="copy-flow-work-head">' + (current ? thumb(subject ? subject.thumb : project.thumb) + '<strong>' + escapeHtml(current.name) + '</strong><span>' + (subject ? escapeHtml(subject.name) : "新商品主体") + '</span><span>每套一份文案</span><span class="copy-source-badge">' + sourceLabel(current) + '</span>' : '<strong>文案确认</strong>') + '</header><div class="copy-set-grid' + (config.setCount === 1 ? ' single' : '') + '">' + sourceNote + cards + '</div><footer class="copy-flow-foot">' + copyFlowStatus + '<button class="btn danger-quiet" type="button" id="abandon-task">放弃这次任务</button><button class="btn" type="button" id="back-from-copy">' + copyReturnLabel + '</button>' + copyFlowAction + '</footer></main></div></section>';
      }

      function renderCopyDrafting(project, isDetail) {
        var config = isDetail ? project.detail : project.main;
        var copyItems = config.items.filter(function (item) { return item.on && item.copy === "rewrite"; });
        var current = copyItems[0] || null;
        var currentSet = Math.min(2, config.setCount);
        var completedSets = Math.max(0, currentSet - 1);
        var subject = current ? projectSubjects(project).find(function (candidate) { return candidate.id === current.subjectId; }) : null;
        var failed = state.copyDraftingFailed;
        var rail = current
          ? '<div class="copy-drafting-function current">' + thumb(subject ? subject.thumb : project.thumb) + '<span><b>' + escapeHtml(current.name) + '</b><span>' + (subject ? escapeHtml(subject.name) : "新商品主体") + '</span><span class="copy-drafting-function-state">' + (failed ? "草拟失败" : "草拟中 · " + completedSets + "/" + config.setCount) + '</span></span></div>'
          : '';
        return '<section class="copy-drafting' + (failed ? ' failed' : '') + '" aria-label="' + (failed ? '文案草拟失败' : '文案草拟中') + '"><div class="copy-drafting-layout"><aside class="copy-drafting-rail"><header class="copy-drafting-rail-head"><strong>功能图片</strong><span>' + copyItems.length + ' 项</span></header><div class="copy-drafting-rail-list">' + rail + '</div><p class="copy-drafting-rail-foot">' + (failed ? "商品素材、商品主体图和生成任务设置已保留。" : "每张选择 AI 改写的功能图片，会按生成套数草拟文案。全部完成后进入文案确认。") + '</p></aside><main class="copy-drafting-stage"><header class="copy-drafting-stage-head"><strong>文案草拟</strong><span>' + (failed ? "草拟失败" : "进度 " + currentSet + " / " + config.setCount) + '</span></header><div class="copy-drafting-status" role="status" aria-live="polite"><div class="copy-drafting-preview">' + thumb(subject ? subject.thumb : project.thumb) + '<span class="copy-drafting-spinner" aria-hidden="true"></span></div><h1>' + (failed ? "这项文案暂时无法草拟" : "正在草拟第 " + currentSet + " 套文案") + '</h1><p>' + (current ? escapeHtml(current.name) : "当前功能图片") + ' · ' + (subject ? escapeHtml(subject.name) : "新商品主体") + '</p>' + (failed ? '' : '<div class="copy-drafting-progress" role="progressbar" aria-label="文案草拟进度" aria-valuemin="0" aria-valuemax="' + config.setCount + '" aria-valuenow="' + completedSets + '" aria-valuetext="正在草拟第 ' + currentSet + ' 套，共 ' + config.setCount + ' 套"><span></span></div>') + '<small>' + (failed ? "你可以重新草拟，或者保留当前设置并改为空白填写。" : "第 " + currentSet + " 套完成后，系统会继续草拟剩余文案。") + '</small>' + (failed ? '<div class="copy-drafting-actions"><button class="btn primary" type="button" id="retry-copy-drafting">重新草拟</button><button class="btn" type="button" id="use-blank-copy">改为空白填写</button></div>' : '') + '</div></main></div></section>';
      }

      function bindCopyDraftingControls(project, isDetail) {
        var retry = document.getElementById("retry-copy-drafting");
        var useBlank = document.getElementById("use-blank-copy");
        if (retry) {
          retry.addEventListener("click", function () {
            state.copyDraftingFailed = false;
            navNote.textContent = "正在重新草拟文案";
            renderWorkbench();
          });
        }
        if (useBlank) {
          useBlank.addEventListener("click", function () {
            var config = isDetail ? project.detail : project.main;
            var current = config.items.find(function (item) { return item.on && item.copy === "rewrite"; });
            state.copySource = "none";
            state.copyFunctionId = current ? current.id : null;
            state.copyDrafts = {};
            state.copyConfirmed = {};
            state.workbenchMode = "copy-confirm";
            navNote.textContent = "请填写并确认每套文案";
            renderWorkbench();
          });
        }
      }

      function bindCopyConfirmControls(project, isDetail) {
        var config = isDetail ? project.detail : project.main;
        bindTaskAbandonControl(project, isDetail, config);
        Array.prototype.forEach.call(view.querySelectorAll("[data-copy-function]"), function (button) {
          button.addEventListener("click", function () {
            state.copyFunctionId = button.getAttribute("data-copy-function");
            renderWorkbench();
          });
        });
        Array.prototype.forEach.call(view.querySelectorAll("[data-copy-field]"), function (input) {
          input.addEventListener("input", function () {
            var setIndex = Number(input.getAttribute("data-copy-set-index"));
            state.copyDrafts[state.copyFunctionId][setIndex][input.getAttribute("data-copy-field")] = input.value;
            state.copyConfirmed[state.copyFunctionId][setIndex] = false;
          });
          input.addEventListener("change", renderWorkbench);
        });
        Array.prototype.forEach.call(view.querySelectorAll("[data-copy-point]"), function (input) {
          input.addEventListener("input", function () {
            var setIndex = Number(input.getAttribute("data-copy-set-index"));
            var pointIndex = Number(input.getAttribute("data-copy-point"));
            state.copyDrafts[state.copyFunctionId][setIndex].sellingPoints[pointIndex] = input.value;
            state.copyConfirmed[state.copyFunctionId][setIndex] = false;
          });
          input.addEventListener("change", renderWorkbench);
        });
        Array.prototype.forEach.call(view.querySelectorAll("[data-copy-remove-point]"), function (button) {
          button.addEventListener("click", function () {
            var setIndex = Number(button.getAttribute("data-copy-set-index"));
            var pointIndex = Number(button.getAttribute("data-copy-remove-point"));
            state.copyDrafts[state.copyFunctionId][setIndex].sellingPoints.splice(pointIndex, 1);
            state.copyConfirmed[state.copyFunctionId][setIndex] = false;
            renderWorkbench();
          });
        });
        Array.prototype.forEach.call(view.querySelectorAll("[data-copy-add-point]"), function (button) {
          button.addEventListener("click", function () {
            var setIndex = Number(button.getAttribute("data-copy-set-index"));
            state.copyDrafts[state.copyFunctionId][setIndex].sellingPoints.push("");
            state.copyConfirmed[state.copyFunctionId][setIndex] = false;
            renderWorkbench();
          });
        });
        Array.prototype.forEach.call(view.querySelectorAll("[data-copy-confirm-set]"), function (button) {
          button.addEventListener("click", function () {
            var setIndex = Number(button.getAttribute("data-copy-confirm-set"));
            state.copyConfirmed[state.copyFunctionId][setIndex] = !state.copyConfirmed[state.copyFunctionId][setIndex];
            renderWorkbench();
          });
        });
        document.getElementById("back-from-copy").addEventListener("click", function () {
          if (state.copyReturnTarget === "subject") {
            var subjectParams = new URLSearchParams({
              project: project.id,
              name: project.name,
              flow: "confirm-material",
              analysisComplete: "1",
              materialFunction: materialFunction,
              setCount: String(config.setCount),
              scenario: "copy-back-subject"
            });
            if (requestedCopyTreatment) subjectParams.set("copyTreatment", requestedCopyTreatment);
            if (requestedReferenceAdded) {
              subjectParams.set("referenceAdded", "1");
              subjectParams.set("referenceAspects", requestedReferenceAspects.join(","));
            }
            window.location.href = "index.html?" + subjectParams.toString();
            return;
          }
          openTaskAbandonDialog(project, isDetail, config, "return-to-settings");
        });
        var nextUnconfirmedCopy = document.getElementById("next-unconfirmed-copy");
        if (nextUnconfirmedCopy) {
          nextUnconfirmedCopy.addEventListener("click", function () {
            var setIndex = Number(nextUnconfirmedCopy.getAttribute("data-copy-set-index"));
            state.copyFunctionId = nextUnconfirmedCopy.getAttribute("data-copy-function");
            renderWorkbench();
            var pendingCard = view.querySelectorAll(".copy-set-card")[setIndex];
            if (pendingCard) {
              pendingCard.scrollIntoView({ block: "nearest" });
              var firstField = pendingCard.querySelector("input");
              if (firstField) firstField.focus();
            }
          });
        }
        var submitConfirmedCopy = document.getElementById("submit-confirmed-copy");
        if (submitConfirmedCopy) submitConfirmedCopy.addEventListener("click", function () {
          openSecondGate(project, isDetail, config);
        });
      }

      function captureWorkbenchInteraction() {
        var active = document.activeElement;
        var snapshot = {
          viewScrollTop: view.scrollTop,
          settingsScrollTop: view.querySelector(".settings-scroll") ? view.querySelector(".settings-scroll").scrollTop : 0,
          copyGridScrollTop: view.querySelector(".copy-set-grid") ? view.querySelector(".copy-set-grid").scrollTop : 0,
          selector: "",
          selectionStart: null,
          selectionEnd: null
        };
        if (!active || !view.contains(active)) return snapshot;
        if (active.matches("[data-copy-field]")) {
          snapshot.selector = '[data-copy-field="' + active.getAttribute("data-copy-field") + '"][data-copy-set-index="' + active.getAttribute("data-copy-set-index") + '"]';
        } else if (active.matches("[data-copy-point]")) {
          snapshot.selector = '[data-copy-point="' + active.getAttribute("data-copy-point") + '"][data-copy-set-index="' + active.getAttribute("data-copy-set-index") + '"]';
        } else if (active.matches("[data-subject-select]")) {
          snapshot.selector = '[data-subject-select="' + active.getAttribute("data-subject-select") + '"]';
        }
        if (snapshot.selector && typeof active.selectionStart === "number") {
          snapshot.selectionStart = active.selectionStart;
          snapshot.selectionEnd = active.selectionEnd;
        }
        return snapshot;
      }

      function restoreWorkbenchInteraction(snapshot) {
        if (!snapshot) return;
        view.scrollTop = snapshot.viewScrollTop;
        var settingsScroll = view.querySelector(".settings-scroll");
        var copyGrid = view.querySelector(".copy-set-grid");
        if (settingsScroll) settingsScroll.scrollTop = snapshot.settingsScrollTop;
        if (copyGrid) copyGrid.scrollTop = snapshot.copyGridScrollTop;
        if (!snapshot.selector) return;
        var target = view.querySelector(snapshot.selector);
        if (!target) return;
        target.focus({ preventScroll: true });
        if (snapshot.selectionStart !== null && typeof target.setSelectionRange === "function") {
          var end = Math.min(snapshot.selectionEnd, target.value.length);
          target.setSelectionRange(Math.min(snapshot.selectionStart, end), end);
        }
      }

      function renderWorkbench() {
        var interactionSnapshot = captureWorkbenchInteraction();
        var p = projects[state.projectIndex];
        var isDetail = state.tab === "detail";
        var config = isDetail ? p.detail : p.main;
        var imagesPerSet = config.items.filter(function (item) { return item.on; }).length;
        var imageCount = imagesPerSet * config.setCount;
        var maxCredits = imageCount * mainImageUnitPrice;
        var hasMissingSubject = config.items.some(function (item) { return item.on && !item.subjectId && !item.pendingMaterial; });
        var hasIncompleteReference = config.items.some(function (item) { return item.on && item.ref && (!item.referenceAspects || !item.referenceAspects.length); });
        var cannotSubmit = imagesPerSet === 0 || hasMissingSubject || hasIncompleteReference;
        var tasks = taskQueueData(p);
        var selectedTask = tasks.find(function (task) { return task.taskId === state.selectedTaskId; });
        var isTaskDetail = state.workbenchMode === "task-detail" && selectedTask;
        var isCopyConfirm = state.workbenchMode === "copy-confirm";
        var isCopyDrafting = state.workbenchMode === "copy-drafting";
        var appShell = document.querySelector(".app");
        appShell.classList.toggle("copy-flow-mode", isCopyConfirm || isCopyDrafting);
        var settingsBody = isTaskDetail
          ? renderTaskDetail(p, selectedTask)
          : isCopyDrafting ? renderCopyDrafting(p, isDetail) : isCopyConfirm ? renderCopyConfirm(p, isDetail) : renderContinueSource() + renderOriginalSettings(p, isDetail);
        if (isCopyDrafting) {
          view.innerHTML = settingsBody;
          bindCopyDraftingControls(p, isDetail);
          applyServiceGateToControls();
          restoreWorkbenchInteraction(interactionSnapshot);
          return;
        }
        if (isCopyConfirm) {
          view.innerHTML = settingsBody;
          bindCopyConfirmControls(p, isDetail);
          applyServiceGateToControls();
          restoreWorkbenchInteraction(interactionSnapshot);
          return;
        }
        var hasPendingMaterial = config.items.some(function (item) { return item.on && item.pendingMaterial; });
        var settingsFooter = isTaskDetail
          ? ""
          : '<footer class="settings-foot"><div class="foot-copy"><div class="foot-summary"><b>' + config.setCount + ' 套 × 每套 ' + imagesPerSet + ' 张功能图片，共 ' + imageCount + ' 张成图</b><span class="foot-max-credit">最多 ' + maxCredits.toLocaleString("zh-CN") + ' 鸭豆</span></div><span>' + (imagesPerSet === 0 ? "请选择至少一种要新增的功能图片。" : hasMissingSubject ? "请为每张功能图片选择一张商品主体图。" : hasIncompleteReference ? "请为已上传的参考图选择至少一项视觉依据。" : hasPendingMaterial ? "下一步统一识别文案并确认商品主体。" : "下一步确认当前任务的文案。") + '</span></div><button class="btn danger-quiet" type="button" id="abandon-task">放弃这次任务</button><button class="btn primary" type="button" id="begin-task"' + (cannotSubmit ? " disabled" : "") + '>下一步</button></footer>';

        view.innerHTML =
          '<section class="workbench" aria-label="' + (isDetail ? "商品详情图" : "商品主图") + '工作台">' +
            '<div class="work-grid">' +
              '<aside class="project-queue" aria-label="商品任务队列">' +
                '<div class="panel-title"><h2>商品任务队列</h2><span>' + tasks.length + ' 个任务</span></div>' +
                '<div class="queue-note">当前任务和历史任务都保存在这里。未使用参考图的已交付图片可以继续生成。</div>' +
                '<button type="button" class="new-project" id="new-task"><span class="new-project-mark" aria-hidden="true">＋</span><span><b>新建生成任务</b><small>为各功能图片选择商品主体图</small></span></button>' +
                '<div class="queue-list">' + taskQueueItems(p) + '</div>' +
                '<div class="queue-foot">任务按最新时间排列。选择任务，可以查看每张已交付图片。</div>' +
              '</aside>' +
              '<section class="settings' + (isTaskDetail ? " task-detail-mode" : "") + '" aria-label="当前生成任务设置">' +
                '<div class="settings-scroll">' + settingsBody + '</div>' + settingsFooter +
              '</section>' +
            '</div>' +
          '</section>';

        if (!isTaskDetail) {
          bindOriginalControls(p, isDetail);
          bindTaskAbandonControl(p, isDetail, config);
        }
        document.getElementById("new-task").addEventListener("click", function () {
          if (blockNewGeneration()) return;
          if (openBillingDebtGate()) return;
          if (hasDraftSettings(config)) {
            openDraftReplaceDialog(p, isDetail, config);
            return;
          }
          resetDraftSettings(p, isDetail, config);
        });
        var beginTask = document.getElementById("begin-task");
        if (beginTask) beginTask.addEventListener("click", function () {
          if (blockNewGeneration()) return;
          if (openBillingDebtGate()) return;
          openFirstGate(p, isDetail, config);
        });
        Array.prototype.forEach.call(view.querySelectorAll("[data-task-output-preview]"), function (button) {
          button.addEventListener("click", function () {
            var task = taskQueueData(p).find(function (item) { return item.taskId === state.selectedTaskId; });
            var source = taskOutputs(p, task).find(function (output) { return output.id === button.getAttribute("data-task-output-preview"); });
            if (source) openTaskPreview(source);
          });
        });
        Array.prototype.forEach.call(view.querySelectorAll("[data-task-output-export]"), function (button) {
          button.addEventListener("click", function () {
            var task = taskQueueData(p).find(function (item) { return item.taskId === state.selectedTaskId; });
            var source = taskOutputs(p, task).find(function (output) { return output.id === button.getAttribute("data-task-output-export"); });
            if (source) openTaskExport(source);
          });
        });
        Array.prototype.forEach.call(view.querySelectorAll("[data-task-output-continue]"), function (button) {
          button.addEventListener("click", function () {
            if (blockNewGeneration()) return;
            if (openBillingDebtGate()) return;
            var task = taskQueueData(p).find(function (item) { return item.taskId === state.selectedTaskId; });
            var source = taskOutputs(p, task).find(function (output) { return output.id === button.getAttribute("data-task-output-continue"); });
            continueFromTaskOutput(p, source);
          });
        });
        var restartTask = view.querySelector("[data-restart-task]");
        if (restartTask) restartTask.addEventListener("click", function () {
          if (blockNewGeneration()) return;
          if (openBillingDebtGate()) return;
          var failedTask = taskQueueData(p).find(function (item) { return item.taskId === state.selectedTaskId; });
          if (!failedTask) return;
          openSecondGateForRestart(p, failedTask);
        });
        Array.prototype.forEach.call(view.querySelectorAll("[data-task-id]"), function (button) {
          button.addEventListener("click", function () {
            var taskId = button.getAttribute("data-task-id");
            var task = taskQueueData(p).find(function (item) { return item.taskId === taskId; });
            state.selectedTaskId = taskId;
            clearSubmissionNotice();
            state.continueSource = null;
            state.workbenchMode = "task-detail";
            navNote.textContent = task && task.state === "ready" ? "已交付图片可以查看和导出；未使用参考图的图片可以继续生成" : task && task.state === "partial" ? "已交付图片仍然保留，未完成图片的额度已经释放" : task && task.state === "failed" ? "任务已停止，未交付图片的额度已经释放" : task && task.state === "wait" ? "该任务排队中，轮到它时自动开始" : "该任务正在生成中";
            renderWorkbench();
          });
        });
        applyServiceGateToControls();
        restoreWorkbenchInteraction(interactionSnapshot);
      }

      function bindOriginalControls(project, isDetail) {
        var config = isDetail ? project.detail : project.main;
        Array.prototype.forEach.call(view.querySelectorAll("[data-original-size]"), function (button) {
          button.addEventListener("click", function () {
            config.size = button.getAttribute("data-original-size");
            renderWorkbench();
          });
        });
        Array.prototype.forEach.call(view.querySelectorAll("[data-original-style]"), function (button) {
          button.addEventListener("click", function () {
            config.style = button.getAttribute("data-original-style");
            renderWorkbench();
          });
        });
        Array.prototype.forEach.call(view.querySelectorAll("[data-original-pick]"), function (button) {
          button.addEventListener("click", function () {
            var item = config.items[Number(button.getAttribute("data-original-pick"))];
            item.on = !item.on;
            if (item.on && state.workbenchMode === "continue-edit" && state.continueSource && !item.subjectId) item.subjectId = state.continueSource.subjectId;
            renderWorkbench();
          });
        });
        Array.prototype.forEach.call(view.querySelectorAll("[data-subject-drop]"), function (dropZone) {
          dropZone.addEventListener("dragenter", function (event) {
            event.preventDefault();
            dropZone.classList.add("is-over");
          });
          dropZone.addEventListener("dragover", function (event) {
            event.preventDefault();
            event.dataTransfer.dropEffect = "copy";
          });
          dropZone.addEventListener("dragleave", function (event) {
            if (!dropZone.contains(event.relatedTarget)) dropZone.classList.remove("is-over");
          });
          dropZone.addEventListener("drop", function (event) {
            event.preventDefault();
            var subjectId = event.dataTransfer.getData("text/product-subject-id");
            var subject = projectSubjects(project).find(function (candidate) { return candidate.id === subjectId; });
            if (!subject) return;
            config.items[Number(dropZone.getAttribute("data-subject-drop"))].subjectId = subject.id;
            navNote.textContent = subject.name + "已用于当前功能图片";
            renderWorkbench();
          });
        });
        Array.prototype.forEach.call(view.querySelectorAll("[data-subject-select]"), function (select) {
          select.addEventListener("change", function () {
            var subject = projectSubjects(project).find(function (candidate) { return candidate.id === select.value; });
            var item = config.items[Number(select.getAttribute("data-subject-select"))];
            item.subjectId = subject ? subject.id : null;
            navNote.textContent = subject ? subject.name + "已用于当前功能图片" : "已清除当前功能图片的商品主体图";
            renderWorkbench();
          });
        });
        Array.prototype.forEach.call(view.querySelectorAll("[data-original-remove]"), function (button) {
          button.addEventListener("click", function () {
            config.items[Number(button.getAttribute("data-original-remove"))].on = false;
            renderWorkbench();
          });
        });
        Array.prototype.forEach.call(view.querySelectorAll("[data-original-reference-add]"), function (button) {
          button.addEventListener("click", function () {
            var item = config.items[Number(button.getAttribute("data-original-reference-add"))];
            item.ref = true;
            item.referenceName = item.name + "_参考图.jpg";
            navNote.textContent = "已为" + item.name + "添加参考图";
            renderWorkbench();
          });
        });
        Array.prototype.forEach.call(view.querySelectorAll("[data-original-reference-replace]"), function (button) {
          button.addEventListener("click", function () {
            var item = config.items[Number(button.getAttribute("data-original-reference-replace"))];
            item.referenceName = item.name + "_新参考图.jpg";
            navNote.textContent = item.name + "的参考图已更换";
            renderWorkbench();
          });
        });
        Array.prototype.forEach.call(view.querySelectorAll("[data-original-reference-remove]"), function (button) {
          button.addEventListener("click", function () {
            var item = config.items[Number(button.getAttribute("data-original-reference-remove"))];
            item.ref = false;
            item.referenceName = "";
            item.referenceAspects = [];
            navNote.textContent = item.name + "的参考图已移除";
            renderWorkbench();
          });
        });
        Array.prototype.forEach.call(view.querySelectorAll("[data-reference-help]"), function (button) {
          button.addEventListener("click", function () {
            openModal(referenceBoundaryDialog, closeReferenceBoundary);
          });
        });
        Array.prototype.forEach.call(view.querySelectorAll("[data-reference-aspect]"), function (checkbox) {
          checkbox.addEventListener("change", function () {
            var item = config.items[Number(checkbox.getAttribute("data-original-index"))];
            var aspect = checkbox.getAttribute("data-reference-aspect");
            var aspects = item.referenceAspects || [];
            if (checkbox.checked && aspects.indexOf(aspect) < 0) aspects.push(aspect);
            if (!checkbox.checked) aspects = aspects.filter(function (value) { return value !== aspect; });
            item.referenceAspects = aspects;
            renderWorkbench();
          });
        });
        Array.prototype.forEach.call(view.querySelectorAll("[data-original-copy]"), function (button) {
          button.addEventListener("click", function () {
            config.items[Number(button.getAttribute("data-original-index"))].copy = button.getAttribute("data-original-copy");
            renderWorkbench();
          });
        });
        Array.prototype.forEach.call(view.querySelectorAll("[data-set-count]"), function (button) {
          button.addEventListener("click", function () {
            config.setCount = Number(button.getAttribute("data-set-count"));
            renderWorkbench();
          });
        });
      }

      function switchTab(tab) {
        if (tab !== state.tab) flushDraftSave();
        state.tab = tab;
        if (state.workbenchMode === "task-detail") {
          state.workbenchMode = "edit";
          state.selectedTaskId = null;
        }
        tabs.forEach(function (button) {
          var selected = button.getAttribute("data-tab") === tab;
          button.setAttribute("aria-selected", String(selected));
          button.setAttribute("tabindex", selected ? "0" : "-1");
          button.setAttribute("aria-controls", "view");
        });
        navNote.textContent = "从上方拖入商品主体图，或在功能图片中直接选择";
        renderWorkbench();
        window.requestAnimationFrame(function () {
          var selectedTab = tabs.find(function (button) { return button.getAttribute("data-tab") === tab; });
          if (selectedTab) selectedTab.focus({ preventScroll: true });
        });
      }

      tabs.forEach(function (button) {
        button.addEventListener("click", function () {
          if (button.disabled) return;
          switchTab(button.getAttribute("data-tab"));
        });
        button.addEventListener("keydown", function (event) {
          if (["ArrowLeft", "ArrowRight", "Home", "End"].indexOf(event.key) < 0) return;
          event.preventDefault();
          var enabledTabs = tabs.filter(function (tabButton) { return !tabButton.disabled; });
          var index = enabledTabs.indexOf(button);
          var next = event.key === "Home" ? 0 : event.key === "End" ? enabledTabs.length - 1 : event.key === "ArrowRight" ? (index + 1) % enabledTabs.length : (index - 1 + enabledTabs.length) % enabledTabs.length;
          switchTab(enabledTabs[next].getAttribute("data-tab"));
        });
      });

      var requestedProjectIndex = projects.findIndex(function (project) { return project.id === requestedProjectId; });
      if (requestedProjectIndex >= 0) state.projectIndex = requestedProjectIndex;
      var activeProject = projects[state.projectIndex];
      if (materialAdded) {
        activeProject.originalSubjectCount = activeProject.subjectCount;
        activeProject.hasAddedSubject = true;
        activeProject.subjectCount += 1;
      }
      if (isNewMaterialFlow || isCopyConfirmFlow) {
        activeProject.main.items.forEach(function (item) {
          item.on = false;
          item.pendingMaterial = false;
          item.subjectId = null;
        });
        var materialItem = activeProject.main.items.find(function (item) { return item.id === materialFunction; }) || activeProject.main.items[0];
        materialItem.on = true;
        materialItem.pendingMaterial = isNewMaterialFlow;
        materialItem.subjectId = isCopyConfirmFlow ? "added" : null;
        if (requestedSetCount) activeProject.main.setCount = requestedSetCount;
        if (requestedCopyTreatment && materialItem.copy) materialItem.copy = requestedCopyTreatment;
        materialItem.ref = requestedReferenceAdded;
        materialItem.referenceAspects = requestedReferenceAdded ? requestedReferenceAspects.slice() : [];
        state.copySource = "material";
        state.workbenchMode = ["copy-drafting", "copy-drafting-failed"].indexOf(requestedScenario) >= 0 ? "copy-drafting" : isCopyConfirmFlow ? "copy-confirm" : "edit";
      }
      if (["gate-one-sufficient", "gate-one-insufficient", "gate-one-confirmed", "gate-one-return-blocked", "main-setup-ready"].indexOf(requestedScenario) >= 0) {
        activeProject.main.items.forEach(function (item) {
          item.on = false;
          item.subjectId = null;
        });
        activeProject.main.items[0].on = true;
        activeProject.main.items[0].subjectId = "front";
        activeProject.main.items[3].on = true;
        activeProject.main.items[3].subjectId = activeProject.subjectCount > 1 ? "side" : "front";
        activeProject.main.setCount = 2;
      }
      if (requestedScenario === "copy-unconfirmed" || requestedScenario === "ux-copy-live-update") {
        activeProject.main.items.forEach(function (item) {
          item.on = false;
          item.subjectId = null;
        });
        activeProject.main.items[0].on = true;
        activeProject.main.items[0].subjectId = "front";
        activeProject.main.items[1].on = true;
        activeProject.main.items[1].subjectId = activeProject.subjectCount > 1 ? "side" : "front";
        activeProject.main.setCount = requestedScenario === "ux-copy-live-update" ? 4 : 2;
        state.copySource = "material";
        state.copyFunctionId = activeProject.main.items[0].id;
        state.copyConfirmed[activeProject.main.items[0].id] = [true, false];
        state.copyConfirmed[activeProject.main.items[1].id] = [false, false];
        state.workbenchMode = "copy-confirm";
        state.firstGateConfirmed = true;
      }
      if (requestedScenario === "copy-ready" || isGateTwoScenario) {
        activeProject.main.items.forEach(function (item) {
          item.on = false;
          item.subjectId = null;
        });
        activeProject.main.items[0].on = true;
        activeProject.main.items[0].subjectId = materialAdded ? "added" : "front";
        activeProject.main.setCount = 2;
        state.copySource = "material";
        state.copyFunctionId = activeProject.main.items[0].id;
        state.copyConfirmed[activeProject.main.items[0].id] = [true, true];
        state.workbenchMode = "copy-confirm";
        state.firstGateConfirmed = true;
      }
      if (requestedScenario === "gate-one-insufficient") {
        walletBalance = 80;
        walletBalanceLabel.textContent = walletBalance.toLocaleString("zh-CN");
      }
      if (["library-draft-saved", "library-draft-replace", "library-abandon-existing"].indexOf(requestedScenario) >= 0) {
        activeProject.main.items.forEach(function (item) {
          item.on = false;
          item.subjectId = null;
        });
        activeProject.main.items[0].on = true;
        activeProject.main.items[0].subjectId = "front";
        activeProject.main.items[3].on = true;
        activeProject.main.items[3].subjectId = activeProject.subjectCount > 1 ? "side" : "front";
        activeProject.main.setCount = 2;
      }
      if (requestedScenario === "main-setup-reference") {
        activeProject.main.items.forEach(function (item) {
          item.on = false;
          item.subjectId = null;
          item.ref = false;
          item.referenceName = "";
          item.referenceAspects = [];
        });
        activeProject.main.items[0].on = true;
        activeProject.main.items[0].subjectId = "front";
        activeProject.main.setCount = 1;
      }
      if (["main-setup-reference-required", "main-setup-reference-boundary"].indexOf(requestedScenario) >= 0) {
        activeProject.main.items.forEach(function (item) {
          item.on = false;
          item.subjectId = null;
          item.ref = false;
          item.referenceName = "";
          item.referenceAspects = [];
        });
        activeProject.main.items[0].on = true;
        activeProject.main.items[0].subjectId = "front";
        activeProject.main.items[0].ref = true;
        activeProject.main.items[0].referenceName = "营销图_参考图.jpg";
        activeProject.main.setCount = 1;
      }
      if (requestedScenario === "main-setup-autosave") {
        activeProject.main.items.forEach(function (item) {
          item.on = false;
          item.subjectId = null;
        });
        activeProject.main.items[0].on = true;
        activeProject.main.items[0].subjectId = "front";
        activeProject.main.setCount = 2;
      }
      document.getElementById("active-project-name").textContent = activeProject.name;
      document.getElementById("active-project-id").textContent = activeProject.id;
      document.getElementById("delete-project").addEventListener("click", function () {
        openProjectDeleteDialog(activeProject);
      });
      renderSubjectPicker(activeProject);
      switchTab("main");
      if (safetyFailureScenarios.indexOf(requestedScenario) >= 0) {
        state.workbenchMode = "task-detail";
        state.selectedTaskId = "failed-main";
        navNote.textContent = "任务已经失败，失败原因和额度释放结果保留在时间线中";
        renderWorkbench();
      }
      if (serviceFailureScenarios.indexOf(requestedScenario) >= 0) {
        state.workbenchMode = "task-detail";
        state.selectedTaskId = "failed-main";
        navNote.textContent = "原失败任务和原结算保持不变；重新发起会建立新任务";
        renderWorkbench();
        if (requestedScenario === "reentry-same-settings-confirm") {
          openSecondGateForRestart(activeProject, taskQueueData(activeProject).find(function (task) { return task.taskId === "failed-main"; }));
        }
      }
      if (["recovery-task-running", "recovery-task-partial", "recovery-task-failed", "billing-settlement-pending"].indexOf(requestedScenario) >= 0) {
        state.workbenchMode = "task-detail";
        state.selectedTaskId = requestedScenario === "recovery-task-running"
          ? "running-main"
          : requestedScenario === "recovery-task-partial"
            ? "partial-main"
            : requestedScenario === "recovery-task-failed"
              ? "failed-main"
              : "completed-main";
        navNote.textContent = requestedScenario === "billing-settlement-pending"
          ? "图片已经交付，结算会在网络恢复后自动处理"
          : "应用重启后继续显示原任务的普通进度或终态";
        renderWorkbench();
      }
      if (requestedScenario === "billing-debt-gate") {
        navNote.textContent = "Gateway 已明确返回余额不足，新的生成入口暂时不可用";
        openBillingDebtGate();
      }
      if (["copy-drafting", "copy-drafting-failed"].indexOf(requestedScenario) >= 0) {
        navNote.textContent = requestedScenario === "copy-drafting-failed" ? "文案草拟失败，设置已保留" : "文案草拟完成后进入文案确认";
      }
      if (requestedScenario === "copy-unconfirmed") {
        navNote.textContent = "请完成剩余文案确认";
      }
      if (requestedScenario === "copy-back-subject") {
        navNote.textContent = "可以返回修改商品主体确认结果";
      }
      if (requestedScenario === "copy-ready" || isGateTwoScenario) {
        navNote.textContent = "全部文案已确认，可以进入提交确认";
      }
      if (["gate-two-open", "gate-two-settlement-rule", "gate-two-lock-rule", "gate-two-actions"].indexOf(requestedScenario) >= 0) {
        openSecondGate(activeProject, false, activeProject.main, "confirm");
      }
      if (requestedScenario === "gate-two-submitting") {
        openSecondGate(activeProject, false, activeProject.main, "confirming");
      }
      if (requestedScenario === "gate-two-rejected") {
        walletBalance = 20;
        walletBalanceLabel.textContent = walletBalance.toLocaleString("zh-CN");
        openSecondGate(activeProject, false, activeProject.main, "rejected");
      }
      if (requestedScenario === "gate-two-unknown") {
        openSecondGate(activeProject, false, activeProject.main, "confirming");
      }
      if (requestedScenario === "gate-two-duplicate" || requestedScenario === "gate-two-accepted") {
        var gateTwoItems = activeProject.main.items.filter(function (item) { return item.on; });
        finishSecondGate({
          project: activeProject,
          isDetail: false,
          config: activeProject.main,
          selectedItems: gateTwoItems,
          selectedNames: gateTwoItems.map(function (item) { return item.name; }),
          totalImages: gateTwoItems.length * activeProject.main.setCount,
          maxCredits: gateTwoItems.length * activeProject.main.setCount * mainImageUnitPrice
        });
      }
      if (requestedScenario === "copy-abandon") {
        navNote.textContent = "放弃前请确认将删除和保留的内容";
        openTaskAbandonDialog(activeProject, false, activeProject.main);
      }
      if (requestedScenario === "gate-one-sufficient") {
        openFirstGate(activeProject, false, activeProject.main);
      }
      if (requestedScenario === "gate-one-insufficient") {
        openFirstGate(activeProject, false, activeProject.main);
      }
      if (requestedScenario === "gate-one-confirmed") {
        openFirstGate(activeProject, false, activeProject.main);
      }
      if (requestedScenario === "gate-one-return-blocked") {
        state.firstGateConfirmed = true;
        state.workbenchMode = "copy-confirm";
        navNote.textContent = "确认文案后开始生成任务";
        renderWorkbench();
        openTaskAbandonDialog(activeProject, false, activeProject.main, "return-to-settings");
      }
      if (requestedScenario === "library-draft-replace") {
        openDraftReplaceDialog(activeProject, false, activeProject.main);
      }
      if (requestedScenario === "library-abandon-new" || requestedScenario === "library-abandon-existing") {
        openTaskAbandonDialog(activeProject, false, activeProject.main);
      }
      if (requestedScenario === "library-delete-blocked" || requestedScenario === "library-delete-confirm") {
        openProjectDeleteDialog(activeProject);
      }
      if (requestedScenario === "main-setup-reference-boundary") {
        openModal(referenceBoundaryDialog, closeReferenceBoundary);
      }
      if (requestedScenario === "ux-dialog-focus") {
        document.getElementById("delete-project").focus({ preventScroll: true });
        openProjectDeleteDialog(activeProject);
      }
      if (requestedScenario === "ux-copy-live-update") {
        window.setTimeout(function () {
          var activeInput = view.querySelector('[data-copy-field="headline"][data-copy-set-index="0"]');
          var copyGrid = view.querySelector(".copy-set-grid");
          if (copyGrid) copyGrid.scrollTop = 48;
          if (activeInput) {
            activeInput.focus({ preventScroll: true });
            activeInput.setSelectionRange(2, 2);
          }
          navNote.textContent = "任务进度已更新；当前文案编辑保持不变";
          renderWorkbench();
        }, 1200);
      }
      if (requestedScenario === "main-setup-autosave") {
        showDraftSaveToast("生成任务设置未保存", "可以继续设置。下次修改时会自动重试。", "failed");
      }
    })();
