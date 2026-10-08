# Change settings

The owner changes the runner and the host, model, and effort of each role, then saves. The next agent that starts uses those values.

## Sub-features

- `topbar.open-settings` The gear in the top bar opens the settings sheet and reads the saved configuration.
  source: row:topbar.open-settings
  check: cd mmw-v3/tests/board && uv run --quiet --with playwright python -m unittest test_topbar_rows.TopbarRowsTest.test_topbar_open_settings

- `board.open-settings` The gear on the open board opens the settings sheet over the page.
  source: row:board.open-settings
  check: cd mmw-v3/tests/board && uv run --quiet --with playwright python -m unittest test_board_rows.BoardRowsTest.test_board_open_settings

- `settings.rescan` Rescan asks this machine again, and the sheet shows that the scan is running.
  source: row:settings.rescan
  check: cd mmw-v3/tests/board && uv run --quiet --with playwright python -m unittest test_settings_rows.SettingsRowsTest.test_settings_rescan

- `settings.runner-pick` Choosing a runner marks the draft as changed.
  source: row:settings.runner-pick
  check: cd mmw-v3/tests/board && uv run --quiet --with playwright python -m unittest test_settings_rows.SettingsRowsTest.test_settings_runner_pick

- `settings.runner-rescan` Choosing a runner that crosses paseo starts a rescan.
  source: row:settings.runner-rescan
  check: cd mmw-v3/tests/board && uv run --quiet --with playwright python -m unittest test_settings_rows.SettingsRowsTest.test_settings_runner_rescan

- `settings.runner-locked` While a scan is running, the runner select does not take a new value.
  source: row:settings.runner-locked
  check: none: no test asserts the runner select stays disabled while a scan is running.

- `settings.host-pick-keeps-model` Choosing a host that still offers the current model keeps that model and marks the draft as changed.
  source: row:settings.host-pick-keeps-model
  check: cd mmw-v3/tests/board && uv run --quiet --with playwright python -m unittest test_settings_rows.SettingsRowsTest.test_settings_host_pick_keeps_model

- `settings.host-pick-clears-model` Choosing a host that does not offer the current model clears the model.
  source: row:settings.host-pick-clears-model
  check: cd mmw-v3/tests/board && uv run --quiet --with playwright python -m unittest test_settings_rows.SettingsRowsTest.test_settings_host_pick_clears_model

- `settings.host-locked` While a scan is running, a host select does not take a new host.
  source: row:settings.host-locked
  check: none: no test asserts a host select stays disabled while a scan is running.

- `settings.model-pick` Choosing a model marks the draft as changed.
  source: row:settings.model-pick
  check: cd mmw-v3/tests/board && uv run --quiet --with playwright python -m unittest test_settings_rows.SettingsRowsTest.test_settings_model_pick

- `settings.model-locked` When the host is not answering, the model cell stays hatched and does not take a new model.
  source: row:settings.model-locked
  check: none: no test asserts the model select stays put when the host is not answering.

- `settings.model-locked-scanning` While a scan is running, a model select does not take a new model.
  source: row:settings.model-locked-scanning
  check: none: no test asserts the model select stays disabled while a scan is running.

- `settings.effort-pick` Choosing an effort marks the draft as changed.
  source: row:settings.effort-pick
  check: cd mmw-v3/tests/board && uv run --quiet --with playwright python -m unittest test_settings_rows.SettingsRowsTest.test_settings_effort_pick

- `settings.effort-locked` An effort this machine no longer offers stays selected, and the sheet names that the model has no such level.
  source: row:settings.effort-locked
  check: node --test mmw-v3/tests/board/local-config.test.mjs

- `settings.effort-locked-scanning` While a scan is running, an effort select does not take a new effort.
  source: row:settings.effort-locked-scanning
  check: none: no test asserts the effort select stays disabled while a scan is running.

- `settings.save` Save writes a changed, valid draft and shows the time it was saved.
  source: row:settings.save
  check: cd mmw-v3/tests/board && uv run --quiet --with playwright python -m unittest test_settings_rows.SettingsRowsTest.test_settings_save

- `settings.save-unchanged` With no draft change, Save stays disabled.
  source: row:settings.save-unchanged
  check: none: no test asserts the Save button stays disabled when the draft is unchanged. The case that calls LocalConfig.saveOff does not drive the button.

