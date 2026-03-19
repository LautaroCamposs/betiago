import discord
from discord.ext import commands
from discord import app_commands
import os
from flask import Flask
from threading import Thread

# ==========================================
# 1. CONFIGURACIÓN DEL SERVIDOR FLASK (WEB)
# ==========================================
app = Flask(__name__)

@app.route('/')
def home():
    return "¡BETIAGO online! Modo texto libre activado. ✍️"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    server = Thread(target=run_flask)
    server.start()

# ==========================================
# 2. CONFIGURACIÓN DEL BOT DE DISCORD
# ==========================================
class BetiagoBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True  
        intents.members = True          
        super().__init__(command_prefix='!', intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print("Comandos de barra (/) sincronizados.")

bot = BetiagoBot()

# --- DATOS DE LAS CUOTAS ---
cuotas_regulares = {
    "Encares": {1: 1.5, 2: 1.6, 3: 2.5},
    "Besos Pico": {1: 1.5, 2: 3.0, 3: 6.0},
    "Besos Chape": {1: 2.0, 2: 6.0, 3: 17.0},
    "Bailes": {1: 1.1, 2: 1.3, 3: 2.0},
    "Instagrams": {1: 1.2, 2: 2.0, 3: 5.0},
    "Asistencias": {1: 1.1, 2: 1.3, 3: 1.7}
}

cuotas_especiales = {
    "1 After McDonald's": 12, 
    "1 Previa Conseguida": 10, 
    "2 Previas Conseguidas": 40,
    "1 After Departamento": 50, 
    "2 Afters Departamento": 400, 
    "1 Infidelidad": 500
}

# --- ESTADO Y MEMORIA ---
apuestas_abiertas = True 
jugadores_anotados = set() 
apuestas_registradas = [] 

@bot.event
async def on_ready():
    print(f'¡Bot {bot.user} conectado!')

# ==========================================
# 3. COMANDOS CON BARRA (SLASH COMMANDS)
# ==========================================

@bot.tree.command(name="betiago", description="Muestra la pizarra completa de cuotas")
async def betiago(interaction: discord.Interaction):
    def fmt(n): return f"{n:g}" 
    mensaje = "**🏆 PIZARRA OFICIAL BETIAGO 🏆**\n\n**Mercados por cantidad (1 / 2 / 3):**\n"
    for categoria, valores in cuotas_regulares.items():
        c1, c2, c3 = f"x{fmt(valores[1])}", f"x{fmt(valores[2])}", f"x{fmt(valores[3])}"
        if categoria == "Encares": c1 = f"**{c1}** 🚀" 
        mensaje += f"🔸 **{categoria}:** {c1} | {c2} | {c3}\n"
    mensaje += "\n**🚨 Mercados Especiales y Exóticos:**\n"
    for evento, cuota in cuotas_especiales.items():
        mensaje += f"🔥 **{evento}:** x{fmt(cuota)}\n"
    estado = "🟢 ABIERTAS" if apuestas_abiertas else "🔴 CERRADAS"
    mensaje += f"\n**ESTADO DE APUESTAS:** {estado}"
    await interaction.response.send_message(mensaje)

@bot.tree.command(name="jugar", description="Anotate en la mesa para participar")
async def jugar(interaction: discord.Interaction):
    jugadores_anotados.add(interaction.user)
    await interaction.response.send_message(f"✅ ¡Ya estás en la mesa, {interaction.user.display_name}! Usá `/apostar` para mandar tu jugada secreta.", ephemeral=True)
    await interaction.channel.send(f"🎲 Alguien se acaba de sentar en la mesa de apuestas...")

@bot.tree.command(name="apostar", description="Registra una jugada secreta (¡Nadie más la verá!)")
@app_commands.describe(jugada="¿Qué va a pasar?", nombre_sujeto="Nombre de quién va a hacer la acción (Escribí lo que quieras)")
async def apostar(interaction: discord.Interaction, jugada: str, nombre_sujeto: str = None):
    if not apuestas_abiertas:
        await interaction.response.send_message("❌ El mercado está cerrado.", ephemeral=True)
        return
    
    # Si no pone nombre, el sujeto es el mismo apostador
    sujeto = nombre_sujeto if nombre_sujeto else interaction.user.display_name
    
    apuestas_registradas.append({
        "apostador": interaction.user.mention,
        "sujeto": sujeto,
        "jugada": jugada
    })
    
    # Confirmación efímera (solo para el usuario)
    await interaction.response.send_message(
        f"🎰 **¡Apuesta Guardada!**\nSujeto: **{sujeto}**\nTu jugada: *{jugada}*\n\n🤫 Nadie más en el servidor puede ver este mensaje.", 
        ephemeral=True
    )

@bot.tree.command(name="ver_mesa", description="Muestra las apuestas de la noche de forma anónima")
async def ver_mesa(interaction: discord.Interaction):
    if not apuestas_registradas:
        await interaction.response.send_message("🕸️ La mesa está vacía.")
        return

    mensaje = "**📝 TICKETS ANÓNIMOS DE LA NOCHE 📝**\n\n"
    for a in apuestas_registradas:
        # Si el nombre del sujeto coincide con el del apostador (lo guardamos como mention pero comparamos)
        # Para simplificar el anonimato total:
        mensaje += f"🔥 **Alguien apostó que [{a['sujeto']}] hará:** {a['jugada']}\n"
    
    await interaction.response.send_message(mensaje)

@bot.tree.command(name="liquidar", description="REVELA quién apostó por quién")
@app_commands.describe(resultados="Resumen de lo que pasó realmente")
async def liquidar(interaction: discord.Interaction, resultados: str):
    if not apuestas_registradas:
        await interaction.response.send_message("⚠️ No hay nada que liquidar.")
        return

    mensaje = "⚖️ **¡EL VEREDICTO FINAL!** ⚖️\n\n"
    mensaje += f"🚨 **RESULTADOS:** *{resultados}*\n\n"
    mensaje += "**Destapando las cartas:**\n"
    
    for a in apuestas_registradas:
        mensaje += f"👤 **{a['apostador']}** le jugó fichas a **{a['sujeto']}**: {a['jugada']}\n"
        
    apuestas_registradas.clear()
    jugadores_anotados.clear()
    await interaction.response.send_message(mensaje)

@bot.tree.command(name="cerrar", description="Cierra el mercado")
async def cerrar(interaction: discord.Interaction):
    global apuestas_abiertas
    apuestas_abiertas = False
    await interaction.response.send_message("🚨 **¡MERCADO CERRADO! No va más.**")

@bot.tree.command(name="abrir", description="Abre el mercado")
async def abrir(interaction: discord.Interaction):
    global apuestas_abiertas
    apuestas_abiertas = True
    await interaction.response.send_message("✅ **Mercado abierto.**")

# ==========================================
# 4. EJECUCIÓN
# ==========================================
if __name__ == '__main__':
    keep_alive()
    TOKEN = os.environ.get("DISCORD_TOKEN")
    if TOKEN:
        bot.run(TOKEN)