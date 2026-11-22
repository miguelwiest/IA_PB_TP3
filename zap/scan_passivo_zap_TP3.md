# Auditoria de Segurança — OWASP ZAP (Scan Passivo) — TP3

## 1. Metodologia

- **Ferramenta:** OWASP ZAP (`zaproxy/zap-stable`), executado via Docker.
- **Tipo de scan:** `zap-baseline.py` — scan **passivo** (spider + análise passiva de tráfego,
  sem ataques ativos), conforme exigido pelo enunciado ("scan passivo da API").
- **Alvo:** API FastAPI rodando localmente em `http://127.0.0.1:8010`
  (`http://host.docker.internal:8010` a partir do container do ZAP, no Docker Desktop/Windows).
- **Comando utilizado:**
  ```bash
  docker run --rm -v "<pasta_zap>":/zap/wrk/:rw zaproxy/zap-stable zap-baseline.py \
    -t http://host.docker.internal:8010 \
    -r zap_report_run1.html \
    -I
  ```
  (`-I` evita que o container retorne código de saída de falha por causa de alertas WARN; a
  análise de severidade é feita manualmente abaixo, como pede o enunciado.)
- **Escopo coberto pelo spider:** rotas públicas alcançáveis sem autenticação a partir da raiz —
  `/`, `/docs` (Swagger UI) e `/openapi.json`. Como o `zap-baseline.py` não foi configurado com um
  script/contexto de autenticação, as rotas protegidas por JWT (`/predict`, `/tickets/{id}`,
  `/auth/me`) não foram exercitadas por requisições autenticadas durante o spider — o que é
  esperado e aceitável para um scan **passivo** sem credenciais, já que o foco aqui é a análise de
  cabeçalhos HTTP, exposição de informação e más configurações da camada de transporte/servidor,
  não um pentest ativo às regras de negócio (esse é o objetivo do TP4/TP5).

## 2. Resultado da 1ª rodada (`zap_report_run1.html`)

```
Total of 3 URLs
FAIL-NEW: 0   FAIL-INPROG: 0   WARN-NEW: 1   WARN-INPROG: 0   INFO: 0   IGNORE: 0   PASS: 61
```

Único alerta reportado:

| Finding (ZAP)                              | Severidade (Risk Level) | Instâncias |
|---------------------------------------------|--------------------------|------------|
| X-Content-Type-Options Header Missing (10021) | **Low**                | 1          |

**Nenhum finding foi classificado como Medium ou High nesta auditoria.** Essa ausência está
documentada explicitamente aqui, conforme exigido pelo enunciado quando não há achados nessas
severidades.

## 3. Análise do finding (mesmo não sendo Medium/High, foi corrigido por boa prática)

- **Finding:** `X-Content-Type-Options Header Missing` (ZAP rule 10021).
- **Severidade:** Low.
- **Por que representa um risco:** sem o cabeçalho `X-Content-Type-Options: nosniff`, navegadores
  mais antigos podem tentar "adivinhar" (MIME-sniffing) o tipo de conteúdo de uma resposta em vez
  de respeitar o `Content-Type` declarado pelo servidor. Isso pode ser explorado para forçar a
  interpretação de uma resposta como HTML/JavaScript executável mesmo quando o servidor pretendia
  servir, por exemplo, JSON — abrindo uma superfície adicional para ataques de Cross-Site Scripting
  (XSS) refletido via content-sniffing.
- **Alteração realizada para corrigir:** middleware HTTP global adicionado em
  `fastapi/main.py` (`add_security_headers`), que injeta `X-Content-Type-Options: nosniff` em
  **todas** as respostas da API. Ver comentário `# ZAP FIX (TP3 - item 5)` no código-fonte,
  imediatamente acima da definição do middleware.
- **Evidência de que o problema não permanece:** 2ª rodada do ZAP (`zap_report_run2.html`), com a
  API já reiniciada e servindo a correção, confirmada via `curl -I http://127.0.0.1:8010/health`
  retornando o cabeçalho `x-content-type-options: nosniff` em toda resposta. Resultado resumido da
  2ª rodada:

```
Total of 3 URLs
PASS: X-Content-Type-Options Header Missing [10021]   <- antes era WARN-NEW, agora PASS
...
FAIL-NEW: 0   FAIL-INPROG: 0   WARN-NEW: 0   WARN-INPROG: 0   INFO: 0   IGNORE: 0   PASS: 62
```

A regra 10021 passou de `WARN-NEW` (1 instância) na 1ª rodada para `PASS` na 2ª rodada, e o total de
regras em `PASS` subiu de 61 para 62, com **zero** alertas `WARN`/`FAIL` restantes. Log completo em
`zap/run1_full.log` e `zap/run2_full.log`.

## 4. Conclusão

A API, no estado em que foi auditada (TP3), **não apresentou nenhum finding Medium ou High** no
scan passivo do OWASP ZAP. O único achado (Low) foi corrigido proativamente e a correção foi
confirmada em uma segunda rodada do mesmo scan. Os relatórios completos (HTML, exportados
diretamente pelo ZAP) estão disponíveis em:
- `zap/zap_report_run1.html` — antes da correção (1 alerta Low).
- `zap/zap_report_run2.html` — depois da correção.
