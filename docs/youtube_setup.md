# YouTube: токен для каналу America Over Time (робить власник, один раз)

Google Cloud проєкт: **hypothetica-511509** (той самий, що в What If): API увімкнено, екран згоди «In production», Desktop-клієнт є.
Новий клієнт НЕ створюємо: файл клієнта What If уже скопійовано в `C:\map-timelapse\client_secret.json` (у `.gitignore`, у git не потрапляє).

## Дві команди (PowerShell)
```
cd C:\map-timelapse
python scripts/youtube_auth.py client_secret.json
```
Відкриється браузер: увійдіть у Google-акаунт і на екрані вибору каналу оберіть **America Over Time** (не What If). Скрипт покаже `channel / id / handle / videos` — перевірте, що це America Over Time.
```
python scripts/youtube_auth.py --store
```
Скрипт відмовиться, якщо в назві каналу немає «America»; інакше запише секрет **YT_TOKEN_JSON** і змінну **YT_CHANNEL_ID** у репо `edbackulin-eng/map-timelapse` (потрібен `gh`, на цьому ПК він уже залогінений).

## Далі автоматично
Як тільки секрет і змінна з'являться, запускається `upload` з `dry_run=1`: у логу має бути `channel ok: UC… America Over Time` і слот публікації; нічого не завантажується. Після перевірки `upload` іде щодня о 11:30 UTC і тримає 2 відео запланованими наперед (пн/пт 20:00 Київ).

Вручну (якщо треба): репо → Settings → Secrets and variables → Actions → *Secrets* → `YT_TOKEN_JSON` = вміст `youtube_token.json`; *Variables* → `YT_CHANNEL_ID` = id каналу.

## Захист (що робить код)
- Токен відкриває рівно 1 канал, і його id має збігатися з `YT_CHANNEL_ID` — інакше нічого не завантажується (не залити на What If).
- Перед кожним завантаженням читається ПОВНИЙ список відео каналу; відео з маркером `[ref: map-timelapse/<slug>]` або з тією ж назвою вдруге не вантажиться. Якщо список не прочитано повністю — нічого не завантажується, робота падає (лист від GitHub).
- `state/episodes.json` комітиться одразу після кожного завантаження; якщо коміт не пройшов — запуск зупиняється.
- Налаштування кожного відео: категорія 27 (Education), `selfDeclaredMadeForKids=false`, `containsSyntheticMedia=false`, обкладинка, опис із джерелами + 3–5 хештегів, теги з ключових слів каналу.

## Відомий ризик
YouTube обмежує відео, завантажені через API з **неперевірених** проєктів, створених після 28.07.2020: вони залишаються **private (locked)**, поки проєкт не пройде аудит («YouTube API Services – Audit and Quota Extension»). Якщо після першого завантаження відео в Studio позначене як заблоковане/приватне й не виходить за розкладом — або подайте форму аудиту для hypothetica-511509, або скажіть мені, і підключимо OAuth-клієнт старішого перевіреного проєкту (як в інших каналах).
