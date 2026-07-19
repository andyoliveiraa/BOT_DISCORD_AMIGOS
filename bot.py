import os
import discord
import datetime
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from aiohttp import web

# Monkey patch discord.ClientStatus to support embedded/console platform
import discord.presences
from discord.enums import try_enum, Status

class CustomClientStatus:
    def __init__(self, *, status='offline', data=None):
        self._status = status or 'offline'
        data = data or {}
        self.desktop = data.get('desktop')
        self.mobile = data.get('mobile')
        self.web = data.get('web')
        self.embedded = data.get('embedded')

    def __repr__(self):
        attrs = [
            ('_status', self._status),
            ('desktop', self.desktop),
            ('mobile', self.mobile),
            ('web', self.web),
            ('embedded', self.embedded),
        ]
        inner = ' '.join('%s=%r' % t for t in attrs)
        return f'<ClientStatus {inner}>'

    def _update(self, status, data, /):
        self._status = status
        self.desktop = data.get('desktop')
        self.mobile = data.get('mobile')
        self.web = data.get('web')
        self.embedded = data.get('embedded')

    @classmethod
    def _copy(cls, client_status, /):
        self = cls.__new__(cls)
        self._status = client_status._status
        self.desktop = client_status.desktop
        self.mobile = client_status.mobile
        self.web = client_status.web
        self.embedded = getattr(client_status, 'embedded', None)
        return self

    @property
    def status(self):
        return try_enum(Status, self._status)

    @property
    def raw_status(self):
        return self._status

    @property
    def mobile_status(self):
        return try_enum(Status, self.mobile or 'offline')

    @property
    def desktop_status(self):
        return try_enum(Status, self.desktop or 'offline')

    @property
    def web_status(self):
        return try_enum(Status, self.web or 'offline')

    @property
    def embedded_status(self):
        return try_enum(Status, self.embedded or 'offline')

    def is_on_mobile(self):
        return self.mobile is not None

discord.presences.ClientStatus = CustomClientStatus
discord.ClientStatus = CustomClientStatus

def get_member_platforms(member):
    platforms = []
    cs = member.client_status
    if getattr(cs, 'desktop', None) and cs.desktop != 'offline':
        platforms.append('PC')
    if getattr(cs, 'mobile', None) and cs.mobile != 'offline':
        platforms.append('Telemóvel')
    if getattr(cs, 'web', None) and cs.web != 'offline':
        platforms.append('Web')
    if getattr(cs, 'embedded', None) and cs.embedded != 'offline':
        platforms.append('Consola')
    return platforms

def get_member_platforms_dict(member):
    platforms = {}
    cs = member.client_status
    if getattr(cs, 'desktop', None) and cs.desktop != 'offline':
        platforms['desktop'] = str(cs.desktop)
    if getattr(cs, 'mobile', None) and cs.mobile != 'offline':
        platforms['mobile'] = str(cs.mobile)
    if getattr(cs, 'web', None) and cs.web != 'offline':
        platforms['web'] = str(cs.web)
    if getattr(cs, 'embedded', None) and cs.embedded != 'offline':
        platforms['embedded'] = str(cs.embedded)
    return platforms


# Load environment variables from .env file
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID_STR = os.getenv("STATUS_CHANNEL_ID")

if not TOKEN:
    print("Erro: A variável de ambiente DISCORD_TOKEN não está configurada no seu ficheiro .env!")
    exit(1)

if not CHANNEL_ID_STR:
    print("Erro: A variável de ambiente STATUS_CHANNEL_ID não está configurada no seu ficheiro .env!")
    exit(1)

try:
    STATUS_CHANNEL_ID = int(CHANNEL_ID_STR)
except ValueError:
    print("Erro: STATUS_CHANNEL_ID deve ser um número inteiro (ID válido de canal do Discord)!")
    exit(1)

# Configure Gateway Intents
intents = discord.Intents.default()
intents.presences = True  # Required to track status updates (Online, Idle, DND, Offline)
intents.members = True    # Required to fetch members lists and detect leaves
intents.guilds = True

# Initialize Bot
bot = commands.Bot(command_prefix="!", intents=intents)
bot.status_history = []  # Store status change logs in-memory

# Emojis for each status
STATUS_EMOJIS = {
    discord.Status.online: "🟢 **Online**",
    discord.Status.idle: "🌙 **Ausente (Idle)**",
    discord.Status.dnd: "⛔ **Não Perturbar (DND)**",
    discord.Status.offline: "⚫ **Invisível / Offline**",
}

def get_status_label(status):
    return STATUS_EMOJIS.get(status, f"❓ **{status}**")

# Web Server Endpoints & Handlers
async def handle_index(request):
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            html = f.read()
        return web.Response(text=html, content_type='text/html')
    except Exception as e:
        return web.Response(text=f"Erro ao carregar o dashboard: {e}", status=500)

async def handle_api_status(request):
    guilds_data = []
    for guild in bot.guilds:
        members_data = []
        for member in guild.members:
            if member.bot:
                continue
            members_data.append({
                "id": str(member.id),
                "name": member.name,
                "display_name": member.display_name,
                "status": str(member.status),
                "platforms": get_member_platforms_dict(member),
                "avatar_url": str(member.display_avatar.url) if member.display_avatar else None
            })
        guilds_data.append({
            "id": str(guild.id),
            "name": guild.name,
            "member_count": guild.member_count,
            "members": members_data
        })
    
    data = {
        "bot_name": bot.user.name if bot.user else "Bot",
        "bot_id": str(bot.user.id) if bot.user else "",
        "bot_avatar_url": str(bot.user.display_avatar.url) if bot.user and bot.user.display_avatar else "",
        "guilds": guilds_data,
        "history": bot.status_history
    }
    return web.json_response(data)

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_index)
    app.router.add_get('/api/status', handle_api_status)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 3026)
    await site.start()
    print("==================================================")
    print("Dashboard Web online em http://localhost:3026")
    print("==================================================")

