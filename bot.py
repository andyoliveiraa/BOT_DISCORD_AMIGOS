import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

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

# Emojis for each status
STATUS_EMOJIS = {
    discord.Status.online: "🟢 **Online**",
    discord.Status.idle: "🌙 **Ausente (Idle)**",
    discord.Status.dnd: "⛔ **Não Perturbar (DND)**",
    discord.Status.offline: "⚫ **Invisível / Offline**",
}

def get_status_label(status):
    return STATUS_EMOJIS.get(status, f"❓ **{status}**")

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
            print(f"  - {member.name} ({status_label})")
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

    msg = f"👤 {after.mention} ({after.name}) alterou o estado:\nDe {before_str} para {after_str}."
    
    try:
        await channel.send(msg)
        print(f"[Presença] {after.name} mudou de {before.status} para {after.status} (Notificado).")
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

    msg = f"❌ **{member.name}** ({member.mention}) saiu do servidor."
    
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
