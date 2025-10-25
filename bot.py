import discord
from discord.ext import commands
import json
import datetime
import random
import os
from PIL import Image, ImageDraw, ImageFont

# === Configuration du bot ===
TOKEN = os.getenv("TOKEN")
GUILD_ID = 1431288504801034344   # Remplace par l'ID de ton serveur
ID_MEMBERS = 1431321479169052872 # Remplace par l'ID du salon id-members
CHANNEL_VALIDATION = 1431718911577030666 # ID du salon de validation

# === IDs des rôles ===
ROLE_NON_VALIDE_ID = 1431379022972981439  # ID du rôle Non Validé
ROLE_MEMBRE_ID = 1431289431280717824     # ID du rôle Membre
ROLE_FOUNDER_ID = 1431289065096876183         # Remplace par l'ID du rôle Founder

# === Code secret pour Founder ===
SECRET_FOUNDER_CODE = "hesoyam"

# === Intents requis pour lire les membres et les messages ===
intents = discord.Intents.default()
intents.members = True            # Pour on_member_join
intents.message_content = True    # Pour lire le contenu des messages

bot = commands.Bot(command_prefix="!", intents=intents)

# === Fonction pour créer la carte d'identité ===
BG_IMAGE_PATH = "bg_id.png"  # ← Remplace "bg_id.png" par le nom de ton fichier de fond
def create_id_card(member_name, cpm_name, member_id, join_date, unique_code, role="GRAUE ZONE MEMBER"):
    image = Image.open(BG_IMAGE_PATH).convert("RGBA")
    draw = ImageDraw.Draw(image)
    font_title = ImageFont.truetype("arial.ttf", 32)
    font_text = ImageFont.truetype("arial.ttf", 20)
    color = (255, 255, 255, 255)

    # === Texte principal ===
    draw.text((40, 40), "GRAUE ZONE ID CARD", font=font_title, fill=color)
    draw.text((40, 100), f"Nom Discord : {member_name}", font=font_text, fill=color)
    draw.text((40, 140), f"Nom CPM : {cpm_name}", font=font_text, fill=color)
    draw.text((40, 180), f"ID Membre : {member_id}", font=font_text, fill=color)
    draw.text((40, 220), "Famille : GRAUE ZONE", font=font_text, fill=color)
    draw.text((40, 260), f"Date Entrée : {join_date}", font=font_text, fill=color)
    draw.text((40, 300), f"Code Unique : {unique_code}", font=font_text, fill=color)
    draw.text((40, 340), f"Rôle : {role}", font=font_text, fill=color)

    # === Tampon principal GRAUE ZONE ===
    tampon = Image.new("RGBA", (150, 150), (0, 0, 0, 0))
    d = ImageDraw.Draw(tampon)
    d.ellipse((0, 0, 150, 150), outline=(255, 255, 255, 200), width=4)
    d.text((30, 50), "GRAUE\nZONE", fill=(255, 255, 255, 230),
           font=ImageFont.truetype("arial.ttf", 22), align="center")

    # === Tampon secondaire : ID unique ===
    tampon_id = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    d2 = ImageDraw.Draw(tampon_id)
    d2.ellipse((0, 0, 100, 100), outline=(255, 255, 255, 180), width=3)
    d2.text((20, 35), unique_code, fill=(255, 255, 255, 220),
            font=ImageFont.truetype("arial.ttf", 16))

    # === Placement sur la carte ===
    w, h = image.size
    image.paste(tampon, (int(w/2 - 75), int(h - 160)), tampon)      # grand tampon centré en bas
    image.paste(tampon_id, (int(w - 130), int(h - 120)), tampon_id) # petit tampon à droite

    # === Sauvegarde finale ===
    output_path = f"id_{member_id}.png"
    image.save(output_path)
    return output_path

# === Quand le bot est prêt ===
@bot.event
async def on_ready():
    print(f"[✅] Connecté en tant que {bot.user}")

# === Quand un membre rejoint ===
@bot.event
async def on_member_join(member):
    if member.guild.id != GUILD_ID:
        return

    role_non_valide = member.guild.get_role(ROLE_NON_VALIDE_ID)
    if role_non_valide:
        await member.add_roles(role_non_valide)
        print(f"[🔒] Rôle Non Validé ajouté à {member.name}")

    # Envoyer le message dans le salon id-members
    channel = bot.get_channel(ID_MEMBERS)
    if channel:
        await channel.send(
            f"👋 Bienvenue {member.mention} !\n"
            "Avant de rejoindre la famille, réponds à ces questions dans ce salon :\n"
            "1️⃣ Quel est ton pseudo sur CPM ?\n"
            "2️⃣ Depuis combien de temps tu joues ?\n"
            "3️⃣ Est-ce que tu respecteras les règles ? (Oui/Non)"
        )

