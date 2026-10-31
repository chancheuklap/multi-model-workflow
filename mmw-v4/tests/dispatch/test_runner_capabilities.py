"""Runner selection, launch capability and catalog storage stay independent."""

import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_catalog import fake_host
from test_local_config import models, base_config


class RunnerCapabilitiesTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='mmw-runner-capabilities-')
        self.addCleanup(temporary.cleanup)
        self.home = Path(temporary.name).resolve()
        environment = {key: value for key, value in os.environ.items()
                       if key not in ('MMW_HOST_CATALOG', 'MMW_RUNNER', 'MMW_CATALOG_MODE',
                                      'CODEX_THREAD_ID', 'CODEX_APP_RUNTIME_CLI_PATH',
                                      'CODEX_APP_TOOLS_PIPE_PATH', 'TERM_PROGRAM', 'HERDR_ENV')}
        environment.update(HOME=str(self.home), MMW_HOME=str(self.home))
        environment_patch = patch.dict(os.environ, environment, clear=True)
        environment_patch.start()
        self.addCleanup(environment_patch.stop)
        models.models_json_path().write_text(json.dumps(base_config()))

    def app_context(self):
        binary = fake_host(self.home, 'codex')
        os.environ.update(CODEX_THREAD_ID='independent-chat',
                          CODEX_APP_RUNTIME_CLI_PATH=str(binary),
                          CODEX_APP_TOOLS_PIPE_PATH='host-owned-binding')

    def test_each_runner_declares_its_launch_capability_without_starting_a_host(self):
        hosts = models.load_hosts()['hosts']
        for runner in ('orca', 'herdr', 'paseo', 'codex-app'):
            with self.subTest(runner=runner):
                self.assertTrue(models._can_start(runner, hosts['codex']))
                self.assertEqual(models._can_start(runner, hosts['claude']), runner != 'codex-app')

    def test_executor_belongs_to_the_caller_while_dispatch_target_remains_orca(self):
        self.app_context()
        os.environ['MMW_RUNNER'] = 'orca'
        self.assertEqual(models.runner_name(), 'orca')
        executor = Path(models.tool_executor())
        self.assertEqual(executor.name, 'codex-app-tools.js')
        self.assertTrue(executor.is_file())
        os.environ.pop('CODEX_APP_TOOLS_PIPE_PATH')
        self.assertEqual(models.tool_executor(), '')

    def test_auto_selects_the_actual_caller_without_changing_saved_configuration(self):
        self.app_context()
        os.environ['MMW_RUNNER'] = 'auto'
        before = models.models_json_path().read_bytes()
        self.assertEqual(models.runner_name(), 'codex-app')
        os.environ['TERM_PROGRAM'] = 'Orca'
        self.assertEqual(models.runner_name(), 'orca')
        os.environ['HERDR_ENV'] = '1'
        self.assertEqual(models.runner_name(), 'herdr')
        self.assertEqual(models.models_json_path().read_bytes(), before)

    def test_app_scan_uses_its_binary_and_keeps_terminal_catalog_unchanged(self):
        self.app_context()
        cli = models.scan_host_catalogs('orca', ['codex'])
        self.assertEqual(cli['hosts']['codex']['state'], 'ok')
        cli_record = models.read_catalog_cache()['cli']['codex']
        rows = json.loads((self.home / 'codex.rows').read_text())
        rows[0].update(id='app-model', displayName='App Model')
        (self.home / 'codex.rows').write_text(json.dumps(rows))
        app = models.scan_host_catalogs('codex-app')
        self.assertEqual(app['source'], 'codex-app')
        self.assertEqual(app['hosts']['claude']['state'], 'unlaunchable')
        self.assertEqual(app['hosts']['codex']['offered'][0]['model'], 'app model')
        self.assertEqual(models.read_catalog_cache()['cli']['codex'], cli_record)
        self.assertEqual(models.read_catalog_cache()['codex-app']['codex']['offerings'][0]['id'],
                         'app-model')

    def test_app_configuration_refuses_unsupported_host_without_overwriting_settings(self):
        self.app_context()
        before = models.models_json_path().read_bytes()
        with self.assertRaises(models.InvalidConfig) as error:
            models.write_local_config(base_config(runner='codex-app'), 1,
                                      models.scan_host_catalogs('codex-app'))
        self.assertTrue(any('cannot start host claude' in row['reason']
                            for row in error.exception.errors))
        self.assertEqual(models.models_json_path().read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
