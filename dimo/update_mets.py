import os
import hashlib
import mimetypes
import shutil
import datetime
import logging
from concurrent.futures import ThreadPoolExecutor

import xml.etree.ElementTree as ET  # stdlib ElementTree
from lxml import etree  # For XSD-validering 


def configure_logger(log_file_path):
    """
    Setter opp en logger som skriver til fil med tidsstempel.
    """
    logger = logging.getLogger("dias_mets_updater")
    logger.setLevel(logging.DEBUG)

    # Fjern eventuelle gamle handlere for å unngå duplisert logging
    if logger.hasHandlers():
        logger.handlers.clear()

    file_handler = logging.FileHandler(log_file_path, mode="a", encoding="utf-8")
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # I tillegg kan du legge til en konsoll-handler hvis ønskelig
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def calculate_sha256(file_path):
    """Returnerer SHA-256-sjekksum for en gitt fil."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def get_mimetype(file_path):
    """Returnerer MIME-type basert på filnavn/innhold."""
    mimetype, _ = mimetypes.guess_type(file_path)
    return mimetype if mimetype else "application/octet-stream"


def prettify_xml(elem, level=0):
    """
    Gjør XML-structuren pen å lese (innrykk) ved bruk av stdlib ElementTree.
    """
    indent = "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = "\n" + (level + 1) * indent
        for subelem in elem:
            prettify_xml(subelem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = "\n" + level * indent
    else:
        if not elem.tail or not elem.tail.strip():
            elem.tail = "\n" + level * indent


def validate_xml(mets_file, schema_file="dias-mets.xsd", stage="before", logger=None):
    """Validerer METS-fil mot XSD-skjema (hvis tilgjengelig)."""
    if logger is None:
        logger = logging.getLogger("dias_mets_updater")

    if not os.path.exists(schema_file):
        logger.warning(f"Fant ikke XSD-skjema '{schema_file}'. Hopper over validering.")
        return

    try:
        schema = etree.XMLSchema(file=schema_file)
        parser = etree.XMLParser(schema=schema)

        tree = etree.parse(mets_file)
        schema.assertValid(tree)  # Validerer hele dokumentet

        logger.info(f"XML-validering {stage} endringer: OK")

    except etree.XMLSyntaxError as e:
        logger.error(f"XML Syntax Error {stage} endringer: {e}")
    except etree.DocumentInvalid as e:
        logger.error(f"Valideringsfeil {stage} endringer: {e}")


def update_dias_mets(mets_file, content_dir, dry_run=False):
    """
    Oppdaterer en dias-mets.xml med nye filstier, filstørrelser og sjekksummer
    basert på faktisk innhold i 'content_dir'.

    - Oppretter en backup av METS-filen i 'logs'-mappen.
    - Validerer før og etter endringer (hvis dias-mets.xsd finnes).
    - Skriver utfyllende logger til mets_update.log.
    - Håndterer million+ filer ved å bruke ThreadPoolExecutor (parallelle sjekksummer).
    """
    # Opprett logs-mappe og loggfil
    logs_dir = os.path.join(os.path.dirname(mets_file), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    log_file = os.path.join(logs_dir, "mets_update.log")

    logger = configure_logger(log_file)
    logger.info("Starter oppdatering av METS.")

    # Valider METS før endring
    validate_xml(mets_file, stage="before", logger=logger)

    # Lag backup
    backup_file = os.path.join(logs_dir, "dias-mets.xml.bak")
    shutil.copy(mets_file, backup_file)
    logger.info(f"Laget backup av METS-fil: {backup_file}")

    # Parse METS-filen med lxml eller stdlib
    # Merk at for XSD-validering brukte vi lxml. For manipulasjon kan stdlib fungere.
    # Her bruker vi lxml for konsistens (etree).
    parser = etree.XMLParser(remove_blank_text=True)
    tree = etree.parse(mets_file, parser)
    root = tree.getroot()

    # Opprett namespace-map (inkluder xlink!)
    NSMAP = {
    "mets": "http://www.loc.gov/METS/",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
    "xlink": "http://www.w3.org/1999/xlink"
}


    # Sikre at rot-elementet har riktig METS-tag + schemaLocation
    root.tag = "{http://www.loc.gov/METS/}mets"
    root.set("{http://www.w3.org/2001/XMLSchema-instance}schemaLocation",
             "http://www.loc.gov/METS/ dias-mets.xsd")

    # Funksjon for å hente ut filinfo parallelt
    def process_file(file_path):
        file_size = os.path.getsize(file_path)
        file_checksum = calculate_sha256(file_path)
        return file_path, file_size, file_checksum

    # Samle filer i content_dir med parallell sjekk
    logger.info(f"Skanner katalog: {content_dir}")
    all_files = []
    for dirpath, _, files in os.walk(content_dir):
        for f in files:
            if f == ".DS_Store":
                continue
            full_path = os.path.join(dirpath, f)
            all_files.append(full_path)

    content_files = {}
    with ThreadPoolExecutor() as executor:
        for file_path, file_size, file_checksum in executor.map(process_file, all_files):
            # F.eks. content/ARKIV1/arkiv.dat -> ARKIV1/arkiv.dat
            rel_path = os.path.relpath(file_path, content_dir)
            content_files[os.path.normpath(rel_path)] = {
                "size": file_size,
                "checksum": file_checksum,
                "full_path": file_path
            }

    logger.info(f"Fant totalt {len(content_files)} filer i '{content_dir}'.")

    # Oppdater hver <mets:file> i METS-filen
    file_elements = root.findall(".//mets:file", namespaces=NSMAP)
    logger.info(f"Antall <file>-elementer i METS: {len(file_elements)}")

    for file_element in file_elements:
        # Finn <mets:FLocat> inni <file>
        flocat = file_element.find(".//mets:FLocat", namespaces=NSMAP)
        if flocat is None:
            continue

        # Hent ut xlink:href
        xlink_href = flocat.get("{http://www.w3.org/1999/xlink}href")
        if not xlink_href:
            continue  # Finner ingen sti, hopp over

        # Fjern "file:" foran stien, normaliser og relater mot content
        old_href = xlink_href.replace("file:", "").strip()
        old_norm = os.path.normpath(old_href)

        # Hvis stien starter med "content", fjern den biten
        # old_norm = "content/ARKIV1/arkiv.dat" -> "ARKIV1/arkiv.dat"
        if old_norm.startswith("content" + os.sep):
            old_norm = os.path.relpath(old_norm, "content")

        logger.debug(f"Sjekker <file>-element med sti: {xlink_href} (-> {old_norm})")

        # Sjekk om vi finner nøyaktig match i content_files
        if old_norm in content_files:
            # Filen finnes i riktig posisjon allerede. Oppdater size/checksum i tilfelle det er endret.
            info = content_files[old_norm]
            file_element.set("SIZE", str(info["size"]))
            file_element.set("CHECKSUM", info["checksum"])
            file_element.set("CHECKSUMTYPE", "SHA-256")
            # For ordens skyld, sett xlink:href på nytt (kanskje den var litt avvikende)
            new_href = f"file:content/{old_norm}"
            flocat.set("{http://www.w3.org/1999/xlink}href", new_href)
            logger.info(f"Oppdatert metadata for fil: {old_norm}")
        else:
            # Ingen direkte match på hele stien. Forsøk fallback ved filnavn
            base_old = os.path.basename(old_norm)
            matched = False
            for new_rel_path, info in content_files.items():
                if os.path.basename(new_rel_path) == base_old:
                    # Oppdater <file>-elementet til ny sti
                    file_element.set("SIZE", str(info["size"]))
                    file_element.set("CHECKSUM", info["checksum"])
                    file_element.set("CHECKSUMTYPE", "SHA-256")

                    new_href = f"file:content/{new_rel_path}"
                    flocat.set("{http://www.w3.org/1999/xlink}href", new_href)

                    logger.info(f"Oppdatert filsti: {old_norm} -> {new_rel_path}")
                    matched = True
                    break

            if not matched:
                logger.warning(f"Fant ingen match for sti: {old_norm}. Ingen oppdatering gjort.")

    # "Prettify" XML via stdlib (valgfritt; lxml kan også brukes)
    # Konverter lxml -> stdlib ElementTree for å bruke prettify_xml
    # (Dette steget er litt valgfritt. Hvis du vil unngå round-trip-problemer,
    # kan du heller bruke lxml pretty_print under skriving.)
    root_str = etree.tostring(root, encoding="unicode")
    root_std = ET.fromstring(root_str)
    prettify_xml(root_std)

    # Skriv endelig resultat (med mindre dry_run)
    if not dry_run:
        new_tree = ET.ElementTree(root_std)
        new_tree.write(mets_file, encoding="utf-8", xml_declaration=True)
        logger.info("dias-mets.xml er oppdatert med nye stier, filstørrelser og sjekksummer.")
    else:
        logger.info("Dry run - ingen endringer er skrevet til METS-filen.")

    # Valider METS etter endring
    validate_xml(mets_file, stage="after", logger=logger)
    logger.info(f"Loggfil er lagret: {log_file}")


if __name__ == "__main__":
    mets_file = "dias-mets.xml"
    content_dir = "content"
    update_dias_mets(mets_file, content_dir, dry_run=False)
