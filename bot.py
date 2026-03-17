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
    return "¡El servidor de BETIAGO está activo y funcionando!"

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
        # Configuramos los intents básicos
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)

    async def setup_hook(self):
        # Esto sincroniza los comandos con barra (/) con Discord
        await self.tree.sync()
        print("Comandos de barra (/) sincronizados.")

bot = BetiagoBot()

# --- DATOS DE LAS CUOTAS Y ESTADO ---
cuotas_regulares = {
    "Encares": {1: 1.50, 2: 1.60, 3: 2.50},
    "Besos Pico": {1: 1.50, 2: 3.00, 3: 6.00},
    "Besos Chape": {1: 2.00, 2: 6.00, 3: 17.00},
    "Bailes": {1: 1.10, 2: 1.30, 3: 2.00},
    "Instagrams": {1: 1.20, 2: 2.00, 3: 5.00},
    "Asistencias": {1: 1.10, 2: 1.30, 3: 1.70}
}
cuotas_especiales = {
    "1 After McDonald's": 12.00, "1 Previa Conseguida": 10.00, "2 Previas Conseguidas": 40.00,
    "1 After Departamento": 50.00, "2 Afters Departamento": 400.00, "1 Infidelidad": 500.00
}

apuestas_abiertas = True 
jugadores_anotados = set() # Aquí guardaremos a los que van a jugar

@bot.event
async def on_ready():
    print(f'¡Bot {bot.user} conectado y recibiendo apuestas!')

# ==========================================
# 3. COMANDOS CON BARRA (SLASH COMMANDS)
# ==========================================

@bot.tree.command(name="betiago", description="Muestra la pizarra completa de cuotas")
async def betiago(interaction: discord.Interaction):
    mensaje = "**🏆 PIZARRA OFICIAL BETIAGO 🏆**\n\n**Mercados (x1 / x2 / x3):**\n"
    for categoria, valores in cuotas_regulares.items():
        c1, c2, c3 = f"{valores[1]:.2f}", f"{valores[2]:.2f}", f"{valores[3]:.2f}"
        if categoria == "Encares": c1 = f"**{c1}** 🚀" 
        mensaje += f"🔸 **{categoria}:** {c1} | {c2} | {c3}\n"
        
    mensaje += "\n**🚨 Mercados Especiales y Exóticos:**\n"
    for evento, cuota in cuotas_especiales.items():
        mensaje += f"🔥 **{evento}:** {cuota:.2f}\n"
        
    estado = "🟢 ABIERTAS" if apuestas_abiertas else "🔴 CERRADAS"
    mensaje += f"\n**ESTADO DE APUESTAS:** {estado}"
    
    await interaction.response.send_message(mensaje)

@bot.tree.command(name="jugar", description="Anotate en la mesa para participar en las apuestas")
async def jugar(interaction: discord.Interaction):
    jugadores_anotados.add(interaction.user)
    await interaction.response.send_message(f"🎲 {interaction.user.mention} se acaba de sentar en la mesa de apuestas.")

@bot.tree.command(name="pedir_apuestas", description="Manda un mensaje privado a todos los anotados pidiendo su jugada")
async def pedir_apuestas(interaction: discord.Interaction):
    if not apuestas_abiertas:
        await interaction.response.send_message("❌ Las apuestas están cerradas. Ábrelas con /abrir primero.")
        return
        
    if not jugadores_anotados:
        await interaction.response.send_message("⚠️ No hay nadie anotado en la mesa. Diles que usen `/jugar` primero.")
        return

    await interaction.response.send_message("📲 Enviando mensajes privados a los jugadores para que armen sus apuestas...")
    
    for jugador in jugadores_anotados:
        try:
            await jugador.send(f"🎰 **¡ES HORA DE APOSTAR!**\nLas cuotas están en la mesa. Pasame por acá tu jugada para esta noche (o andá al servidor y usá `/apostar`).")
        except discord.Forbidden:
            await interaction.channel.send(f"❌ No le pude mandar mensaje privado a {jugador.mention} porque tiene los MDs bloqueados.")

@bot.tree.command(name="apostar", description="Registra tu jugada en el sistema")
@app_commands.describe(jugada="Escribe a qué le vas a apostar")
async def apostar(interaction: discord.Interaction, jugada: str):
    if not apuestas_abiertas:
        await interaction.response.send_message(f"❌ Lo siento {interaction.user.mention}, las apuestas están cerradas. ¡Llegaste tarde!")
        return
    await interaction.response.send_message(f"💸 Apuesta registrada para {interaction.user.mention}: **{jugada}**")

@bot.tree.command(name="cerrar", description="Cierra el mercado de apuestas")
async def cerrar(interaction: discord.Interaction):
    global apuestas_abiertas
    if not apuestas_abiertas:
        await interaction.response.send_message("⚠️ Las apuestas ya estaban cerradas.")
        return
    apuestas_abiertas = False
    await interaction.response.send_message("🚨 **¡ATENCIÓN! EL MERCADO BETIAGO ESTÁ CERRADO** 🚨\nYa no se aceptan más jugadas.")

@bot.tree.command(name="abrir", description="Vuelve a abrir el mercado de apuestas")
async def abrir(interaction: discord.Interaction):
    global apuestas_abiertas
    if apuestas_abiertas:
        await interaction.response.send_message("⚠️ Las apuestas ya están abiertas.")
        return
    apuestas_abiertas = True
    await interaction.response.send_message("✅ **¡EL MERCADO BETIAGO VUELVE A ESTAR ABIERTO!** ✅\nHagan sus jugadas.")

# ==========================================
# 4. EJECUCIÓN DEL PROGRAMA
# ==========================================
if __name__ == '__main__':
    keep_alive()
    TOKEN = os.environ.get("DISCORD_TOKEN")
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("ERROR: No se encontró el TOKEN.")