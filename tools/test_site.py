"""Regression checks for generation safety and the static website contract."""
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse, unquote

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('generator', ROOT / 'tools/gen_i18n.py')
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)

class Elements(HTMLParser):
    def __init__(self, source):
        super().__init__(); self.elements=[]; self.feed(source)
    def handle_starttag(self, tag, attrs): self.elements.append((tag,dict(attrs)))

class GeneratorSafety(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='easen-generator-')
        self.root = Path(self.temp.name).resolve()
        self.old_root = generator.ROOT
        generator.ROOT = str(self.root)
        generator.PENDING_WRITES.clear(); generator.PLANNED_OUTPUTS.clear()
        self.source = '<html lang="zh"><head><title>Old</title><link rel="canonical" href="https://chinaeasen.com/"/></head><body><h1><span data-lang="en">Hello</span><span data-lang="fr">Bonjour</span><span data-lang="fr">Bonjour</span></h1><script>var retained = 1;</script></body></html>'
        (self.root/'index.html').write_text(self.source,encoding='utf-8')
        for language in ['en','fr']:
            (self.root/language).mkdir()
            (self.root/language/'index.html').write_text('previous',encoding='utf-8')
        (self.root/'en/custom-page.html').write_text('handwritten page',encoding='utf-8')
        (self.root/'en/about.html').write_text('existing about',encoding='utf-8')
    def tearDown(self):
        generator.ROOT = self.old_root
        generator.PENDING_WRITES.clear(); generator.PLANNED_OUTPUTS.clear()
        # Only the uniquely allocated temporary test directory is cleaned up.
        self.assertEqual(Path(self.temp.name).resolve(), self.root)
        self.temp.cleanup()
    def main(self,*args):
        old=sys.argv;sys.argv=['gen_i18n.py',*args]
        try:generator.main()
        finally:sys.argv=old
    def test_partial_generation_preserves_unselected_files(self):
        self.main('--langs','en','--pages','index.html')
        self.assertEqual((self.root/'en/custom-page.html').read_text(),'handwritten page')
        self.assertEqual((self.root/'en/about.html').read_text(),'existing about')
        self.assertEqual((self.root/'fr/index.html').read_text(),'previous')
        self.assertIn('hreflang="fr"',(self.root/'en/index.html').read_text())
    def test_full_generation_preserves_custom_pages(self):
        self.main('--langs','en,fr')
        self.assertEqual((self.root/'en/custom-page.html').read_text(),'handwritten page')
    def test_check_has_no_writes(self):
        before={str(p.relative_to(self.root)):p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        with self.assertRaises(SystemExit) as caught:self.main('--langs','en','--check')
        self.assertEqual(caught.exception.code,1)
        self.assertEqual(before,{str(p.relative_to(self.root)):p.read_bytes() for p in self.root.rglob('*') if p.is_file()})
    def test_invalid_page_rejected_before_writing(self):
        with self.assertRaises(SystemExit):self.main('--pages','../index.html')
        self.assertEqual((self.root/'en/index.html').read_text(),'previous')
    def test_duplicate_translation_removed_and_script_preserved(self):
        result=generator.gen_page(self.source,'index.html','fr',{'index.html'},'\n')
        self.assertEqual(result.count('>Bonjour</span>'),1)
        self.assertIn('<script>var retained = 1;</script>',result)
    def test_output_outside_root_rejected(self):
        with self.assertRaises(ValueError):generator.stage_write(self.root.parent/'outside.html',b'not allowed')

class WebsiteContract(unittest.TestCase):
    def test_generated_site_is_current(self):
        result=subprocess.run([sys.executable,str(ROOT/'tools/gen_i18n.py'),'--check'],capture_output=True)
        self.assertEqual(result.returncode,0,result.stdout.decode('utf-8',errors='replace')+result.stderr.decode('utf-8',errors='replace'))
    def test_local_links_resolve(self):
        errors=[]
        for path in ROOT.rglob('*.html'):
            relative=path.relative_to(ROOT).as_posix()
            if relative.startswith(('admin/','tools/')) or relative=='index-demo.html':continue
            page_url='https://chinaeasen.com/'+(relative[:-10] if relative.endswith('index.html') else relative)
            for tag,attrs in Elements(path.read_text(encoding='utf-8')).elements:
                if tag!='a' or not attrs.get('href') or attrs['href'].startswith('#'):continue
                url=urlparse(urljoin(page_url,attrs['href']))
                if url.hostname!='chinaeasen.com':continue
                target=unquote(url.path).lstrip('/')
                if target.startswith(('images/','videos/')):continue
                destination=ROOT/target
                if destination.is_dir():destination/= 'index.html'
                if not destination.is_file():errors.append((relative,attrs['href']))
        self.assertEqual(errors,[])
    def test_language_metadata_and_return_urls(self):
        for language in generator.LANGS:
            for page,translations in generator.SEO_META.items():
                text=(ROOT/language/page).read_text(encoding='utf-8')
                elements=Elements(text).elements
                canon=[a['href'] for t,a in elements if t=='link' and a.get('rel')=='canonical']
                self.assertEqual(canon,[generator.page_url(page,language)])
                description=[a['content'] for t,a in elements if t=='meta' and a.get('name')=='description']
                self.assertEqual(description,[translations[language][1]])
                for tag,a in elements:
                    if tag=='input' and a.get('name')=='_next':self.assertTrue(a['value'].startswith('https://chinaeasen.com/'+language+'/'))
                for block in re.findall(r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>',text,re.S):
                    data=json.loads(block)
                    for node in data.get('@graph',[data]):
                        if node.get('@type') in {'AboutPage','ContactPage','CollectionPage','Article','BlogPosting'}:
                            self.assertEqual(node.get('url'),generator.page_url(page,language))
                            self.assertEqual(node.get('inLanguage'),language)
    def test_no_placeholder_whatsapp(self):
        for path in ROOT.rglob('*.html'):
            self.assertNotIn('wa.me/8613800000000',path.read_text(encoding='utf-8'),str(path))
    def test_no_fake_product_offer_on_landing_pages(self):
        for path in (ROOT/'en').glob('*.html'):
            if path.name in generator.SEO_META:continue
            text=path.read_text(encoding='utf-8')
            self.assertIn('rel="canonical"',text,str(path))
            for block in re.findall(r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>',text,re.S):
                for node in json.loads(block).get('@graph',[]):self.assertNotEqual(node.get('@type'),'Product',str(path))
    def test_admin_has_no_published_password_or_persistent_token(self):
        text=(ROOT/'admin/index.html').read_text(encoding='utf-8')
        self.assertNotRegex(text,r'ADMIN_(?:USER|PASS)\s*=')
        self.assertNotRegex(text,r'localStorage\.setItem\([\'"]easen-token')
        self.assertIn('verifyRepositoryToken',text)
        self.assertNotIn('id="login-pass"',text)

if __name__=='__main__':unittest.main(verbosity=2)
