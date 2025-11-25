# reminder

*reminder* é um sistema Python projetado para enviar e-mails e mensagens no Telegram com lembretes programados. O sistema utiliza uma base de dados PostgreSQL para armazenar os lembretes e oferece múltiplas opções de envio.

## Para Utilizar

Para que o programa funcione corretamente, é interessante ter um banco de dados PostgreSQL funcionando localmente, seja via Docker ou instalado na sua máquina.

### Configuração do Ambiente

Crie o arquivo `.env` e adicione as variáveis. Preencha de acordo com suas configurações:

```env
# Credenciais SMTP
PASSWORD=""
EMAIL=""

# Credenciais banco de dados
DATABASE=""
DB_USER=""
DB_PASSWORD=""
DB_CONTAINER=""
HOST="localhost"
PORT="5433"

# Credenciais Telegram
BOT_TOKEN=""
CHAT_ID=""
```

### Usando Docker (Opcional)

Caso prefira utilizar Docker, segue um exemplo de `compose.yml`:

```yml
services:
  home-db:
    image: postgres:13
    environment:
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5433:5432"

volumes:
  postgres_data:
```

### Instalação e Execução

Após configurar o banco de dados e o arquivo `.env`, execute os seguintes comandos:

```bash
# Execute um de cada vez para que não ocorram erros
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Após a instalação, o script está funcional. Os comandos disponíveis são:

```bash
# Listar todos os lembretes
python main.py list

# Inserir um novo lembrete
python main.py insert "SEU LEMBRETE AQUI"

# Deletar um lembrete específico pelo ID
python main.py delete ID

# Limpar todos os lembretes
python main.py clear

# Enviar lembretes (opções disponíveis)
python main.py send                    # Envia para E-mail e Telegram
python main.py send mail              # Envia apenas por E-mail
python main.py send telegram          # Envia apenas para Telegram
```

### Opções de Envio

O comando `send` agora oferece três modos de operação:

- **Sem parâmetro**: Envia lembretes tanto por E-mail quanto para Telegram
- **`mail`**: Envia lembretes apenas por E-mail
- **`telegram`**: Envia lembretes apenas para o Telegram

## Link Simbólico (Opcional)

Caso queira criar um comando global para o script, utilize o arquivo `reminder.sh` para criar um link simbólico:

```bash
# Dá permissão de execução ao arquivo
chmod 775 reminder.sh 

# Cria o link simbólico (ajuste o caminho conforme necessário)
sudo ln -s $HOME/Projects/python/send_mail_reminder/reminder.sh /bin/reminder

# Comandos disponíveis via link simbólico
reminder list
reminder insert "SEU LEMBRETE"
reminder delete ID
reminder clear
reminder send
reminder send mail
reminder send telegram
```

## Funcionalidades

- ✅ Armazenamento de lembretes em banco PostgreSQL
- ✅ Envio de e-mails automáticos
- ✅ Envio de mensagens para Telegram
- ✅ Interface de linha de comando intuitiva
- ✅ Opção de enviar para ambos ou apenas um canal
- ✅ Formatação Markdown para mensagens no Telegram

## Dependências

As principais dependências estão listadas no `requirements.txt`:
- `click` - Interface de linha de comando
- `psycopg2` - Conexão com PostgreSQL
- `python-dotenv` - Gerenciamento de variáveis de ambiente
- `requests` - Requisições HTTP para API do Telegram

---

Para dúvidas ou sugestões, entre em contato:
[LinkedIn](https://www.linkedin.com/in/pablodeas/) | [WhatsApp](https://api.whatsapp.com/send?phone=5521966916139)