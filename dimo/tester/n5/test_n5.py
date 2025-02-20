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
            '05': self._test_periodisering,
            'all': self._run_all_tests
        }

        if test_name not in test_map:
            raise ValueError(f"Unknown test: {test_name}")

        return test_map[test_name]()

    def _test_endringslogg(self) -> Dict[str, Any]:
        """Test 01: Count changes in endringslogg
        https://github.com/arkivverket/AV-MTM/blob/master/n5uttrekkstester/antall_endringer_endringslogg.py 
        """
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
        """Test 02: Count archive entities
        https://github.com/arkivverket/AV-MTM/blob/master/n5uttrekkstester/arkivenhetstelling.py 
        """
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
        """Test 03: Count classes by creation date
        https://github.com/arkivverket/AV-MTM/blob/master/n5uttrekkstester/klasse_dato.py
        """
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
        """Test 04: Check for empty documents
        https://github.com/arkivverket/AV-MTM/blob/master/n5uttrekkstester/sjekk_tomme_dokumentobjekt.py 
        """
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

    def _test_periodisering(self) -> Dict[str, Any]:
        """Test 05: Check periodization of archive records
        Analyzes the dates in the archive structure and checks if they fall within the expected period.
        https://github.com/arkivverket/AV-MTM/blob/master/n5uttrekkstester/periodiseringskontroll.py
        """
        tree = ET.parse(self.arkivstruktur_path)
        root = tree.getroot()
        ns = "http://www.arkivverket.no/standarder/noark5/arkivstruktur"
        
        # Find all journal dates
        journal_dates = []
        for reg in root.findall(f".//{{{ns}}}journaldato"):
            if reg is not None and reg.text:
                journal_dates.append(reg.text.strip())
        
        # Try to find period dates from arkivdel
        start_date = None
        end_date = None
        for arkivdel in root.findall(f".//{{{ns}}}arkivdel"):
            opprettet = arkivdel.find(f".//{{{ns}}}opprettetDato")
            avsluttet = arkivdel.find(f".//{{{ns}}}avsluttetDato")
            if opprettet is not None and opprettet.text:
                start_date = opprettet.text.strip()
            if avsluttet is not None and avsluttet.text:
                end_date = avsluttet.text.strip()
            if start_date and end_date:
                break
        
        # Use default dates if not found
        start_date = start_date or "1970-01-01"
        end_date = end_date or "2030-12-31"
        
        # Count dates within and outside period
        dates_within = 0
        dates_outside = 0
        dates_by_year = {}
        
        for date_str in journal_dates:
            try:
                date = datetime.strptime(date_str, "%Y-%m-%d").date()
                year = date.year
                dates_by_year[year] = dates_by_year.get(year, 0) + 1
                
                period_start = datetime.strptime(start_date, "%Y-%m-%d").date()
                period_end = datetime.strptime(end_date, "%Y-%m-%d").date()
                
                if period_start <= date <= period_end:
                    dates_within += 1
                else:
                    dates_outside += 1
            except ValueError:
                continue
        
        return {
            'total_journal_dates': len(journal_dates),
            'period_start': start_date,
            'period_end': end_date,
            'dates_within_period': dates_within,
            'dates_outside_period': dates_outside,
            'dates_by_year': dict(sorted(dates_by_year.items()))
        }

    def _run_all_tests(self) -> Dict[str, Any]:
        """Run all available tests"""
        return {
            'test_01': self._test_endringslogg(),
            'test_02': self._test_arkivenhetstelling(),
            'test_03': self._test_klasse_dato(),
            'test_04': self._test_tomme_dokumentobjekt(),
            'test_05': self._test_periodisering()
        }

def run_n5_test(test_name: Optional[str] = None) -> Dict[str, Any]:
    """Main entry point for running N5 tests"""
    workspace = env_handling.get_workspace()
    uttrekksmappe = workspace.get_workspace_path()
    tester = N5Tester(uttrekksmappe)
    return tester.run_test(test_name or 'all')