import asyncio
import os
import subprocess
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message

# ==============================
# BOT TOKEN
# ==============================
TOKEN = "8209871017:AAFeSfWiNt9GxP-UxFhRPF7oLK1dKXXIp_k"

bot = Bot(token=TOKEN)
dp = Dispatcher()

COMMAND_FILE = "commands.txt"


# ==============================
# AUTO-INSTALL MISSING LIBRARIES
# ==============================
async def auto_install_missing_lib(error_text: str) -> str:
    lines = error_text.lower().split("\n")
    missing = []

    for line in lines:
        if "no module named" in line:
            try:
                lib = line.split("named")[-1].replace("'", "").strip()
                if lib:
                    missing.append(lib)
            except:
                pass

    output = ""
    for lib in missing:
        result = subprocess.run(
            f"pip install {lib}",
            shell=True,
            capture_output=True,
            text=True
        )
        output += f"\n\n📦 Installing {lib} → \n" + result.stdout + result.stderr

    if not missing:
        return "No missing libraries found."

    return output


# ==============================
# LOAD COMMANDS
# ==============================
def load_commands():
    if not os.path.exists(COMMAND_FILE):
        return []
    with open(COMMAND_FILE, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


# ==============================
# SHOW COMMANDS
# ==============================
@dp.message(commands=["cmds"])
async def show_commands(message: Message):
    cmds = load_commands()
    if not cmds:
        await message.reply("⚠ commands.txt is empty!")
    else:
        await message.reply("📜 Available Commands:\n" + "\n".join(cmds))


# ==============================
# RELOAD COMMANDS
# ==============================
@dp.message(commands=["reload"])
async def reload_cmds(message: Message):
    await message.reply("🔄 Commands Reloaded!")


# ==============================
# RUN PYTHON FILE
# ==============================
async def run_python_file(message: Message):
    os.makedirs("downloads", exist_ok=True)
    file_path = f"downloads/{message.document.file_name}"

    await bot.download(message.document, destination=file_path)

    try:
        result = subprocess.run(
            ["python3", file_path],
            capture_output=True,
            text=True,
            timeout=25
        )

        output = result.stdout + result.stderr

        # Missing library auto-fix
        if "No module named" in output:
            fix = await auto_install_missing_lib(output)
            output = "❗ Auto Fix Attempted:\n" + fix

        if not output.strip():
            output = "Python file ran but returned no output."

        await message.reply(f"🖥 Output:\n{output}")

    except Exception as e:
        await message.reply(f"❌ Error running file:\n{e}")


# ==============================
# TERMINAL COMMANDS
# ==============================
async def run_terminal(cmd: str) -> str:
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=35
        )
        return result.stdout + result.stderr
    except Exception as e:
        return f"❌ Terminal Error: {e}"


# ==============================
# MAIN HANDLER
# ==============================
@dp.message()
async def handler(message: Message):
    text = message.text or ""
    cmds = load_commands()

    # Run Python file
    if message.document and message.document.file_name.endswith(".py"):
        await run_python_file(message)
        return

    # PIP command
    if text.startswith("/pip "):
        command = text.replace("/pip ", "pip ")
        output = await run_terminal(command)
        await message.reply(f"📦 *PIP Output:*\n{output}")
        return

    # Terminal command
    if text.startswith("/term "):
        command = text.replace("/term ", "")
        output = await run_terminal(command)
        await message.reply(f"🖥 *Terminal Output:*\n{output}")
        return

    # Install requirements
    if text.startswith("/install_requirements"):
        if not os.path.exists("requirements.txt"):
            await message.reply("⚠ requirements.txt not found!")
            return
        output = await run_terminal("pip install -r requirements.txt")
        await message.reply(f"📦 Installed Requirements:\n{output}")
        return

    # commands.txt simple commands
    if text in cmds:
        await message.reply(f"✔ Command executed: {text}")
        return

    await message.reply("Send a .py file or valid command.")


# ==============================
# START BOT
# ==============================
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