# Override Bot.setup_hook to launch the web server inside the event loop
async def setup_hook():
    bot.loop.create_task(start_web_server())

bot.setup_hook = setup_hook

@bot.event
async def on_ready():
    print(f"==================================================")
    print(f"Bot conectado com sucesso!")
    print(f"Nome do Bot: {bot.user.name}")
    print(f"ID do Bot:   {bot.user.id}")
    print(f"==================================================")
    
    # Sync slash commands globally
    try:
        print("A sincronizar comandos slash...")
        synced = await bot.tree.sync()
        print(f"Sincronizados {len(synced)} comando(s) slash.")
    except Exception as e:
        print(f"Erro ao sincronizar comandos: {e}")

    # Chunk guilds to load all members and cache presences from gateway
    print("\nA carregar presenças e membros dos servidores...")
    for guild in bot.guilds:
        try:
            await guild.chunk()
            print(f"✓ Membros de '{guild.name}' carregados com sucesso.")
        except Exception as e:
            print(f"⚠ Erro ao carregar membros de '{guild.name}': {e}")

    # List ALL members (including offline ones) in all connected guilds on console
    print("\n[Lista Completa de Membros nos Servidores]:")
    for guild in bot.guilds:
        print(f"Servidor: {guild.name} (ID: {guild.id})")
        members_count = 0
        for member in guild.members:
            if member.bot:
                continue
            members_count += 1
            status_label = get_status_label(member.status)
            platforms = get_member_platforms(member)
            plat_str = f" [{', '.join(platforms)}]" if platforms else ""
            print(f"  - {member.name} ({status_label}){plat_str}")
        if members_count == 0:
            print("  - Nenhum membro encontrado neste servidor.")
    print(f"==================================================\n")

@bot.event
async def on_presence_update(before: discord.Member, after: discord.Member):
    # Only notify if status changed (Online, Idle, DND, Offline)
    if before.status == after.status:
        return

    # Check if the notification channel exists
    channel = bot.get_channel(STATUS_CHANNEL_ID)
    if not channel:
        try:
            channel = await bot.fetch_channel(STATUS_CHANNEL_ID)
        except Exception as e:
            print(f"Erro ao obter o canal {STATUS_CHANNEL_ID}: {e}")
            return

    before_str = get_status_label(before.status)
    after_str = get_status_label(after.status)

    # Get platforms
    platforms = get_member_platforms(after)
    plat_str = f" (via {', '.join(platforms)})" if platforms and after.status != discord.Status.offline else ""
    msg = f"👤 **{after.display_name}** alterou o estado:\nDe {before_str} para {after_str}{plat_str}."
    
    # Store in-memory status logs for the dashboard
    log_entry = {
        "user_name": after.name,
        "user_id": str(after.id),
        "avatar_url": str(after.display_avatar.url) if after.display_avatar else "",
        "old_status": str(before.status),
        "new_status": str(after.status),
        "platforms": get_member_platforms_dict(after),
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    bot.status_history.append(log_entry)
    if len(bot.status_history) > 100:
        bot.status_history.pop(0)

    try:
        await channel.send(msg)
        print(f"[Presença] {after.name} mudou de {before.status} para {after.status}{plat_str} (Notificado).")
    except Exception as e:
        print(f"Erro ao enviar mensagem de status para o canal: {e}")

@bot.event
async def on_member_remove(member: discord.Member):
    # Notify when someone leaves the server
    channel = bot.get_channel(STATUS_CHANNEL_ID)
    if not channel:
        try:
            channel = await bot.fetch_channel(STATUS_CHANNEL_ID)
        except Exception as e:
            print(f"Erro ao obter o canal {STATUS_CHANNEL_ID} no evento on_member_remove: {e}")
            return

    msg = f"❌ **{member.display_name}** saiu do servidor."
    
    # Store leave update in history log
    log_entry = {
        "user_name": member.name,
        "user_id": str(member.id),
        "avatar_url": str(member.display_avatar.url) if member.display_avatar else "",
        "old_status": "",
        "new_status": "left",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    bot.status_history.append(log_entry)
    if len(bot.status_history) > 100:
        bot.status_history.pop(0)

    try:
        await channel.send(msg)
        print(f"[Saída] {member.name} saiu do servidor (Notificado).")
    except Exception as e:
        print(f"Erro ao enviar mensagem de saída para o canal: {e}")

@bot.tree.command(name="online", description="Lista todos os membros que estão online no servidor de momento.")
async def online_command(interaction: discord.Interaction):
    guild = interaction.guild
    if not guild:
        await interaction.response.send_message("Este comando só pode ser usado dentro de um servidor.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=False)

    online_members = []
    for member in guild.members:
        if member.bot:
            continue
        if member.status != discord.Status.offline:
            online_members.append(member)

    if not online_members:
        await interaction.followup.send("Não há utilizadores online de momento (ou as presenças ainda não foram indexadas).")
        return

    member_lines = []
    for m in online_members:
        status_label = get_status_label(m.status)
        member_lines.append(f"- {m.mention} ({m.name}) - {status_label}")

    # Discord embeds have a 4096 character limit for descriptions, so we chunk if needed
    description = "\n".join(member_lines)
    if len(description) > 4000:
        description = description[:3900] + "\n... (e outros)"

    embed = discord.Embed(
        title=f"🟢 Membros Online de Momento ({len(online_members)})",
        description=description,
        color=discord.Color.green()
    )
    
    await interaction.followup.send(embed=embed)

# Start Bot
if __name__ == "__main__":
    bot.run(TOKEN)
