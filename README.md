# 🤖 BOT_DISCORD_AMIGOS — Rastreador de Presença 🟢

Um bot moderno, rápido e robusto para o Discord escrito em Python (`discord.py`) que monitoriza e notifica a atividade e o estado de presença dos utilizadores no servidor em tempo real. Este projeto também está integrado com as diretrizes e regras do **ECC (Everything Claude Code)** para garantir alta qualidade de código e segurança.

---

## ✨ Funcionalidades Principais

*   🟢 **Notificações em Tempo Real**: Envia mensagens automáticas de forma instantânea para um canal de texto específico assim que um utilizador altera o seu estado:
    *   🟢 **Online**
    *   🌙 **Ausente (Idle)**
    *   ⛔ **Não Perturbar (DND)**
    *   ⚫ **Invisível / Offline**
*   ❌ **Alertas de Saída**: Notifica o canal imediatamente quando um membro sai do servidor.
*   💬 **Comando Slash `/online`**: Lista todos os utilizadores online de forma limpa e organizada dentro do Discord utilizando embeds visuais.
*   💻 **Registo no Terminal**: Apresenta uma tabela/lista no terminal ao iniciar com todos os utilizadores online.

---

## 🛠️ Pré-requisitos

Antes de iniciar, assegure-se de que tem instalado no seu sistema:
*   [Python 3.8+](https://www.python.org/)
*   `pip` (gestor de pacotes do Python)

---

## ⚙️ Configuração Passo a Passo

### 1. Clonar e Instalar as Dependências 📦

Instale as bibliotecas necessárias declaradas no `requirements.txt`:
```bash
pip install -r requirements.txt
```

### 2. Ativar as Intents no Discord Developer Portal 🔓

Para que o bot possa monitorizar a atividade dos utilizadores, precisa de permissões especiais (**Gateway Intents**):
1.  Aceda ao [Discord Developer Portal](https://discord.com/developers/applications).
2.  Selecione a sua aplicação/bot.
3.  Vá ao separador **Bot** no menu lateral esquerdo.
4.  Desça até à secção **Privileged Gateway Intents**.
5.  Ative as seguintes opções:
    *   **Presence Intent** (Necessário para obter atualizações de estado online/offline).
    *   **Server Members Intent** (Necessário para listar membros e detetar quando alguém sai).
6.  Clique em **Save Changes**.

### 3. Configurar as Variáveis de Ambiente 📝

Crie um ficheiro `.env` na raiz do projeto (copiando o modelo de `.env.example`) com as suas credenciais:
```env
DISCORD_TOKEN=O_TEU_TOKEN_AQUI
STATUS_CHANNEL_ID=ID_DO_CANAL_DE_TEXTO_AQUI
```
> ⚠️ **Nota de Segurança**: Nunca partilhe ou faça upload do ficheiro `.env` para repositórios públicos. Ele já está configurado no `.gitignore` para sua segurança.

---

## 🚀 Como Executar o Bot

Com as dependências instaladas e o ficheiro `.env` devidamente preenchido, execute o seguinte comando na raiz do projeto:

```bash
python bot.py
```

Assim que ligar, verá no terminal a confirmação de sincronização dos comandos slash e a lista inicial de membros online.

---

## 📁 Estrutura do Projeto

*   `bot.py`: O código principal do bot com os eventos (`on_presence_update`, `on_member_remove`) e o comando slash `/online`.
*   `.env`: Ficheiro local de chaves privadas (ignorado pelo Git).
*   `.env.example`: Modelo de configuração das chaves de ambiente.
*   `requirements.txt`: Dependências do projeto.
*   `.agents/`: Pasta de configurações e regras do **ECC** para otimização da assistência por inteligência artificial.

---

## 📄 Licença

Este projeto está licenciado sob a licença [MIT](LICENSE).
