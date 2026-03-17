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
    return "¡El servidor de BETIAGO está activo y funcionando en DigitalOcean!"

def run_flask():
    # Usamos el puerto 8080 que configuramos en el panel
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
        intents.message_content = True  # ¡Asegurate de activar esto en el Developer Portal!
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
apuestas_registradas = {} # {usuario_mencion: "jugada"}

@bot.event
async def on_ready():
    print(f'¡Bot {bot.user} conectado y recibiendo apuestas!')

# ==========================================
# 3. COMANDOS CON BARRA (SLASH COMMANDS)
# ==========================================

@bot.tree.command(name="betiago", description="Muestra la pizarra completa de cuotas")
async def betiago(interaction: discord.Interaction):
    def fmt(n): return f"{n:g}" # Quita .0 si es entero

    mensaje = "**🏆 PIZARRA OFICIAL BETIAGO 🏆**\n\n"
    mensaje += "**Mercados por cantidad (1 / 2 / 3):**\n"
    
    for categoria, valores in cuotas_regulares.items():
        c1 = f"x{fmt(valores[1])}"
        c2 = f"x{fmt(valores[2])}"
        c3 = f"x{fmt(valores[3])}"
        
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
    await interaction.response.send_message(f"🎲 {interaction.user.mention} se sentó en la mesa. ¡Hagan sus pronósticos!")

@bot.tree.command(name="pedir_apuestas", description="Manda privado a los anotados pidiendo su jugada")
async def pedir_apuestas(interaction: discord.Interaction):
    if not apuestas_abiertas:
        await interaction.response.send_message("❌ Las apuestas están cerradas.")
        return
    if not jugadores_anotados:
        await interaction.response.send_message("⚠️ No hay nadie en la mesa. Usen `/jugar` primero.")
        return

    await interaction.response.send_message("📲 Mandando cobradores a los privados de los jugadores...")
    for jugador in jugadores_anotados:
        try:
            await jugador.send("🎰 **¡DALE QUE CERRAMOS!**\nPasame por acá tu jugada o usá `/apostar` en el servidor.")
        except:
            await interaction.channel.send(f"❌ No pude contactar a {jugador.mention} (MD cerrados).")

@bot.tree.command(name="apostar", description="Registra o cambia tu jugada")
@app_commands.describe(jugada="Escribe tu pronóstico para la noche")
async def apostar(interaction: discord.Interaction, jugada: str):
    if not apuestas_abiertas:
        await interaction.response.send_message(f"❌ {interaction.user.mention}, llegaste tarde. Mercado cerrado.")
        return
    
    apuestas_registradas[interaction.user.mention] = jugada
    await interaction.response.send_message(f"💸 Apuesta registrada para {interaction.user.mention}: **{jugada}**")

@bot.tree.command(name="ver_mesa", description="Muestra todas las apuestas actuales")
async def ver_mesa(interaction: discord.Interaction):
    if not apuestas_registradas:
        await interaction.response.send_message("🕸️ La mesa está vacía.")
        return

    mensaje = "**📝 TICKET OFICIAL DE LA NOCHE 📝**\n\n"
    for jugador, jugada in apuestas_registradas.items():
        mensaje += f"👤 **{jugador}:** {jugada}\n"
    await interaction.response.send_message(mensaje)

@bot.tree.command(name="cerrar", description="Cierra el mercado de apuestas")
async def cerrar(interaction: discord.Interaction):
    global apuestas_abiertas
    apuestas_abiertas = False
    await interaction.response.send_message("🚨 **¡MERCADO CERRADO! No va más.** 🚨")

@bot.tree.command(name="abrir", description="Abre el mercado de apuestas")
async def abrir(interaction: discord.Interaction):
    global apuestas_abiertas
    apuestas_abiertas = True
    await interaction.response.send_message("✅ **Mercado abierto. ¡Hagan sus apuestas!**")

@bot.tree.command(name="liquidar", description="Termina la noche y limpia la mesa")
@app_commands.describe(resultados="Resumen de lo que pasó realmente")
async def liquidar(interaction: discord.Interaction, resultados: str):
    if not apuestas_registradas:
        await interaction.response.send_message("⚠️ No hay nada que liquidar.")
        return

    mensaje = "⚖️ **¡RESULTADOS DE LA NOCHE!** ⚖️\n\n"
    mensaje += f"🚨 **Sucedió:** *{resultados}*\n\n"
    mensaje += "**Pronósticos de la mesa:**\n"
    for jugador, jugada in apuestas_registradas.items():
        mensaje += f"👤 **{jugador}:** {jugada}\n"
        
    # Limpieza
    apuestas_registradas.clear()
    jugadores_anotados.clear()
    
    await interaction.response.send_message(mensaje)

# ==========================================
# 4. EJECUCIÓN
# ==========================================
if __name__ == '__main__':
    keep_alive()
    TOKEN = os.environ.get("DISCORD_TOKEN")
    if TOKEN:
        bot.run(TOKEN)