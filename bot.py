import os
import json
import random
import discord
from discord.ext import commands
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore

from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# .env ファイルから環境変数を読み込む
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
TEST_GUILD_ID = int(os.getenv("TEST_GUILD_ID", 0))
FIREBASE_KEY_PATH = os.getenv("FIREBASE_KEY_PATH", "serviceAccountKey.json")
FIREBASE_CONFIG_JSON = os.getenv("FIREBASE_CONFIG_JSON")

# ----------------------------------------------------
# Firebase 初期化処理
# ----------------------------------------------------
if FIREBASE_CONFIG_JSON:
    cred_dict = json.loads(FIREBASE_CONFIG_JSON)
    cred = credentials.Certificate(cred_dict)
else:
    cred = credentials.Certificate(FIREBASE_KEY_PATH)

firebase_admin.initialize_app(cred)
db = firestore.client()

# ----------------------------------------------------
# Firestore 読み書き用ヘルパー関数
# ----------------------------------------------------
def get_guild_members(guild_id: int) -> list:
    doc_ref = db.collection("splatoon_sets").document(str(guild_id))
    doc = doc_ref.get()
    if doc.exists:
        data = doc.to_dict()
        return data.get("members", [])
    return []

def add_guild_member(guild_id: int, member_name: str):
    members = get_guild_members(guild_id)
    if member_name not in members:
        members.append(member_name)
        db.collection("splatoon_sets").document(str(guild_id)).set({"members": members})

def remove_guild_member(guild_id: int, member_name: str):
    members = get_guild_members(guild_id)
    if member_name in members:
        members.remove(member_name)
        db.collection("splatoon_sets").document(str(guild_id)).set({"members": members})

def reset_guild_members(guild_id: int):
    db.collection("splatoon_sets").document(str(guild_id)).set({"members": []})

