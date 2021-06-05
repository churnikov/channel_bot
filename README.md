# channel_bot
Collect all media resources in one telegram bot!

Checkout [@nya_channels_bot](https://t.me/nya_channels_bot)

This bot is not as good as @junction_bot, but it does it's job

the main thing of this bot is that you don't have to pay for unlimited number of channels, unlike in [@junction_bot](https://t.me/junction_bot), 
because we didn't set up payment :)

But also because you can set up this bot on your machine.

For that you need to:
1. have python ≥ 3.9;
2. [setup mongodb](https://www.freecodecamp.org/news/learn-mongodb-a4ce205e7739/) so that it's available on localhost;
3. Clone this repo and `cd` into it; 
4. install requirement via `pip3 install --user .` or if you have poetry `poetry install`;
5. launch bot via `TG_API_HASH=INSERT_TELEGRAM_API_HASH TG_BOT_TOKEN=INSERT_TELEGRAM_BOT_TOKEN TG_API_ID=INSERT_TELEGRAM_API_ID run_channel_bot` (or you can copy `.env.example` into `.env` file and insert your credentials there)
   2. `TG_API_HASH` and `TG_API_ID` you can get from [telegram website](https://core.telegram.org/api/obtaining_api_id).
   3. `TG_BOT_TOKEN` you can get from [@BotFather](https://t.me/BotFather)
    
# Privacy note

If it's not obvious, we collect some data from users. In fact, we collect users ids and channels that they subscribe to. That data is required to make this application possible. If you are not okay with the fact that we collect a little bit of your data, feel free to set up your own application using instructions above. 
