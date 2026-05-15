import unittest
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "python"))

from models.product import Product, product_embedding_text
from search.ranking import search_products


class ProductSearchTest(unittest.TestCase):
    def setUp(self):
        self.products = [
            Product(
                id="1",
                nombre="Camiseta roja Adidas",
                descripcion="Camiseta deportiva roja para looks casuales.",
                marca="Adidas",
                categorias=["camiseta", "deportivo"],
                carpeta="camisetas",
            ),
            Product(
                id="2",
                nombre="Zapatos Oxford negros",
                descripcion="Zapatos elegantes de cuero para eventos formales.",
                marca="Elegante",
                categorias=["zapatos", "formal"],
                carpeta="calzado",
            ),
            Product(
                id="3",
                nombre="Bolso verde",
                descripcion="Bolso de cuero verde para conjuntos casuales.",
                marca="Green Haven",
                categorias=["bolso", "accesorio"],
                carpeta="accesorios",
            ),
        ]

    def test_prioritizes_embedding_similarity(self):
        results = search_products(
            self.products,
            query_embedding=[0.0, 1.0],
            product_embeddings={
                "1": [1.0, 0.0],
                "2": [0.0, 1.0],
                "3": [0.2, 0.8],
            },
            semantic_threshold=0.0,
            limit=2,
        )

        self.assertEqual([result.producto.id for result in results], ["2", "3"])
        self.assertEqual(results[0].score_embedding, 1.0)

    def test_filters_by_category_after_semantic_search(self):
        results = search_products(
            self.products,
            category="zapatos",
            query_embedding=[0.0, 1.0],
            product_embeddings={
                "1": [1.0, 0.0],
                "2": [0.0, 1.0],
                "3": [0.0, 1.0],
            },
            semantic_threshold=0.0,
        )

        self.assertEqual([result.producto.id for result in results], ["2"])

    def test_applies_semantic_threshold(self):
        results = search_products(
            self.products,
            query_embedding=[0.0, 1.0],
            product_embeddings={
                "1": [1.0, 0.0],
                "2": [0.0, 0.4],
                "3": [0.8, 0.2],
            },
            semantic_threshold=0.5,
        )

        self.assertEqual([result.producto.id for result in results], ["2"])

    def test_returns_empty_without_embeddings(self):
        results = search_products(self.products)

        self.assertEqual(results, [])

    def test_product_embedding_text_contains_main_fields(self):
        text = product_embedding_text(self.products[0])

        self.assertIn("Camiseta roja Adidas", text)
        self.assertIn("Adidas", text)
        self.assertIn("camiseta", text)


if __name__ == "__main__":
    unittest.main()
