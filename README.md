# LosPrice

**Precifique com inteligência. Lucre com confiança.**

Sistema de precificação para food service — pastelarias, pizzarias, hamburguerias,
lanchonetes e restaurantes. Calcula o custo real de cada produto a partir da ficha
técnica e define o preço certo para cada canal de venda.

Faz parte da família **Los Software**, junto com o
[LosManager](https://github.com/ramonxxl/LosManager).

---

## O problema que ele resolve

A maioria dos donos de food service precifica multiplicando o custo por uma margem.
Isso está errado, e o erro custa caro.

Taxa de iFood, taxa de cartão e imposto **não incidem sobre o custo — incidem sobre
o preço de venda**. Quem multiplica perde dinheiro sem perceber:

| Método | Preço | Lucro real | Margem real |
|---|---|---|---|
| Multiplicando (errado) | R$ 7,65 | R$ 0,13 | 1,6% |
| Dividindo (correto) | R$ 10,64 | R$ 2,13 | **20,0%** |

> Custo R$ 5,00 · iFood 27% · imposto 6% · lucro desejado 20%

O LosPrice usa o **método divisor**:

```
preço = (custo + custos em R$) ÷ (1 − soma dos percentuais)
```

---

## Recursos

### Ingredientes
- Cadastro pela **compra**: informe "5 kg por R$ 185,00" e o sistema deriva o custo por grama
- **Fator de correção** — 1 kg de carne que rende 700 g depois da limpeza custa 43% mais caro
- Histórico de preços com variação percentual
- Alerta automático quando um insumo sobe de preço

### Embalagens
- Custo por unidade a partir do pacote comprado
- Alerta de **peso sobre o produto** — embalagem passando de 10% do custo

### Fichas técnicas
- Montagem item a item com custo se formando em tempo real
- **Composição do custo** com participação de cada ingrediente
- Rendimento e custo por porção
- Detecção de ficha desatualizada quando um insumo muda de preço

### Precificação
- Preço certo para **Balcão, WhatsApp, iFood, 99Food e Rappi** lado a lado
- Lucro líquido e margem real por canal
- Arredondamento psicológico (`,90`)
- Alerta de produto vendendo no prejuízo

### Simulador
- "E se eu vender por R$ 18,90?" com abertura completa do preço
- Barra proporcional mostrando para onde vai cada centavo
- Preço mínimo, desconto máximo e custo-alvo

### Fornecedores
- Cadastro, itens fornecidos e total já comprado
- **Comparativo de preço** quando o mesmo insumo veio de mais de um fornecedor

### Configurações
- Regime tributário com alíquota automática
- Edição das taxas de cada canal
- **Rateio real de custo fixo** — em R$ por unidade e em % sobre o faturamento
- Backup e restauração do banco

### Dashboard
- Alertas acionáveis: produto no prejuízo, ficha defasada, insumo que subiu
- Ranking de produtos por margem
- Insumos que mais pesam nas fichas — onde negociar rende mais

### Relatórios
- **Ficha técnica em PDF** para imprimir e colar na cozinha
- Tabela de preços por canal em PDF
- **Engenharia de cardápio** — classifica cada produto em Estrela, Puxador,
  Enigma ou Abacaxi cruzando margem com volume de vendas
- Exportação para Excel com quatro abas

---

## Instalação

### Usar o programa pronto (Windows)

Baixe o `LosPrice.zip` da página de
[Releases](https://github.com/ramonxxl/LosPrice/releases), extraia a pasta
onde quiser e execute **`LosPrice.exe`**. Não precisa ter Python instalado.

Os dados ficam ao lado do executável, em `dados/`, `backups/` e `relatorios/`.
Para atualizar depois, substitua os arquivos do programa e **mantenha essas
três pastas** — assim nada é perdido.

### Rodar a partir do código

Requer **Python 3.10+**.

```bash
git clone https://github.com/ramonxxl/LosPrice.git
cd LosPrice
pip install -r requirements.txt
python main.py
```

O banco de dados é criado automaticamente na primeira execução.

### Gerar o executável

```bash
build.bat
```

O resultado sai em `dist/LosPrice/`. Todo push na `main` também gera uma
release automática pelo GitHub Actions.

---

## Estrutura

```
LosPrice/
├── main.py                 janela, menu lateral e roteamento
├── core/
│   └── calculo.py          motor de cálculo (sem interface, testável)
├── database/
│   └── conexao.py          schema, conexão e backup
├── controllers/            regra de negócio — as telas não escrevem SQL
├── screens/                interface
├── utils/
│   ├── tema.py             identidade visual e formatação brasileira
│   └── componentes.py      widgets reutilizáveis
└── assets/
```

A arquitetura separa cálculo, dados e interface. `core/calculo.py` não importa
nada de interface nem de banco — pode ser testado sozinho:

```bash
python core/calculo.py
```

---

## Tecnologia

Python · CustomTkinter · SQLite · Pillow · ReportLab · OpenPyXL

---

## Licença

Uso pessoal e comercial reservado ao autor.

© Los Software
