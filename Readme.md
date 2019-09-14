# Bishop CI/CD Python script
*Автоматизируйте анализ безопасности мобильных Android приложений при помощи платформы [Bishop](https://bishop.appsec.global/).*

Данный скрипт предназначен для встраивания анализа безопасности мобильных приложений в непрерывный процесс разработки (CI/CD).
В процессе выполнения скрипта приложение отправляется в платформу Bishop для анализа. На выходе формируется json файл (`bishop_scan_report.json`) с подробными результатами. 

## Варианты запуска
На данный момент поддерживается несколько вариантов запуска:
 * анализ приложения, apk-файл которого расположенного локально 
 * анализ приложения из системы [HockeyApp](https://hockeyapp.net/)

## Параметры запуска
Параметры запуска зависят от расположения файла apk, отправляемого на анализ. Так же, существуют обязательные параметры, которые необходимо указывать при любом виде запуска:
 * `bishop_url` - сетевой адрес Bishop (путь до корня без последнего `/`), при использовании cloud версии - `https://saas.mobile.appsec.world`
 * `profile` - id профиля для которого проводится анализ
 * `testcase` - id testcase, который будет воспроизведен во время анализа
 * `token` - CI/CD токен для доступа (как его получить можно посмотреть в документации)
 * `distribution_system` - способ загрузки приложения, возможные опции: `file` и `hockeyapp`. Более подробно про них описано ниже в соответствующих разделах

### Локальный запуск
Данный вид запуска подразумевает, что apk файл приложения для анализа располагается локально, рядом (на одной системе) со скриптом. 
Для выбора этого способа при запуске необходимо указать параметр `distribution_system file`. В этом случае обязательным параметром необходимо указать путь к файлу `file_path`

### HockeyApp
Для загрузки приложения из системы дистрибуции HockeyApp при запуске необходимо указать параметр `distribution_system hockeyapp`. Так же необходимо указать обязательные параметры:
 * `hockey_token` (обязательный параметр) - API токен для доступа. Как его получить можно узнать [здесь](https://rink.hockeyapp.net/manage/auth_tokens)
 * `hockey_version` (необязательный параметр) - при указании данного параметра будет скачана конкретная версия приложения по коду его версии (поле `version` в [API](https://support.hockeyapp.net/kb/api/api-versions)). При отсутствии данного параметра будет загружена последняя доступная версия приложения (latest).
 * `bundle_id` или `public_id` (обязательный параметр)
    * `bundle_id` - идентификатор Android приложения или, по другому, имя пакета (`com.swordfishsecurity.app.example`). При указании данной опции будет осуществлен поиск по всем приложениям внутри HockeyApp и выбрано приложение с соответствующим идентификатором. Поле в API - [bundle_identifier](https://support.hockeyapp.net/kb/api/api-apps)
    * `public_idr` - идентификатор приложения внутри системы HockeyApp. При указании данного параметра будет загружено приложение с соответствующим идентификатором. Поле в API - [public_identifier](https://support.hockeyapp.net/kb/api/api-apps)


## Примеры запуска

#### Локальный файл 
Для запуска анализа локального файла:

```
python3.6 run-bishop-scan.py --distribution_system file --file_path "/bishop/demo/apk/swordfish-demo.apk" --bishop_url "https://saas.mobile.appsec.world" --profile 1 --testcase 4 --token "eyJ0eXA4OiJKA1QiLbJhcGciO5JIU4I1NiJ1.eyJzdaJqZWNcX2lkIj53LCJle5AiOjf1OTM5OTU3MjB1.hfI6c4VN_U2mo5VfRoENPvJCvpxhLzjHqI0gxqgr2Bs"
```

В результате будет запущен автоматизированный анализ приложения `swordfish-demo.apk` с профилем с `id` 1 и будет запущен тест кейс с `id` 4.

#### HockeyApp по bundle_identifier и указанием версии
Для запуска анализа приложения из системы HockeyApp:

```
python3.6 run-bishop-scan.py --distribution_system hockeyapp --hockey_token 18bc81146d374ba4b1182ed65e0b3aaa --bundle_id com.swordfishsecurity.demo --hockey_version 1026 --url "https://saas.mobile.appsec.world" --profile 2 --testcase 3 --token "eyJ0eXA4OiJKA1QiLbJhcGciO5JIU4I1NiJ1.eyJzdaJqZWNcX2lkIj53LCJle5AiOjf1OTM5OTU3MjB1.hfI6c4VN_U2mo5VfRoENPvJCvpxhLzjHqI0gxqgr2Bs"
```

В результате в системе HockeyApp будет найдено приложение с идентификатором пакета `com.swordfishsecurity.demo` и версией `1026`. Он будет скачен и для него будет проведен автоматизированный анализ с профилем с `id` 2 и будет запущен тест-кейс с `id` 3.

#### HockeyApp по public_identifier и с последней доступной версией
Для запуска анализа последней версии приложения из системы HockeyApp по его публичному идентификатору:

```
python3.6 run-bishop-scan.py --distribution_system hockeyapp --hockey_token 18bc81146d374ba4b1182ed65e0b3aaa --public_id "1234567890abcdef1234567890abcdef" --url "https://saas.mobile.appsec.world" --profile 2 --testcase 3 --token "eyJ0eXA4OiJKA1QiLbJhcGciO5JIU4I1NiJ1.eyJzdaJqZWNcX2lkIj53LCJle5AiOjf1OTM5OTU3MjB1.hfI6c4VN_U2mo5VfRoENPvJCvpxhLzjHqI0gxqgr2Bs"
```

В результате в системе HockeyApp будет найдено приложение с уникальным публичным идентификатором `1234567890abcdef1234567890abcdef` и последней доступной версией. Файл приложения будет скачен и для него будет проведен автоматизированный анализ с профилем с `id` 2 и будет запущен тест-кейс с `id` 3.