import discord
from discord.ext import commands
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
    # Render asigna un puerto dinámico, por defecto usamos 8080 si no lo encuentra
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    # Iniciamos Flask en un hilo separado para que no bloquee al bot
    server = Thread(target=run_flask)
    server.start()

# ==========================================
# 2. CONFIGURACIÓN DEL BOT DE DISCORD
# ==========================================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# --- DATOS DE LAS CUOTAS ---
cuotas_regulares = {
    "Encares": {1: 1.50, 2: 1.60, 3: 2.50},
    "Besos Pico": {1: 1.50, 2: 3.00, 3: 6.00},
    "Besos Chape": {1: 2.00, 2: 6.00, 3: 17.00},
    "Bailes": {1: 1.10, 2: 1.30, 3: 2.00},
    "Instagrams": {1: 1.20, 2: 2.00, 3: 5.00},
    "Asistencias": {1: 1.10, 2: 1.30, 3: 1.70}
}

cuotas_especiales = {
    "1 After McDonald's": 12.00,
    "1 Previa Conseguida": 10.00,
    "2 Previas Conseguidas": 40.00,
    "1 After Departamento": 50.00,
    "2 Afters Departamento": 400.00,
    "1 Infidelidad": 500.00
}

apuestas_abiertas = True 

@bot.event
async def on_ready():
    print(f'¡Bot {bot.user} conectado y recibiendo apuestas!')

@bot.command()
async def betiago(ctx):
    """Envía la pizarra completa al canal de Discord"""
    mensaje = "**🏆 PIZARRA OFICIAL BETIAGO 🏆**\n\n"
    mensaje += "**Mercados (x1 / x2 / x3):**\n"
    for categoria, valores in cuotas_regulares.items():
        c1, c2, c3 = f"{valores[1]:.2f}", f"{valores[2]:.2f}", f"{valores[3]:.2f}"
        if categoria == "Encares":
            c1 = f"**{c1}** 🚀" 
        mensaje += f"🔸 **{categoria}:** {c1} | {c2} | {c3}\n"
        
    mensaje += "\n**🚨 Mercados Especiales y Exóticos:**\n"
    for evento, cuota in cuotas_especiales.items():
        mensaje += f"🔥 **{evento}:** {cuota:.2f}\n"
        
    estado = "🟢 ABIERTAS" if apuestas_abiertas else "🔴 CERRADAS"
    mensaje += f"\n**ESTADO DE APUESTAS:** {estado}"
    
    await ctx.send(mensaje)

@bot.command()
async def cerrar(ctx):
    """Cierra el mercado de apuestas"""
    global apuestas_abiertas
    if not apuestas_abiertas:
        await ctx.send("⚠️ Las apuestas ya estaban cerradas.")
        return
    apuestas_abiertas = False
    await ctx.send("🚨 **¡ATENCIÓN! EL MERCADO BETIAGO ESTÁ CERRADO** 🚨\nYa no se aceptan más jugadas.")

@bot.command()
async def abrir(ctx):
    """Vuelve a abrir el mercado de apuestas"""
    global apuestas_abiertas
    if apuestas_abiertas:
        await ctx.send("⚠️ Las apuestas ya están abiertas.")
        return
    apuestas_abiertas = True
    await ctx.send("✅ **¡EL MERCADO BETIAGO VUELVE A ESTAR ABIERTO!** ✅\nHagan sus jugadas.")

@bot.command()
async def apostar(ctx, *, jugada: str):
    """Registra una apuesta si el mercado está abierto"""
    if not apuestas_abiertas:
        await ctx.send(f"❌ Lo siento {ctx.author.mention}, las apuestas están cerradas. ¡Llegaste tarde!")
        return
    await ctx.send(f"💸 Apuesta registrada para {ctx.author.mention}: **{jugada}**")

# ==========================================
# 3. EJECUCIÓN DEL PROGRAMA
# ==========================================
if __name__ == '__main__':
    # Arranca el servidor web
    keep_alive()
    
    # Arranca el bot de Discord obteniendo el token desde Render
    TOKEN = os.environ.get("DISCORD_TOKEN")
    
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("ERROR: No se encontró la variable DISCORD_TOKEN. Asegurate de configurarla en Render.")