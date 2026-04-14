"""Cache de imagens de categorias carregadas de CSV."""

import csv
from functools import lru_cache
from pathlib import Path


def repo_data_dir() -> Path:
    """Resolve diretório base do repositório para dados auxiliares."""
    return Path(__file__).resolve().parents[4] / "data_ingestao"


@lru_cache(maxsize=1)
def category_images() -> dict[str, str]:
    """Carrega mapeamento categoria -> imagem a partir do CSV com aliases."""
    csv_path = repo_data_dir() / "dim_categoria_imagens.csv"
    if not csv_path.exists():
        return {}

    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        mapping: dict[str, str] = {}
        for row in reader:
            category = (row.get("Categoria") or row.get("categoria") or "").strip()
            link = (row.get("Link") or row.get("link") or "").strip()
            if category and link:
                mapping[category] = link

        aliases = {
            "casa_conforto_2": "casa_conforto",
            "construcao_ferramentas_construcao": "construcao_ferramentas",
            "construcao_ferramentas_ferramentas": "construcao_ferramentas",
            "construcao_ferramentas_iluminacao": "construcao_iluminacao",
            "construcao_ferramentas_jardim": "ferramentas_jardim",
            "construcao_ferramentas_seguranca": "construcao_seguranca",
            "moveis_cozinha_area_de_servico_jantar_e_jardim": "moveis_cozinha_jantar_jardim",
            "portateis_cozinha_e_preparadores_de_alimentos": "portateis_cozinha",
        }

        for alias, target in aliases.items():
            if target in mapping and alias not in mapping:
                mapping[alias] = mapping[target]

        return mapping
