import asyncio
import os
import subprocess
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import Command

TOKEN = "8209871017:AAFeSfWiNt9GxP-UxFhRPF7oLK1dKXXIp_k"

bot = Bot(token=TOKEN)
dp = Dispatcher()

COMMAND_FILE = "commands.txt"


# -------- AUTO-INSTALL MISSING LIBRARIES --------

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


# -------- LOAD COMMANDS --------

def load_commands():
    if not os.path.exists(COMMAND_FILE):
        return []
    with open(COMMAND_FILE, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


# -------- SHOW COMMANDS --------

@dp.message(Command("cmds"))
async def show_commands(message: Message):
    cmds = load_commands()
    if not cmds:
        await message.answer("⚠ commands.txt is empty!")
    else:
        await message.answer("📜 Available Commands:\n" + "\n".join(cmds))


# -------- RELOAD COMMANDS --------

@dp.message(Command("reload"))
async def reload_cmds(message: Message):
    await message.answer("🔄 Commands Reloaded!")


# -------- RUN PYTHON FILE (.py) --------

@dp.message(F.document)
async def handle_document(message: Message):
    if not message.document.file_name.endswith(".py"):
        await message.answer("Send a valid .py file only.")
        return

    os.makedirs("downloads", exist_ok=True)
    file_path = f"downloads/{message.document.file_name}"

    await bot.download(message.document, destination=file_path)

    try:
        result = subprocess.run(
            ["python3", file_path],
            capture_output=True,
            text=True
        )
        output = result.stdout + result.stderr

        if "No module named" in output:
            fix = await auto_install_missing_lib(output)
            output = "❗ Auto Fix Attempted:\n" + fix

        if not output.strip():
            output = "Python file ran but returned no output."

        await message.answer(f"🖥 Output:\n{output}")

    except Exception as e:
        await message.answer(f"❌ Error running file:\n{e}")


# -------- TERMINAL COMMANDS --------

async def run_terminal(cmd: str) -> str:
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True
        )
        return result.stdout + result.stderr
    except Exception as e:
        return f"❌ Terminal Error: {e}"


@dp.message(F.text.startswith("/pip "))
async def pip_cmd(message: Message):
    command = message.text.replace("/pip ", "pip ")
    output = await run_terminal(command)
    await message.answer(f"📦 *PIP Output:*\n{output}")


@dp.message(F.text.startswith("/term "))
async def term_cmd(message: Message):
    command = message.text.replace("/term ", "")
    output = await run_terminal(command)
    await message.answer(f"🖥 *Terminal Output:*\n{output}")


@dp.message(F.text.startswith("/install_requirements"))
async def install_req(message: Message):
    if not os.path.exists("requirements.txt"):
        await message.answer("⚠ requirements.txt not found!")
        return

    output = await run_terminal("pip install -r requirements.txt")
    await message.answer(f"📦 Installed Requirements:\n{output}")


# -------- CUSTOM commands.txt COMMANDS --------

@dp.message()
async def basic_handler(message: Message):
    cmds = load_commands()
    if message.text in cmds:
        await message.answer(f"✔ Command executed: {message.text}")
    else:
        await message.answer("Send a .py file or valid command.")


# -------- START BOT --------

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
