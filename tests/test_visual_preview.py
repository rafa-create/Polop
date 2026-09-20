"""Offline regression checks; does not claim Unreal shader/render validation."""
import ast
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


class PreviewTests(unittest.TestCase):
    def setUp(self):
        self.values = {}
        self.refuse = None
        system = types.SimpleNamespace(
            get_console_variable_float_value=lambda name: self.values[name],
            execute_console_command=self.command)
        self.unreal = types.SimpleNamespace(
            SystemLibrary=system, UnrealEditorSubsystem=object,
            get_editor_subsystem=lambda cls: types.SimpleNamespace(get_editor_world=lambda: object()),
            log=lambda message: None)
        self.namespace = {'__name__': 'offline_test'}
        self.modules = patch.dict(sys.modules, {'unreal': self.unreal})
        self.modules.start()
        sys.modules.pop('_polop_light_preview_state', None)
        exec(compile((ROOT/'Unreal/preview_quality.py').read_text(encoding='utf-8'),
                     'preview_quality.py', 'exec'), self.namespace)
        self.values.update({name: float(index+70) for index, name in enumerate(self.namespace['_PREVIEW'])})
        self.original = self.values.copy()

    def tearDown(self):
        sys.modules.pop('_polop_light_preview_state', None)
        self.modules.stop()

    def command(self, world, text):
        name, value = text.split()
        if name != self.refuse:
            self.values[name] = float(value)

    def test_preview_restores_exact_previous_values(self):
        toggle = self.namespace['toggle_preview']
        toggle()
        self.assertEqual(self.values, self.namespace['_PREVIEW'])
        # A second Execute Python Script uses fresh globals in the same session.
        other = {'__name__': 'offline_test'}
        exec(compile((ROOT/'Unreal/preview_quality.py').read_text(), 'preview', 'exec'), other)
        other['toggle_preview']()
        self.assertEqual(self.values, self.original)
        self.assertNotIn('_polop_light_preview_state', sys.modules)

    def test_partial_failure_keeps_restore_available(self):
        self.refuse = 'r.ScreenPercentage'
        with self.assertRaises(RuntimeError):
            self.namespace['toggle_preview']()
        self.assertIn('_polop_light_preview_state', sys.modules)
        self.refuse = None
        self.namespace['toggle_preview']()
        self.assertEqual(self.values, self.original)

    def test_failed_restore_retains_snapshot(self):
        self.namespace['toggle_preview']()
        self.refuse = 'r.ScreenPercentage'
        with self.assertRaises(RuntimeError):
            self.namespace['toggle_preview']()
        self.assertIn('_polop_light_preview_state', sys.modules)
        self.refuse = None
        self.namespace['toggle_preview']()
        self.assertEqual(self.values, self.original)


class SyntaxTests(unittest.TestCase):
    def test_generator_and_embedded_sources_compile(self):
        source = (ROOT/'Unreal/previz_polop.py').read_text(encoding='utf-8')
        tree = ast.parse(source)
        compile(tree, 'previz_polop.py', 'exec')
        found = 0
        for node in tree.body:
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
                if any(isinstance(t, ast.Name) and t.id.startswith('_SOURCE_') for t in node.targets):
                    compile(node.value.value, 'embedded', 'exec')
                    found += 1
        self.assertGreaterEqual(found, 2)


if __name__ == '__main__':
    unittest.main()
