# Planejamento do Modelo de Classificação e do Teste Adversarial (TP3 — item 6)

**Projeto:** Customer Support Ticket Classifier
**Disciplina:** Projeto de Bloco (PB) — Instituto Infnet
**Autor:** Miguel Andrade

---

## 1. Modelo candidato

**Algoritmo escolhido: Regressão Logística (`sklearn.linear_model.LogisticRegression`)**, com
Support Vector Machine (SVM linear, `sklearn.svm.LinearSVC`) como segundo candidato a comparar em
validação cruzada.

**Por que Regressão Logística é adequada para este problema:**
- O problema formalizado na Seção 12 do `eda/eda_tp3.ipynb` é uma **classificação multiclasse**
  (5 classes de intenção: `Technical issue`, `Billing inquiry`, `Cancellation request`,
  `Refund request`, `Product inquiry`), com `y = Ticket Type` nominal e sem ordem — exatamente o
  cenário em que a Regressão Logística multinomial (softmax) se aplica diretamente, retornando uma
  distribuição de probabilidade sobre as classes (útil para expor `confidence` na resposta da API,
  como já simulado em `fastapi/routes/predict.py`).
- É um modelo **linear, rápido de treinar e de inferir**, adequado ao volume do dataset (3.000
  tickets) e a um espaço de atributos esparso e de alta dimensionalidade típico de
  bag-of-words/CountVectorizer — cenário onde modelos lineares costumam performar bem e evitar
  overfitting em relação a modelos não lineares mais complexos.
- É **interpretável**: os coeficientes por classe permitem inspecionar quais termos mais
  contribuem para cada intenção, o que ajuda tanto na auditoria do modelo quanto na futura análise
  de robustez contra exemplos adversariais (TP4/TP5).
- Serve como **baseline forte e bem estabelecido** na literatura de classificação de texto antes de
  evoluir para modelos mais complexos (ex.: embeddings + redes neurais) em etapas futuras do
  projeto.

O **SVM linear** é mantido como candidato alternativo a ser comparado empiricamente (métricas de
acurácia/F1 macro, já que as classes são bem balanceadas conforme a Seção 12.3 da EDA) no TP4, pois
também tende a performar bem em espaços de alta dimensionalidade esparsos como os gerados por
CountVectorizer.

---

## 2. Estratégia de representação do texto

**Técnica escolhida: `CountVectorizer` (scikit-learn), conforme exigido pelo enunciado.**

**Por que CountVectorizer:**
- Transforma cada descrição de ticket em um vetor de contagens de termos (bag-of-words), produzindo
  uma matriz esparsa de atributos numéricos compatível com `LogisticRegression`/`LinearSVC`.
- É **simples, determinístico e rápido** de ajustar e aplicar, adequado como primeira
  vetorização antes de explorar alternativas mais sofisticadas (TF-IDF, embeddings) em iterações
  futuras — e é exatamente a técnica indicada no enunciado do TP3 para este marco do projeto.
- Os dados textuais do dataset (`Ticket Description`) são relativamente curtos e objetivos (em
  média ~19-20 palavras, ver Seção 11 da EDA), o que favorece uma representação de contagem simples
  sem perda excessiva de sinal discriminativo entre as 5 classes de intenção.
- Parâmetros a calibrar no TP4: `ngram_range` (unigrama + bigrama para capturar expressões como
  "não funciona"), `max_features` (limitar dimensionalidade) e `stop_words` (remoção de termos sem
  valor discriminativo).

---

## 3. Alvo do teste adversarial (TP4/TP5)

```
ALVO_PENTEST_ADVERSARIAL = "URL_DO_COLEGA_A_DEFINIR — pendente de pareamento com outro grupo/aluno para pentest adversarial no TP4"
```

**Situação atual:** este é um **placeholder explícito**. Até o momento desta entrega (TP3), não
existe um colega/grupo real definido como par para o pentest adversarial cruzado previsto no
enunciado do TP4/TP5. Assim que o pareamento for definido pelo professor/coordenação, este
documento deve ser atualizado substituindo o placeholder acima pela URL ou endereço IP real e
autorizado da API do colega que será atacada, e pela URL da própria API deste grupo (ex.:
`http://<host>:8010`) a ser informada ao colega correspondente como alvo autorizado.

**Observação de segurança:** nenhum teste adversarial deve ser executado contra qualquer alvo até
que a autorização explícita de pareamento esteja documentada aqui e confirmada por ambas as partes.
