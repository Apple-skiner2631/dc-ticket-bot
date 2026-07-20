import os
import discord
from discord.ext import commands
from discord import ui
from datetime import datetime

TOKEN = os.getenv("DISCORD_TOKEN")
TICKET_CHANNEL_ID = 1466986768652963983
PENDING_CAT_ID = 1490338802261299312
RESOLVED_CAT_ID = 1490339576689201212

STAFF_ROLE_IDS = [1459696673239470338, 1459700251295223994]

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="$", intents=intents)

class TicketModal(ui.Modal, title="📨 建立工單"):
    event = ui.TextInput(label="原因及事件", placeholder="請簡述您的問題...", max_length=100)
    reason = ui.TextInput(label="詳細說明", style=discord.TextStyle.paragraph, placeholder="請詳細描述事件經過...", max_length=1000)
    proof = ui.TextInput(label="上傳附件連結 (選填)", placeholder="可提供圖片或雲端連結，限10KB以內", required=False, max_length=500)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        category = guild.get_channel(PENDING_CAT_ID)
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        

        for role_id in STAFF_ROLE_IDS:
            staff_role = guild.get_role(role_id)
            if staff_role:
                overwrites[staff_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        
        channel_name = f"ticket-{interaction.user.name}"
        ticket_channel = await guild.create_text_channel(name=channel_name, category=category, overwrites=overwrites)
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        embed = discord.Embed(title=" ✅ 工單已建立\n 請耐心等待管理人員受理!", color=discord.Color.blue())
        embed.description = f"**時間:** {current_time}\n**使用者:** {interaction.user.mention}\n**事件:** {self.event.value}\n**原因:** {self.reason.value}\n**附件證明:** {self.proof.value if self.proof.value else '無'}"
        
        view = TicketControlView()
        await ticket_channel.send(embed=embed, view=view)
        await interaction.followup.send(f"**工單已成功建立：{ticket_channel.mention}**", ephemeral=True)

class TicketLaunchView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="📩 開啟工單", style=discord.ButtonStyle.green, custom_id="launch_ticket")
    async def launch(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(TicketModal())

class TicketControlView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="❌ 關閉工單", style=discord.ButtonStyle.blurple, custom_id="close_ticket")
    async def close(self, interaction: discord.Interaction, button: ui.Button):
        category = interaction.guild.get_channel(RESOLVED_CAT_ID)
        await interaction.channel.edit(category=category)
        
        embed = discord.Embed(title="**📨 工單管理選項**", description="**請選擇後續處理方式：**", color=discord.Color.orange())
        view = TicketPostCloseView()
        await interaction.response.send_message(embed=embed, view=view)

class TicketPostCloseView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="❌ 關閉工單", style=discord.ButtonStyle.secondary, custom_id="opt_close")
    async def opt_close(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message("**⛔工單已保持關閉狀態。**", ephemeral=True)

    @ui.button(label="⛔ 刪除頻道", style=discord.ButtonStyle.danger, custom_id="opt_delete")
    async def opt_delete(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message("**⚠頻道即將在 5 秒後刪除...**")
        await interaction.channel.delete()

    @ui.button(label="📥 匯出對話檔案", style=discord.ButtonStyle.success, custom_id="opt_export")
    async def opt_export(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()
        log_text = ""
        async for message in interaction.channel.history(limit=None, oldest_first=True):
            log_text += f"[{message.created_at.strftime('%Y-%m-%d %H:%M:%S')}] {message.author}: {message.content}\n"
        
        file_path = f"transcript-{interaction.channel.name}.txt"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(log_text)
        
        await interaction.followup.send(file=discord.File(file_path))
        os.remove(file_path)

@bot.event
async def on_ready():
    bot.add_view(TicketLaunchView())
    bot.add_view(TicketControlView())
    bot.add_view(TicketPostCloseView())
    channel = bot.get_channel(TICKET_CHANNEL_ID)
    if channel:
        await channel.purge(limit=10)
        embed = discord.Embed(
            title="📨 票務系統 | Ticket System", 
            description="""歡迎使用支援服務，請點擊下方按鈕以開啟專屬工單。

**⚠️ 開票須知：**
1. 開啟工單前，請務必先詳閱伺服器規範。
2. 進入頻道後請詳細說明事由，**請勿惡意標記 (@) 管理團隊**。
3. 請勿無故濫用票務系統，非必要請勿隨意開票。

*管理團隊將會盡快為您處理，感謝您的配合！*""", 
            color=discord.Color.green()
        )
        await channel.send(embed=embed, view=TicketLaunchView())

@bot.command(name="new")
async def cmd_new(ctx):
    guild = ctx.guild
    category = guild.get_channel(PENDING_CAT_ID)
    
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }
    

    for role_id in STAFF_ROLE_IDS:
        staff_role = guild.get_role(role_id)
        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        
    ticket_channel = await guild.create_text_channel(name=f"ticket-{ctx.author.name}", category=category, overwrites=overwrites)
    
    embed = discord.Embed(title="**工單已建立!**", description=f"📄 歡迎使用工單系統。\n管理團隊將迅速為您服務! \n> **👥使用者:** {ctx.author.mention}", color=discord.Color.blue())
    await ticket_channel.send(embed=embed, view=TicketControlView())
    await ctx.send(f"**已為您開啟工單頻道：{ticket_channel.mention}**")

@bot.command(name="user")
async def cmd_user(ctx, member: discord.Member):
    if "ticket-" in ctx.channel.name:
        await ctx.channel.set_permissions(member, read_messages=True, send_messages=True)
        await ctx.send(f"**✅ 已成功將 {member.mention} 邀請至本工單頻道。**")
    else:
        await ctx.send("**⚠ 此指令只能在工單頻道內使用!**", delete_after=5)

@bot.command(name="close")
async def cmd_close(ctx):
    if "ticket-" in ctx.channel.name:
        embed = discord.Embed(title="**📨 工單管理選項**", description="**請選擇後續處理方式：**", color=discord.Color.orange())
        await ctx.send(embed=embed, view=TicketPostCloseView())
    else:
        await ctx.send("⚠ 此指令只能在工單頻道內使用。", delete_after=5)

import logging
logging.basicConfig(level=logging.INFO)
bot.run(TOKEN)