# ----------------------------------------------------
# スプラトゥーン ブキデータ
# ----------------------------------------------------
WEAPONS = [
    'ボールドマーカー',
    'ボールドマーカーネオ',
    'スプラシューター',
    'ヒーローシューター',
    'スプラシューターコラボ',
    'オクタシューター',
    'スプラシューター煌',
    'わかばシューター',
    'もみじシューター',
    'シャープマーカー',
    'シャープマーカーネオ',
    'シャープマーカーGECK',
    '.52ガロン',
    '.52ガロンデコ',
    '.96ガロン',
    '.96ガロンデコ',
    '.96ガロン爪',
    'H3リールガン',
    'H3リールガンD',
    'H3リールガンSNAK',
    'L3リールガン',
    'L3リールガンD',
    'L3リールガン箔',
    'N-ZAP85',
    'N-ZAP89',
    'プロモデラーMG',
    'プロモデラーRG',
    'プロモデラー彩',
    'スペースシューター',
    'スペースシューターコラボ',
    'ジェットスイーパー',
    'ジェットスイーパーカスタム',
    'ジェットスイーパーCOBR',
    'プライムシューター',
    'プライムシューターコラボ',
    'プライムシューターFRZN',
    'スプラローラー',
    'スプラローラーコラボ',
    'カーボンローラー',
    'カーボンローラーデコ',
    'カーボンローラーANGL',
    'ワイドローラー',
    'ワイドローラーコラボ',
    'ワイドローラー惑',
    'ヴァリアブルローラー',
    'ヴァリアブルローラーフォイル',
    'ダイナモローラー',
    'ダイナモローラーテスラ',
    'ダイナモローラー冥',
    'スプラチャージャー',
    'スプラチャージャーコラボ',
    'スプラチャージャーFRST',
    'スプラスコープ',
    'スプラスコープコラボ',
    'スプラスコープFRST',
    'スクイックリンα',
    'スクイックリンβ',
    'ソイチューバー',
    'ソイチューバーカスタム',
    '14式竹筒銃・甲',
    '14式竹筒銃・乙',
    'R-PEN/5H',
    'R-PEN/5B',
    'リッター4K',
    'リッター4Kカスタム',
    '4Kスコープ',
    '4Kスコープカスタム',
    'ヒッセン',
    'ヒッセン・ヒュー',
    'ヒッセンASH',
    'バケットスロッシャー',
    'バケットスロッシャーデコ',
    'スクリュースロッシャー',
    'スクリュースロッシャーネオ',
    'エクスプロッシャー',
    'エクスプロッシャーカスタム',
    'オーバーフロッシャー',
    'オーバーフロッシャーデコ',
    'モップリン',
    'モップリンD',
    'モップリン角',
    'スプラスピナー',
    'スプラスピナーコラボ',
    'スプラスピナーPYTN',
    'ノーチラス47',
    'ノーチラス79',
    'イグザミナー',
    'イグザミナー・ヒュー',
    'バレルスピナー',
    'バレルスピナーデコ',
    'クーゲルシュライバー',
    'クーゲルシュライバー・ヒュー',
    'ハイドラント',
    'ハイドラントカスタム',
    'ハイドラント圧',
    'スプラマニューバー',
    'スプラマニューバーコラボ',
    'スプラマニューバー耀',
    'スパッタリー',
    'スパッタリー・ヒュー',
    'スパッタリーOWL',
    'クアッドホッパーブラック',
    'クアッドホッパーホワイト',
    'デュアルスイーパー',
    'デュアルスイーパーカスタム',
    'デュアルスイーパー蹄',
    'ケルビン525',
    'ケルビン525デコ',
    'ガエンFF',
    'ガエンFFカスタム',
    'ノヴァブラスター',
    'ノヴァブラスターネオ',
    'クラッシュブラスター',
    'クラッシュブラスターネオ',
    'ホットブラスター',
    'ホットブラスターカスタム',
    'ホットブラスター艷',
    'ロングブラスター',
    'ロングブラスターカスタム',
    'S-BLAST92',
    'S-BLAST91',
    'ラピッドブラスター',
    'ラピッドブラスターデコ',
    'Rブラスターエリート',
    'Rブラスターエリートデコ',
    'RブラスターエリートWNTR',
    'パラシェルター',
    'パラシェルターソレーラ',
    'スパイガジェット',
    'スパイガジェットソレーラ',
    'スパイガジェット繚',
    'キャンピングシェルター',
    'キャンピングシェルターソレーラ',
    'キャンピングシェルターCREM',
    '24式張替傘・甲',
    '24式張替傘・乙',
    'トライストリンガー',
    'トライストリンガーコラボ',
    'トライストリンガー燈',
    'LACT-450',
    'LACT-450デコ',
    'LACT-450MILK',
    'フルイドV',
    'フルイドVカスタム',
    'パブロ',
    'パブロ・ヒュー',
    'ホクサイ',
    'ホクサイ・ヒュー',
    'ホクサイ彗',
    'フィンセント',
    'フィンセント・ヒュー',
    'フィンセントBRNZ',
    'ドライブワイパー',
    'ドライブワイパーデコ',
    'ドライブワイパーRUST',
    'ジムワイパー',
    'ジムワイパー・ヒュー',
    'ジムワイパー封',
    'デンタルワイパーミント',
    'デンタルワイパースミ'
]

# ----------------------------------------------------
# Bot インテント設定
# ----------------------------------------------------
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# ----------------------------------------------------
# UI コンポーネント定義
# ----------------------------------------------------

# ① ガチャ結果の下に出る「もう一度ガチャを引く」ボタン
class GachaRetryView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="もう一度ガチャを引く", style=discord.ButtonStyle.primary, emoji="🎲")
    async def retry_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_id = interaction.guild_id
        members = get_guild_members(guild_id)

        if not members:
            return await interaction.response.send_message(
                "メンバーが登録されていません！「ニックネーム登録」から登録してください。", 
                ephemeral=True
            )

        results = [f"**{m}**: {random.choice(WEAPONS)}" for m in members]
        embed = discord.Embed(title="🦑 ブキ抽選結果 🦑", description="\n".join(results), color=discord.Color.green())
        await interaction.response.send_message(embed=embed, view=GachaRetryView())


# ② 「確認」ボタンを押したときに表示されるドロップダウン付きView（本人だけに表示）
class MemberSelectView(discord.ui.View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=180)
        self.guild_id = guild_id
        
        members = get_guild_members(guild_id)
        options = []

        if members:
            for m in members:
                options.append(discord.SelectOption(label=m, description="選択するとメンバーから削除します", emoji="👤"))
        else:
            options.append(discord.SelectOption(label="登録メンバーなし", description="ニックネームを登録してね", value="none", emoji="❌"))

        self.select_menu = discord.ui.Select(
            placeholder=f"現在のメンバー（{len(members)}名）/ 選択で削除",
            options=options,
            disabled=(len(members) == 0)
        )
        self.select_menu.callback = self.select_callback
        self.add_item(self.select_menu)

    async def select_callback(self, interaction: discord.Interaction):
        selected_member = self.select_menu.values[0]
        guild_id = interaction.guild_id

        remove_guild_member(guild_id, selected_member)
        
        # 削除された状態の新しいドロップダウンで画面を更新
        new_view = MemberSelectView(guild_id)
        members = get_guild_members(guild_id)
        await interaction.response.edit_message(
            content=f"👥 メンバー確認・管理（現在の人数: **{len(members)}名**）\n※リストから選択すると削除できます。",
            view=new_view
        )