- `settings.save-blocked` While a cell is flagged, Save stays disabled.
  source: row:settings.save-blocked
  check: none: no test asserts the Save button stays disabled while a cell is flagged. The case that calls LocalConfig.saveOff does not drive the button.

- `settings.save-scanning` While a scan is running, Save stays disabled.
  source: row:settings.save-scanning
  check: none: no test asserts the Save button stays disabled while a scan is running. The case that calls LocalConfig.saveOff does not drive the button.

- `settings.save-refused` After a version conflict, Save stays disabled until the sheet is read again.
  source: row:settings.save-refused
  check: none: no test asserts the Save button stays disabled while a version conflict is showing. The case that calls LocalConfig.saveOff does not drive the button.

- `settings.reread` 重新读取 loads the saved configuration again and drops the refusal banner.
  source: row:settings.reread
  check: cd mmw-v3/tests/board && uv run --quiet --with playwright python -m unittest test_settings_rows.SettingsRowsTest.test_settings_reread

- `settings.close` The X on an unchanged sheet closes it.
  source: row:settings.close
  check: cd mmw-v3/tests/board && uv run --quiet --with playwright python -m unittest test_settings_rows.SettingsRowsTest.test_settings_close

- `board.close-settings` The X on the settings sheet closes it and leaves the top bar in place.
  source: row:board.close-settings
  check: cd mmw-v3/tests/board && uv run --quiet --with playwright python -m unittest test_board_rows.BoardRowsTest.test_board_close_settings

- `settings.close-unchanged` The dismiss control on an unchanged sheet closes it without a write.
  source: row:settings.close-unchanged
  check: cd mmw-v3/tests/board && uv run --quiet --with playwright python -m unittest test_settings_rows.SettingsRowsTest.test_settings_close_unchanged

- `settings.cancel` Cancel on a changed sheet discards the draft and closes the sheet.
  source: row:settings.cancel
  check: cd mmw-v3/tests/board && uv run --quiet --with playwright python -m unittest test_settings_rows.SettingsRowsTest.test_settings_cancel

- `board.cancel-settings` Cancel closes the settings sheet and leaves the top bar in place.
  source: row:board.cancel-settings
  check: cd mmw-v3/tests/board && uv run --quiet --with playwright python -m unittest test_board_rows.BoardRowsTest.test_board_cancel_settings

## How to get to it (user POV)

- The gear at the right of the top bar, `[data-ui="顶栏.settings"]`, opens the settings sheet.

## Driving it

Preconditions: the board is open on the origin `discover` printed, as Open the board describes. The sheet writes the lease's private `MMW_HOME` copy of `models.json`.

- Click `[data-ui="顶栏.settings"]`. The sheet title is 这台机器上，每个 agent 跑在哪. `[data-ui="本机配置.sheet.status"]` reads 没有改动. `[data-ui="本机配置.sheet.save"]` is disabled. The dismiss control reads 关闭.
- Set `[data-ui="本机配置.runner.select"]` to herdr. The status becomes 改了 1 处：runner. Save is enabled. The dismiss control reads 取消.
- Click `[data-ui="本机配置.sheet.cancel"]`. The sheet is gone. Open the gear again and the runner is still orca.
- Set the runner to herdr and click `[data-ui="本机配置.sheet.save"]`. The status becomes 已保存 and a time, and Save is disabled. Set the runner back to orca and save again. The runner on the reopened sheet is orca.

## Gotchas

A run wastes its time, or reports a pass it did not earn, in these cases.

- A save from the harness board writes the lease's private `MMW_HOME` only. This machine's real `models.json` stays as it was.
- Save stays disabled until the draft differs from the saved copy, no cell is flagged, and no scan is running.
- After a change, the dismiss control reads 取消 and drops the draft. With no change it reads 关闭.
- When `MMW_RUNNER` is set, it wins over the runner cell. The sheet says so.
- A version conflict leaves the sheet up and offers 重新读取. Save stays off until that reread.

The critical flow `task-board/settings-save` saves another legal reviewer model and reads it back on reopening. Run `python3 ~/.agents/skills/ui-acceptance/scripts/journey.py run task-board/settings-save --break "PUT /api/settings"`.
