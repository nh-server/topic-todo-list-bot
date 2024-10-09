A simple discord bot that allows a team to anonymously submit ideas

---

### Setup
1. Install python 3.11 or later
1. Rename `config.yml.example` to `config.yml`
1. Get a bot token from [here](https://discord.com/developers). And put it into the `token` section of the yml file.
1. Set up postgres 13 or later and create a user for the bot. Then put those log in credentials in `config.yml`.
1. Run `pip install -r requirements.txt`
1. Run `python3 main.py`

---

### Usage
- Run `)help` to see all commands, or `/` to see available slash commands for the bot.

    To get set up on your server users with administrator permissions should:
    - Add roles of the users that will be able to submit ideas to the list of approved roles for the `send` command.
    - Run `)channel set <channel>` to set an output channel, make sure its a private channel that only the whitelisted users can see!

- If you are a whitelisted user and want to submit an idea, you can do so by doing `/send title:<your message title> message:<your message>` in the server.
    - A confirmation check will be displayed (ephemeral, so invisible to anyone but the user.)
- You can react with a 👍 if you want to increase the priority of a topic.
- Users with administrator permissions can close topics by using `/close topic:<topic number> outcome:<Accepted/Denied> reason:<reason>` They can choose to close a topic with "Accepted" or "Denied". Fundamentally these work the same, this is just for visual effect.

---

### Credits
- PhazonicRidley for the original source
- FrozenChen for help modernizing the code