# ③ ニックネーム登録モーダル（入力フォーム）
class FeedbackModal(discord.ui.Modal, title="ニックネーム登録"):
    name = discord.ui.TextInput(
        label="ニックネーム",
        placeholder="例: 野上恒",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id
        user_name = self.name.value.strip()

        add_guild_member(guild_id, user_name)
        members = get_guild_members(guild_id)

        await interaction.response.send_message(
            f"「{user_name}」さんを登録しました🦑（現在の登録人数: **{len(members)}名**）",
            ephemeral=True
        )


# ④ メインパネルView（ボタンのみでスッキリ）
class TestView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    # ブキガチャボタン
    @discord.ui.button(label="ブキガチャ", style=discord.ButtonStyle.primary, emoji="🦑", row=0)
    async def primary_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_id = interaction.guild_id
        members = get_guild_members(guild_id)

        if not members:
            return await interaction.response.send_message(
                "メンバーが登録されていません！「ニックネーム登録」から登録してください。", 
                ephemeral=True
            )

        results = [f"**{m}**: {random.choice(WEAPONS)}" for m in members]
        embed = discord.Embed(title="🦑 ブキ抽選結果 🦑", description="\n".join(results), color=discord.Color.blurple())
        await interaction.response.send_message(embed=embed, view=GachaRetryView())

    # ニックネーム登録ボタン
    @discord.ui.button(label="ニックネーム登録", style=discord.ButtonStyle.success, emoji="📝", row=0)
    async def open_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(FeedbackModal())

    # 確認ボタン（押すとドロップダウン画面が出現）
    @discord.ui.button(label="確認", style=discord.ButtonStyle.secondary, emoji="👥", row=0)
    async def confirm_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_id = interaction.guild_id
        members = get_guild_members(guild_id)
        view = MemberSelectView(guild_id)
        await interaction.response.send_message(
            content=f"👥 メンバー確認・管理（現在の人数: **{len(members)}名**）\n※リストから選択すると削除できます。",
            view=view,
            ephemeral=True
        )


# ----------------------------------------------------
# Bot イベント＆コマンド
# ----------------------------------------------------
# @bot.event
# async def on_ready():
#     print(f"Logged in as {bot.user}")
#     try:
#         if TEST_GUILD_ID:
#             guild_obj = discord.Object(id=TEST_GUILD_ID)
#             bot.tree.copy_global_to(guild=guild_obj)
#             synced = await bot.tree.sync(guild=guild_obj)
#             print(f"Synced {len(synced)} command(s) to test guild.")
#         else:
#             synced = await bot.tree.sync()
#             print(f"Synced {len(synced)} command(s) globally.")
#     except Exception as e:
#         print(f"Sync error: {e}")

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        # グローバル（すべてのサーバー）にコマンドを同期
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s) globally.")
    except Exception as e:
        print(f"Synced error: {e}")

@bot.tree.command(name="gacha", description="スプラトゥーンブキガチャパネルを表示します")
async def gacha(interaction: discord.Interaction):
    # /gacha を呼び出した時に、自動でメンバーをリセットする
    reset_guild_members(interaction.guild_id)

    embed = discord.Embed(
        title="スプラトゥーンブキガチャ🦑",
        description="メンバー情報をリセットしました！\n下のボタンから参加者を追加してね！",
        color=discord.Color.blurple()
    )
    embed.set_footer(text="Discord Splatoon Buki Gacha Bot")
    # ドロップダウンのないシンプルなViewを渡す
    await interaction.response.send_message(embed=embed, view=TestView())

@bot.tree.command(name="reset", description="登録されているメンバーをすべてリセットします")
async def reset_command(interaction: discord.Interaction):
    reset_guild_members(interaction.guild_id)
    await interaction.response.send_message("🧹 データベースに登録されていたメンバーをすべてリセットしました！", ephemeral=True)

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("エラー: DISCORD_TOKEN が設定されていません。")
    else:
        bot.run(DISCORD_TOKEN)

# Renderのポートタイムアウト回避用ダミーWebサーバー
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()