# === Gestion des réponses dans le salon id-members avec code secret ===
@bot.event
async def on_message(message):
    if message.author == bot.user or message.channel.id != ID_MEMBERS:
        return

    member = None
    for guild in bot.guilds:
        m = guild.get_member(message.author.id)
        if m:
            member = m
            break
    if not member:
        return

    with open("members.json", "r") as f:
        data = json.load(f)

    if str(member.id) not in data:
        data[str(member.id)] = {"step": 1}
        await message.channel.send(f"{member.mention}, quel est ton pseudo sur CPM ?")
    else:
        step = data[str(member.id)]["step"]

        if step == 1:
            data[str(member.id)]["cpm_name"] = message.content
            data[str(member.id)]["step"] = 2
            await message.channel.send(f"{member.mention}, depuis combien de temps tu joues ?")

        elif step == 2:
            data[str(member.id)]["experience"] = message.content
            data[str(member.id)]["step"] = 3
            await message.channel.send(f"{member.mention}, est-ce que tu respecteras les règles ? (Oui/Non)")

        elif step == 3:
            answer = message.content.strip()
            guild_obj = bot.get_guild(GUILD_ID)

            # Supprimer le message si c'est le code secret pour Founder
            if answer == SECRET_FOUNDER_CODE:
                await message.delete()

            if answer.lower() == "oui":
                role_name = "GRAUE ZONE MEMBER"
                role_obj = guild_obj.get_role(ROLE_MEMBRE_ID)
                if role_obj:
                    await member.add_roles(role_obj)
                    await message.channel.send("🎉 Tu as reçu le rôle de membre !")

            elif answer == SECRET_FOUNDER_CODE:
                role_name = "GRAUE ZONE FOUNDER"
                role_obj = guild_obj.get_role(ROLE_FOUNDER_ID)
                if role_obj:
                    await member.add_roles(role_obj)
                    await message.channel.send("🎉 Tu as reçu le rôle membre !")

            else:
                role_name = "À définir"
                await message.channel.send("⚠️ Tu as répondu 'Non'. Tu ne recevras pas le rôle de membre tant que tu respectes pas les règles.")

            # Générer la carte d'identité
            cpm_name = data[str(member.id)]["cpm_name"]
            join_date = datetime.datetime.now().strftime("%d/%m/%Y")
            unique_code = f"GZ-{random.randint(1000,9999)}"
            id_image = create_id_card(member.name, cpm_name, member.id, join_date, unique_code, role_name)

            await message.channel.send(f"✅ {member.mention}, voici ta carte d'identité officielle :")
            await message.channel.send(file=discord.File(id_image))

            # Envoyer dans le salon de validation
            channel_validation = bot.get_channel(CHANNEL_VALIDATION)
            if channel_validation:
                embed = discord.Embed(
                    title="🕶️ Nouvelle Carte d'Identité GRAUE ZONE",
                    description=f"**{member.mention}** a complété son inscription.",
                    color=discord.Color.dark_gray()
                )
                embed.add_field(name="Nom CPM", value=cpm_name, inline=False)
                embed.add_field(name="Experience", value=data[str(member.id)]["experience"], inline=False)
                embed.add_field(name="Respect des règles", value=("Oui" if answer.lower()=="oui" else "Founder"), inline=False)
                embed.set_footer(text=f"Code : {unique_code} | Rôle : {role_name}")
                await channel_validation.send(embed=embed)
                await channel_validation.send(file=discord.File(id_image))

            data[str(member.id)]["step"] = "done"

    # Sauvegarder le JSON
    with open("members.json", "w") as f:
        json.dump(data, f, indent=4)

    await bot.process_commands(message)

# === Commande pour poser les questions manuellement ===
@bot.command()
async def start_questions(ctx, member: discord.Member):
    role_non_valide = ctx.guild.get_role(ROLE_NON_VALIDE_ID)
    if role_non_valide and role_non_valide not in member.roles:
        await member.add_roles(role_non_valide)
        await ctx.send(f"[🔒] Rôle Non Validé ajouté à {member.mention}")

    channel = bot.get_channel(ID_MEMBERS)
    if channel:
        await channel.send(
            f"👋 {member.mention}, bienvenue !\n"
            "Avant de rejoindre la famille, réponds à ces questions dans ce salon :\n"
            "1️⃣ Quel est ton pseudo sur CPM ?\n"
            "2️⃣ Depuis combien de temps tu joues ?\n"
            "3️⃣ Est-ce que tu respecteras les règles ? (Oui/Non)"
        )

    with open("members.json", "r") as f:
        data = json.load(f)
    if str(member.id) not in data:
        data[str(member.id)] = {"step": 1}
    with open("members.json", "w") as f:
        json.dump(data, f, indent=4)

# === Lancer le bot ===
bot.run(TOKEN)
