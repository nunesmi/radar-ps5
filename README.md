# Radar PS5

Monitoramento automático de ofertas do **PS5 Slim 1 TB com leitor de disco** (e, como
oportunidades secundárias, PS5 Digital, PS5 Pro, DualSense e DualSense Edge).

Roda no **GitHub Actions a cada ~10 minutos, 24 h por dia**, mesmo com o computador
desligado. Grava o histórico no próprio repositório, publica um painel no GitHub Pages
e manda alertas pelo **Telegram** só para ofertas EXCEPCIONAIS ou IMPERDÍVEIS.

## Como funciona

| Etapa | O que faz | Arquivo |
|---|---|---|
| Coleta | Ofertas da comunidade no **Pelando** (site: funciona só fora de servidores de nuvem), canais públicos do Telegram **Pelando Promoções** e **CJ Promoções** (funcionam na nuvem; oferta considerada ativa por 90 min) e preços de vitrine da **KaBuM!** (Pix, cartão, parcelas, estoque, só vendido pela KaBuM!) | `radar/sources.py` |
| Modelo | Reconhece o modelo pelo título. Só aceita o console principal com evidência clara de leitor de disco + 1 TB. Descarta Digital, 825 GB, usados, importados, leitor avulso e acessórios. Na dúvida: "modelo a confirmar", que nunca gera alerta | `radar/models.py` |
| Loja | Só lojas da lista de confiáveis. Marketplaces (Mercado Livre, Shopee) aparecem como confiabilidade "Média" | `radar/config.py` |
| Preço | Média de mercado = mediana dos preços de vitrine de 2+ lojas em 30 dias; sem dados suficientes, usa a referência configurada. Ofertas relâmpago **não** entram na média | `radar/pricing.py` |
| Alerta | Telegram, sem duplicar (só re-alerta se o preço cair mais R$ 50). Avisa também se todas as fontes falharem por 1 hora | `radar/notify.py` |
| Painel | `docs/index.html` + `docs/data.json` | `docs/` |

### Classificação (console principal)

| Classe | Critério (contra a média de mercado) | Alerta |
|---|---|---|
| EXCEPCIONAL | ≥ 20% ou ≥ R$ 900 abaixo, ou abaixo do menor preço já visto (com ≥ 10%) | ✅ |
| IMPERDÍVEL | ≥ 12% ou ≥ R$ 500 abaixo | ✅ |
| BOA OFERTA | ≥ 5% ou ≥ R$ 200 abaixo | — |
| MONITORAR | abaixo da média, mas pouco | — |
| DESCARTAR | igual/acima da média, loja não confiável ou modelo errado | — |

Produtos secundários só alertam quando EXCEPCIONAIS **e** no menor preço já visto (±5%).
Console abaixo de R$ 2.500 é sinalizado como **possível erro de preço** (risco de cancelamento).

## Ajustes comuns

Tudo em `radar/config.py`: lojas confiáveis, buscas, preço de referência, limites das classes.

## Limitações honestas

- Amazon e Magalu bloqueiam consultas automáticas, e a API do Mercado Livre exige login de
  desenvolvedor. O site do Pelando bloqueia servidores de nuvem (HTTP 403 no GitHub Actions).
  Ofertas dessas lojas chegam pelos canais do Telegram do Pelando e da CJ Promoções.
- O GitHub Actions roda a cada ~10 min e pode atrasar; ofertas que duram 2 minutos podem escapar.
- Cupons não são testados no carrinho (exigiria entrar na sua conta); o alerta mostra o cupom do post.
- O GitHub pausa agendamentos de repositórios sem atividade por 60 dias; os commits do próprio
  radar contam como atividade.

## Rodar localmente

```
python run.py --dry-run     # consulta tudo, imprime alertas, não grava nada
python -m unittest discover -s tests
```
