"""Configuração do radar. Edite à vontade: lojas confiáveis, buscas e limites."""

# ---------------------------------------------------------------------------
# Buscas por fonte
# ---------------------------------------------------------------------------
PELANDO_QUERIES = [
    "ps5 slim",
    "ps5 midia fisica",
    "playstation 5 disk",
    "playstation 5 leitor",
    "ps5 pro",
    "dualsense",
]

KABUM_QUERIES = [
    "ps5-slim",
    "playstation-5-slim-midia-fisica",
    "playstation-5-pro",
    "controle-dualsense",
]

# ---------------------------------------------------------------------------
# Lojas: nome (como aparece no Pelando / fonte) -> confiabilidade
#   "alta"  = loja grande, produto normalmente vendido e entregue por ela
#   "media" = marketplace: confira se o vendedor é a própria plataforma ou loja oficial
# Lojas fora desta lista são DESCARTADAS.
# ---------------------------------------------------------------------------
TRUSTED_STORES = {
    "amazon": "alta",
    "kabum!": "alta",
    "kabum": "alta",
    "magalu": "alta",
    "magazine luiza": "alta",
    "casas bahia": "alta",
    "ponto": "alta",
    "ponto frio": "alta",
    "extra": "alta",
    "fast shop": "alta",
    "carrefour": "alta",
    "havan": "alta",
    "bemol": "alta",
    "shopb": "alta",
    "americanas": "alta",
    "girafa": "alta",
    "playstation": "alta",
    "playstation store": "alta",
    "sony": "alta",
    "netshoes": "alta",
    "loja vivo": "media",   # ofertas costumam exigir plano Vivo: confira condições
    "lojas zema": "media",
    "mercado livre": "media",
    "shopee": "media",
}

# Anúncios do Mercado Livre cujo catálogo é comprovadamente o PS5 Slim 1 TB COM leitor.
# (o título do catálogo "Sony PlayStation 5 Slim 1TB cor branco" não diz "leitor")
KNOWN_DISC_CATALOG_IDS = {"MLB28616777", "MLB52897777"}

# ---------------------------------------------------------------------------
# Referências de mercado (usadas até o radar ter histórico próprio suficiente)
# Fontes: FarejaPreço 23-25/11/2026 (preço típico R$ 4.300, mínimo R$ 3.700 em 18/11);
#         tabela Sony desde 02/04/2026 (R$ 5.099,90).
# ---------------------------------------------------------------------------
REFERENCE = {
    "ps5_slim_disco_1tb": {"tipico": 4300.0, "minimo": 3650.0},
    "ps5_slim_digital": {"tipico": 4050.0, "minimo": 3200.0},
    "ps5_pro": {"tipico": None, "minimo": None},
    "dualsense": {"tipico": 399.90, "minimo": 214.0},
    "dualsense_edge": {"tipico": 1349.90, "minimo": None},
    "dualsense_especial": {"tipico": None, "minimo": None},
}

PRODUCT_LABELS = {
    "ps5_slim_disco_1tb": "PS5 Slim 1 TB com leitor de disco",
    "ps5_slim_digital": "PS5 Slim Digital",
    "ps5_pro": "PS5 Pro",
    "dualsense": "Controle DualSense",
    "dualsense_edge": "DualSense Edge",
    "dualsense_especial": "DualSense edição especial",
    "modelo_a_confirmar": "PS5 (modelo a confirmar)",
}

MAIN_PRODUCT = "ps5_slim_disco_1tb"

# Mínimo de observações de lojas para usar a mediana própria em vez da referência
MIN_OBS_FOR_OWN_BASELINE = 8
MIN_STORES_FOR_OWN_BASELINE = 2   # mediana própria só com preços de 2+ lojas
BASELINE_WINDOW_DAYS = 30

# ---------------------------------------------------------------------------
# Classificação (desconto real em relação ao preço médio de mercado)
# ---------------------------------------------------------------------------
CLASS_RULES = {
    # nome: (desconto % mínimo, queda absoluta mínima em R$ para console)
    "EXCEPCIONAL": (0.20, 900.0),
    "IMPERDÍVEL": (0.12, 500.0),
    "BOA OFERTA": (0.05, 200.0),
}
ALERT_CLASSES_MAIN = {"EXCEPCIONAL", "IMPERDÍVEL"}
ALERT_CLASSES_SECONDARY = {"EXCEPCIONAL"}

# Preço de console abaixo disto é tratado como possível erro de precificação
PRICE_ERROR_BELOW = 2500.0
# Re-alertar a mesma oferta só se o preço cair pelo menos isto
REALERT_DROP = 50.0
# Alerta de saúde se todas as fontes falharem por N execuções seguidas
HEALTH_FAIL_RUNS = 6

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
