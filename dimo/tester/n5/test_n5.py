import xml.etree.ElementTree as ET
import pathlib as pl
from typing import Dict, Any, Optional

from ... import env_handling

class N5Tester:
    def __init__(self, uttrekksmappe: pl.Path):
        self.uttrekksmappe = uttrekksmappe
        self.arkivstruktur_path = pl.Path.joinpath(uttrekksmappe, "arkivstruktur.xml")
        self.endringslogg_path = pl.Path.joinpath(uttrekksmappe, "endringslogg.xml")

    def run_test(self, test_name: str) -> Dict[str, Any]:
        """Run a specific N5 test by name"""
        test_map = {
            '01': self._test_endringslogg,
            '02': self._test_arkivenhetstelling,
            '03': self._test_klasse_dato,
            '04': self._test_tomme_dokumentobjekt,
            'all': self._run_all_tests
        }

        if test_name not in test_map:
            raise ValueError(f"Unknown test: {test_name}")

        return test_map[test_name]()

    def _test_endringslogg(self) -> Dict[str, Any]:
        """Test 01: Count changes in endringslogg"""
        tree = ET.parse(self.endringslogg_path)
        root = tree.getroot()
        
        changes = {}
        total_changes = 0
        namespace = {'ns': 'http://www.arkivverket.no/standarder/noark5/endringslogg'}

        for parent in root.findall(".//ns:endring", namespace):
            for child in parent.findall(".//ns:referanseArkivenhet", namespace):
                if child.text:
                    ref = child.text.strip()
                    changes[ref] = changes.get(ref, 0) + 1
                    total_changes += 1

        return {
            'significant_changes': {ref: count for ref, count in changes.items() if count > 4},
            'total_changes': total_changes
        }

    def _test_arkivenhetstelling(self) -> Dict[str, Any]:
        """Test 02: Count archive entities"""
        counts = {
            'arkivdeler': 0,
            'saker': 0,
            'journalposter': 0,
            'dokumentobjekt': 0
        }

        for element in ET.parse(self.arkivstruktur_path).iter():
            tag = element.tag.split('}')[-1]
            if tag == 'arkivdel': counts['arkivdeler'] += 1
            elif tag == 'mappe': counts['saker'] += 1
            elif tag == 'registrering': counts['journalposter'] += 1
            elif tag == 'dokumentobjekt': counts['dokumentobjekt'] += 1

        return counts

    def _test_klasse_dato(self) -> Dict[str, Any]:
        """Test 03: Count classes by creation date"""
        tree = ET.parse(self.arkivstruktur_path)
        root = tree.getroot()
        
        date_counts = {}
        ns = "http://www.arkivverket.no/standarder/noark5/arkivstruktur"

        for klasse in root.findall(f".//{{{ns}}}klasse"):
            dato = klasse.find(f".//{{{ns}}}opprettetDato")
            if dato is not None and dato.text:
                date = dato.text.strip()
                date_counts[date] = date_counts.get(date, 0) + 1

        return {'date_counts': dict(sorted(date_counts.items()))}

    def _test_tomme_dokumentobjekt(self) -> Dict[str, Any]:
        """Test 04: Check for empty documents"""
        tree = ET.parse(self.arkivstruktur_path)
        root = tree.getroot()
        
        empty_docs = []
        ns = "http://www.arkivverket.no/standarder/noark5/arkivstruktur"

        for reg in root.findall(f".//{{{ns}}}registrering"):
            dok = reg.find(f".//{{{ns}}}dokumentobjekt")
            if dok is not None:
                size = dok.find(f".//{{{ns}}}filstoerrelse")
                if size is not None and size.text == "0":
                    empty_docs.append({
                        'system_id': reg.find(f".//{{{ns}}}systemID").text,
                        'title': reg.find(f".//{{{ns}}}tittel").text,
                        'journalposttype': reg.find(f".//{{{ns}}}journalposttype").text if reg.find(f".//{{{ns}}}journalposttype") is not None else "",
                        'format': dok.find(f".//{{{ns}}}format").text if dok.find(f".//{{{ns}}}format") is not None else ""
                    })

        return {
            'empty_documents': empty_docs,
            'count': len(empty_docs)
        }

    def _run_all_tests(self) -> Dict[str, Any]:
        """Run all available tests"""
        return {
            'test_01': self._test_endringslogg(),
            'test_02': self._test_arkivenhetstelling(),
            'test_03': self._test_klasse_dato(),
            'test_04': self._test_tomme_dokumentobjekt()
        }

def run_n5_test(test_name: Optional[str] = None) -> Dict[str, Any]:
    """Main entry point for running N5 tests"""
    workspace = env_handling.get_workspace()
    uttrekksmappe = workspace.get_workspace_path()
    tester = N5Tester(uttrekksmappe)
    return tester.run_test(test_name or 'all')