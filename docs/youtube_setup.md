# YouTube: токен для каналу America Over Time (робить власник, один раз)

Google Cloud проєкт: **hypothetica-511509**. Токен вводите ви; я його не бачу і не комітю (`client_secret*.json` і `youtube_token.json` у `.gitignore`).

## 1. Увімкнути API
1. https://console.cloud.google.com → угорі виберіть проєкт **hypothetica-511509**.
2. **APIs & Services → Library** → знайдіть **YouTube Data API v3** → **Enable**.

## 2. Екран згоди OAuth
1. **APIs & Services → OAuth consent screen** (або «Google Auth platform»).
2. User type **External**, назва застосунку (напр. `AOT uploader`), ваш e-mail у «support» і «developer contact».
3. Scopes: додайте `.../auth/youtube.upload` і `.../auth/youtube`.
4. Test users: додайте Google-акаунт, який керує каналом.
5. **Publishing status → «Publish app» (In production).** Інакше refresh-токен у режимі Testing живе лише 7 днів і публікація зламається. Для неперевіреного застосунку на екрані згоди буде попередження «Google hasn't verified this app» — це нормально: **Advanced → Go to … (unsafe)**.

## 3. Ключ клієнта
1. **APIs & Services → Credentials → Create credentials → OAuth client ID → Application type: Desktop app** → Create.
2. **Download JSON** → збережіть як `C:\map-timelapse\client_secret.json`.

## 4. Авторизувати канал (на вашому ПК)
```bash
pip install google-auth-oauthlib google-api-python-client
cd C:\map-timelapse
python scripts/youtube_auth.py client_secret.json
```
Відкриється браузер: виберіть акаунт, а на екрані вибору каналу — **America Over Time** (не What If і не інший). Скрипт покаже `channel / id / handle / videos`. Перевірте, що це America Over Time.

## 5. Покласти токен у GitHub
Найпростіше (потрібен `gh auth login` з правами на репо `edbackulin-eng/map-timelapse`):
```bash
python scripts/youtube_auth.py --store
```
Скрипт відмовиться, якщо в назві каналу немає «America», запише секрет **YT_TOKEN_JSON** і змінну **YT_CHANNEL_ID**.

Вручну: репо → Settings → Secrets and variables → Actions → *Secrets* → New: `YT_TOKEN_JSON` = вміст `youtube_token.json`; *Variables* → New: `YT_CHANNEL_ID` = id каналу з кроку 4.

## 6. Перевірка
Actions → **upload** → Run workflow, `dry_run = 1`. У логу має бути `channel ok: UC… America Over Time` і запланований слот; нічого не завантажується. Далі `upload` іде щодня о 11:30 UTC і тримає 2 відео запланованими наперед (пн/пт 20:00 Київ).

## Захист (що робить код)
- Токен відкриває рівно 1 канал, і його id має збігатися з `YT_CHANNEL_ID` — інакше нічого не завантажується (не залити на What If).
- Перед кожним завантаженням читається ПОВНИЙ список відео каналу; відео з маркером `[ref: map-timelapse/<slug>]` або з тією ж назвою вдруге не вантажиться. Якщо список не прочитано повністю — нічого не завантажується, робота падає (лист від GitHub).
- `state/episodes.json` комітиться одразу після кожного завантаження; якщо коміт не пройшов — запуск зупиняється.
- Налаштування кожного відео: категорія 27 (Education), `selfDeclaredMadeForKids=false`, `containsSyntheticMedia=false`, обкладинка, опис із джерелами + 3–5 хештегів, теги з ключових слів каналу.

## Відомий ризик
YouTube обмежує відео, завантажені через API з **неперевірених** проєктів, створених після 28.07.2020: вони залишаються **private (locked)**, поки проєкт не пройде аудит («YouTube API Services – Audit and Quota Extension»). Якщо після першого завантаження відео в Studio позначене як заблоковане/приватне й не виходить за розкладом — або подайте форму аудиту для hypothetica-511509, або скажіть мені, і підключимо OAuth-клієнт старішого перевіреного проєкту (як в інших каналах).
