try:
    from pyrogram import Client
except Exception:
    print("\nInstall Pyrogram and try again: pip3 install -r requirements.txt --break-system-packages")
    exit(1)
    
print(
"  ____                    ____                _              "
" |  _ \\ _   _ _ __ ___   / ___|  ___  ___ ___(_) ___  _ __   "
" | |_) | | | | '__/ _ \\  \\___ \\ / _ \\/ __/ __| |/ _ \\| '_ \\  "
" |  __/| |_| | | | (_) |  ___) |  __/\\__ \\__ \\ | (_) | | | | "
" |_|    \\__, |_|  \\___/  |____/ \\___||___/___/_|\\___/|_| |_| "
"        |___/                                                "
    )

print("Get your app credentials from https://my.telegram.org/apps and enter them below.")

API_KEY = int(input("Enter TELEGRAM API KEY. Ex: 12345678: "))
API_HASH = input("Enter TELEGRAM API HASH. Ex: 1a2b3c4d5e6f: ")
PHONE_NO = input("Enter your Telegram phone number including country code. Ex: +91xxxxxxxxxx: ")

with Client(
    name="WZUser",
    in_memory=True,
    api_id=API_KEY,
    api_hash=API_HASH,
    phone_number=PHONE_NO,
    app_version="@WZML_X User Session",
    device_model="@WZML_X Bot V3",
    system_version="@WZML_X Pyro Server",
) as user:
    user.send_message("me",
                     "**PyrogramV2 Session String**:\n\n"
                     f"||{user.export_session_string()}||\n\n"
                     "**Do not share this anywhere else account hack!**\n\n"
                     "**Generated by @WZML_X Manual Script.**"
                     )
    print(
        f"User's (@{user.me.username}) Pyrogram Session String has been sent to "
        "Saved Messages of your Telegram account!"
    )