# InfraWatch — Middleware Distribuído para Monitoramento de Infraestrutura

O **InfraWatch** é um projeto acadêmico desenvolvido para a disciplina de Middleware Distribuído, com o objetivo de construir uma solução de monitoramento de infraestrutura utilizando comunicação entre serviços independentes.

A aplicação pretende simular o monitoramento de servidores, coletando métricas como uso de CPU, memória RAM e disponibilidade. A partir dessas informações, o sistema deverá identificar condições anormais e gerar alertas.

O projeto será desenvolvido em Python, utilizando uma arquitetura distribuída baseada em microsserviços, comunicação síncrona e assíncrona e execução em containers Docker.

## Objetivos

- Desenvolver um middleware próprio para intermediar a comunicação entre serviços.
- Implementar comunicação síncrona por meio de APIs REST.
- Implementar comunicação assíncrona utilizando mensageria.
- Monitorar métricas de infraestrutura.
- Detectar situações que ultrapassem limites previamente definidos.
- Implementar mecanismos de resiliência e tolerância a falhas.
- Aplicar autenticação e controle de acesso.
- Implementar observabilidade por meio de logs, métricas e identificadores de correlação.

## Arquitetura planejada

A solução será organizada em serviços independentes, que se comunicarão por meio do middleware e de um sistema de mensageria.

```text
             Simulador de Servidores
                      |
                      v
             Middleware InfraWatch
                      |
              Comunicação REST
                      |
                      v
              Monitoring Service
                      |
               Eventos de alerta
                      |
                      v
                  RabbitMQ
                      |
                      v
                Alert Service
```

### Componentes

| Componente | Responsabilidade |
|---|---|
| Simulador | Gerar métricas fictícias de servidores. |
| Middleware | Intermediar a comunicação, autenticar requisições, aplicar políticas de resiliência e registrar informações. |
| Monitoring Service | Receber e analisar as métricas de infraestrutura. |
| RabbitMQ | Gerenciar a comunicação assíncrona por meio de filas. |
| Alert Service | Consumir eventos e registrar alertas identificados. |

## Tecnologias

- **Python 3.11** — linguagem principal.
- **FastAPI** — desenvolvimento das APIs REST.
- **RabbitMQ** — mensageria e comunicação assíncrona.
- **Docker** — conteinerização dos serviços.
- **Docker Compose** — gerenciamento do ambiente distribuído.
- **Git e GitHub** — versionamento e documentação.

## Funcionalidades previstas

- [ ] Simulação de servidores e geração de métricas.
- [ ] Recebimento e processamento de métricas de CPU, RAM e disponibilidade.
- [ ] Comunicação síncrona entre serviços via REST.
- [ ] Comunicação assíncrona utilizando RabbitMQ.
- [ ] Identificação de métricas que ultrapassem limites definidos.
- [ ] Geração e processamento de alertas.
- [ ] Autenticação por token ou API Key.
- [ ] Controle de acesso baseado em papéis (RBAC).
- [ ] Implementação de mecanismos de resiliência, como retry e timeout.
- [ ] Logs estruturados e métricas básicas.
- [ ] Propagação de Correlation ID entre os serviços.
- [ ] Documentação de estratégias de tolerância a falhas.
- [ ] Inicialização do ambiente completo utilizando Docker Compose.

## Execução

O objetivo é permitir que todo o ambiente seja iniciado com um único comando:

```bash
docker compose up --build
```

As instruções completas de instalação e execução serão adicionadas conforme a implementação dos serviços.

## Estrutura planejada do projeto

```text
InfraWatch/
├── middleware/
├── monitoring-service/
├── alert-service/
├── simulator/
├── docker-compose.yml
├── README.md
└── docs/
    └── architecture/
```

## Contexto acadêmico

Projeto desenvolvido em grupo para a disciplina de **Middleware Distribuído**, do curso de Ciência da Computação da Universidade Católica de Pernambuco (UNICAP).

**Professor:** Pedro Ximenes  
**Ano:** 2026

---

*Este repositório documenta o desenvolvimento do InfraWatch, desde a definição da arquitetura até a implementação e validação da solução distribuída.*
