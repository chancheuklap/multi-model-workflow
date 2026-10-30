"""Exercise the delivered import/export CLIs with small source documents."""
import json
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[2] / 'skills/diagram-design/scripts'


class ImportExport(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def run_script(self, name, source, content, *args):
        path = self.root / source
        path.write_text(content, encoding='utf-8')
        return subprocess.run([sys.executable, str(SCRIPTS / name), str(path), *args],
                              capture_output=True, text=True, check=True)

    def test_drawio_retains_literal_labels_and_excludes_hidden_cells(self):
        source = '''<mxGraphModel><root><mxCell id="0"/><mxCell id="1" parent="0"/>
<mxCell id="a" value="List&lt;String&gt;" vertex="1" parent="1"><mxGeometry x="10" y="20" width="100" height="40"/></mxCell>
<mxCell id="b" value="&lt;b&gt;a &amp;lt; b &amp;gt; c&lt;/b&gt;" style="html=1" vertex="1" parent="1"><mxGeometry x="200" y="20" width="100" height="40"/></mxCell>
<mxCell id="hidden" value="Draft" visible="0" vertex="1" parent="1"><mxGeometry width="100" height="40"/></mxCell>
</root></mxGraphModel>'''
        result = self.run_script('drawio_extract.py', 'input.drawio', source, '--json')
        nodes = json.loads(result.stdout)['pages'][0]['nodes']
        self.assertEqual({node['id']: node['label'] for node in nodes},
                         {'a': 'List<String>', 'b': 'a < b > c'})

    def test_mermaid_header_tail_and_edge_ids_keep_the_connection(self):
        result = self.run_script('mermaid_extract.py', 'input.mmd',
                                 'graph TD; A[Start] e1@--> B[End]; e1@{ animate: true };', '--json')
        diagram = json.loads(result.stdout)['diagrams'][0]
        self.assertEqual({n['id'] for n in diagram['nodes']}, {'A', 'B'})
        self.assertEqual([(e['source'], e['target']) for e in diagram['edges']], [('A', 'B')])

    def test_sequence_digest_retains_numbering_and_alternative_regions(self):
        result = self.run_script('mermaid_extract.py', 'input.mmd', '''sequenceDiagram
autonumber 10 5
alt success
A->>B: Save
else retry
B->>A: Try again
end
''')
        self.assertIn('from 10, step 5', result.stdout)
        self.assertIn('else: retry', result.stdout)

    def test_excalidraw_reports_inner_and_outer_groups(self):
        elements = [dict(id=name, type='rectangle', groupIds=groups, x=0, y=0, width=80, height=40)
                    for name, groups in [('a', ['inner', 'outer']), ('b', ['inner', 'outer']), ('c', ['outer'])]]
        result = self.run_script('excalidraw_extract.py', 'input.excalidraw',
                                 json.dumps(dict(type='excalidraw', elements=elements)), '--json')
        groups = json.loads(result.stdout)['scene']['analysis']['collapsible_groups']
        self.assertEqual({g['id']: g['children'] for g in groups}, {'outer': 3, 'inner': 2})

    def test_export_preserves_conditional_css_and_accessible_names(self):
        source = '''<!doctype html><html><head><style>
body { color: #2d3142; }
@media print { .node { fill: red; } }
@media screen { .node { fill: blue; } }
</style></head><body><svg viewBox="0 0 100 100" role="img" aria-labelledby="sample-title sample-desc">
<title id="sample-title">Sample</title><desc id="sample-desc">A box.</desc>
<rect class="node" width="80" height="40"/></svg></body></html>'''
        out = self.root / 'output.svg'
        self.run_script('export_svg.py', 'input.html', source, str(out), '--system-fonts')
        exported = out.read_text()
        root = ET.fromstring(exported)
        self.assertEqual(root.attrib['aria-labelledby'], 'sample-title sample-desc')
        self.assertEqual(root[0].tag.rsplit('}', 1)[-1], 'title')
        css = ''.join(element.text or '' for element in root.iter() if element.tag.endswith('}style'))
        self.assertIn('@media print', css)
        self.assertIn('@media screen', css)
        self.assertNotIn('fonts.googleapis.com', exported)


if __name__ == '__main__':
    unittest.main()
