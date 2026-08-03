import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from scrapers.emvs_scraper import parse_promotions


HTML = """
<section>
  <article>
    <a href="fichaExpte.do?idExpediente=100">113/2026</a>
    <p>Descripción: Servicios de dirección de obra de edificio de 46 viviendas
       (VPPA) en la promoción denominada VALLECAS 72</p>
    <p>Asunto: Alta licitación en Portal</p>
    <p>Organismo: Departamento de Innovación y Calidad</p>
  </article>
  <article>
    <a href="fichaExpte.do?idExpediente=101">094/2026</a>
    <p>Descripción: Servicio de seguro de impago de rentas para viviendas</p>
    <p>Asunto: Alta licitación en Portal</p>
    <p>Organismo: Gestión de Vivienda</p>
  </article>
</section>
"""


class EmvsScraperTests(unittest.TestCase):
    def test_keeps_projects_and_discards_administrative_contracts(self):
        promotions = parse_promotions(HTML)
        self.assertEqual(len(promotions), 1)
        self.assertEqual(promotions[0]["title"], "VALLECAS 72")
        self.assertEqual(promotions[0]["source"], "EMVS Madrid")
        self.assertIn("idExpediente=100", promotions[0]["url"])


if __name__ == "__main__":
    unittest.main()
