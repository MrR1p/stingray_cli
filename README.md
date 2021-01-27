# Stingray CI/CD Python script
*Автоматизируйте анализ безопасности мобильных приложений при помощи системы [Stingray](https://stingray-mobile.ru/).*

Данный скрипт предназначен для встраивания анализа безопасности мобильных приложений в непрерывный процесс разработки (CI/CD).
В процессе выполнения скрипта приложение отправляется в систему Stingray для анализа. На выходе формируется json файл с подробными результатами.

## Способ установки

### Пакетный менеджер pip
Возможно установить пакет, используя pip:

`pip install stingray_cli`

При таком способе возможно запускать сканирование без указания интерпретатора `python` при помощи команды `stingray_cli`, пример:

`stingray_cli -h`

Во всех примерах ниже будет использован именно такой подход 

### Исходный код
Также поддерживается запуск при помощи загрузки исходных файлов и запуска непосредственно основного скрипта:

`python3 stingray_cli/run_stingray_scan.py -h`

При таком способе запуска необходимо дополнительно установить пакеты, указанные в `requirements.txt`

## Варианты запуска
На данный момент поддерживается несколько вариантов запуска:
 * анализ приложения, apk-файл которого расположенного локально
 * анализ приложения из системы [HockeyApp](https://hockeyapp.net/)
 * анализ приложений из системы [AppCenter](https://appcenter.ms)

## Параметры запуска
Параметры запуска зависят от расположения файла apk, отправляемого на анализ. Так же, существуют обязательные параметры, которые необходимо указывать при любом виде запуска:
 * `stingray_url` - сетевой адрес Stingray (путь до корня без последнего `/`), при использовании cloud версии - `https://saas.mobile.appsec.world`
 * `company_id` - идентификатор компании в рамках которой будет осуществлено сканирование
 * `architecture_id` - идентификатор архитектуры операционной системы, на которой будет произведено сканирование
 * `profile_id` - id профиля для которого проводится анализ
 * `testcase_id` - id testcase_id, который будет воспроизведен во время анализа; возможен запуск нескольких тесткейсов, для этого их id перечисляются через пробел
 * `token` - CI/CD токен для доступа (как его получить можно посмотреть в документации)
 * `nowait` - опциональный параметр, определяющий необходимость ожидания завершения сканирования. Если данный флаг установлен - скрипт не будет дожидаться завершения сканирования, а выйдет сразу же после запуска. Если флаг не стоит - скрипт будет ожидать завершения процесса анализа и формировать отчет.
 * `report_json_file_name` - опциональный параметр, определяющая, имя json-файла в который выгружается информация по сканирования в формате json. При отсутствии параметра информация сохраняться в json не будет. 
 * `distribution_system` - способ загрузки приложения, возможные опции: `file`, `hockeyapp` и `appcenter`. Более подробно про них описано ниже в соответствующих разделах

### Локальный запуск
Данный вид запуска подразумевает, что apk файл приложения для анализа располагается локально, рядом (на одной системе) со скриптом.
Для выбора этого способа при запуске необходимо указать параметр `distribution_system file`. В этом случае обязательным параметром необходимо указать путь к файлу `file_path`

### HockeyApp
Для загрузки приложения из системы дистрибуции HockeyApp при запуске необходимо указать параметр `distribution_system hockeyapp`. Так же необходимо указать обязательные параметры:
 * `hockey_token` (обязательный параметр) - API токен для доступа. Как его получить можно узнать [здесь](https://rink.hockeyapp.net/manage/auth_tokens)
 * `hockey_version` (необязательный параметр) - при указании данного параметра будет скачана конкретная версия приложения по коду его версии (поле `version` в [API](https://support.hockeyapp.net/kb/api/api-versions)). При отсутствии данного параметра будет загружена последняя доступная версия приложения (latest).
 * `hockey_bundle_id` или `hockey_public_id` (обязательный параметр)
    * `hockey_bundle_id` - идентификатор Android приложения или, по другому, имя пакета (`com.swordfishsecurity.app.example`). При указании данной опции будет осуществлен поиск по всем приложениям внутри HockeyApp и выбрано приложение с соответствующим идентификатором. Поле в API - [bundle_identifier](https://support.hockeyapp.net/kb/api/api-apps)
    * `hockey_public_id` - идентификатор приложения внутри системы HockeyApp. При указании данного параметра будет загружено приложение с соответствующим идентификатором. Поле в API - [public_identifier](https://support.hockeyapp.net/kb/api/api-apps)

### AppCenter
Для загрузки приложения из системы дистрибуции AppCenter при запуске необходимо указать параметр `distribution_system appcenter`. Так же необходимо указать обязательные параметры:
 * `appcenter_token` - API токен для доступа. Как его получить можно узнать [здесь](https://docs.microsoft.com/en-us/appcenter/api-docs/)
 * `appcenter_owner_name` - владелец приложения, как узнать имя владельца можно [здесь](https://intercom.help/appcenter/en/articles/1764707-how-to-find-the-app-name-and-owner-name-from-your-app-url) или в [официальной документации](https://docs.microsoft.com/en-us/appcenter/api-docs/#find-your-app-center-app-name-and-owner-name)
 * `appcenter_app_name` - имя приложения в системе AppCenter. Как его узнать можно по [ссылке](https://docs.microsoft.com/en-us/appcenter/api-docs/#find-your-app-center-app-name-and-owner-name)
 * `appcenter_release_id` или `appcenter_app_version`
    * `appcenter_release_id` - идентификатор загружаемого релиза в системе AppCenter для конкретного приложения. Возможно выставить значение `latest` - тогда будет загружен последний доступный релиз приложения. [Официальная документация](https://openapi.appcenter.ms/#/distribute/releases_getLatestByUser)
    * `appcenter_app_version` - при указании данного параметра будет найдена и скачана конкретная версия приложения по коду его версии (указанной в Android Manifest) (поле `version` в [документации](https://openapi.appcenter.ms/#/distribute/releases_list)).

## Примеры запуска

### Локальный файл

#### Стандартный способ запуска
Для запуска анализа локального файла:


```
stingray_cli --distribution_system file --file_path "/stingray/demo/apk/demo.apk" --stingray_url "https://saas.mobile.appsec.world" --profile_id 1 --testcase_id 4 --company_id 1 --architecture_id 1 --token "eyJ0eXA4OiJKA1QiLbJhcGciO5JIU4I1NiJ1.eyJzdaJqZWNcX2lkIj53LCJle5AiOjf1OTM5OTU3MjB1.hfI6c4VN_U2mo5VfRoENPvJCvpxhLzjHqI0gxqgr2Bs"
```

В результате будет запущен автоматизированный анализ приложения `demo.apk` с профилем с `id` 1 и будет запущен тест кейс с `id` 4.

#### Запуск без ожидания завершения сканирования

```
stingray_cli --distribution_system file --file_path "/stingray/demo/apk/demo.apk" --stingray_url "https://saas.mobile.appsec.world" --profile_id 1 --testcase_id 4 --company_id 1 --architecture_id 1 --token "eyJ0eXA4OiJKA1QiLbJhcGciO5JIU4I1NiJ1.eyJzdaJqZWNcX2lkIj53LCJle5AiOjf1OTM5OTU3MjB1.hfI6c4VN_U2mo5VfRoENPvJCvpxhLzjHqI0gxqgr2Bs" --nowait
```
В результате будет запущен автоматизированный анализ приложения `demo.apk` с профилем с `id` 1 и будет запущен тест кейс с `id` 4 и скрипт завершится сразу после запуска сканирования и не будет дожидаться окончания и генерировать отчет.

#### Генерация Summary отчета в формате JSON

```
stingray_cli --distribution_system file --file_path "/stingray/demo/apk/demo.apk" --stingray_url "https://saas.mobile.appsec.world" --profile_id 1 --testcase_id 4 --company_id 1 --architecture_id 1 --token "eyJ0eXA4OiJKA1QiLbJhcGciO5JIU4I1NiJ1.eyJzdaJqZWNcX2lkIj53LCJle5AiOjf1OTM5OTU3MjB1.hfI6c4VN_U2mo5VfRoENPvJCvpxhLzjHqI0gxqgr2Bs" --summary_report_json_file_name summary_report.json
```
В результате будет запущен автоматизированный анализ приложения `demo.apk` с профилем с `id` 1 и будет запущен тест кейс с `id` 4 и по завершении сканирования вместе с PDF-отчетом будет выгружен JSON отчет с суммарным количеством дефектов и краткой статистикой по сканированию.


### HockeyApp по bundle_identifier и указанием версии
Для запуска анализа приложения из системы HockeyApp:

```
stingray_cli --distribution_system hockeyapp --hockey_token 18bc81146d374ba4b1182ed65e0b3aaa --bundle_id com.stingray.demo --hockey_version 31337 --stingray_url "https://saas.mobile.appsec.world" --profile_id 2 --testcase_id 3 --company_id 1 --architecture_id 1 --token "eyJ0eXA4OiJKA1QiLbJhcGciO5JIU4I1NiJ1.eyJzdaJqZWNcX2lkIj53LCJle5AiOjf1OTM5OTU3MjB1.hfI6c4VN_U2mo5VfRoENPvJCvpxhLzjHqI0gxqgr2Bs"
```

В результате в системе HockeyApp будет найдено приложение с идентификатором пакета `com.stingray.demo` и версией `31337`. Он будет скачен и для него будет проведен автоматизированный анализ с профилем с `id` 2 и будет запущен тест-кейс с `id` 3.

### HockeyApp по public_identifier и с последней доступной версией
Для запуска анализа последней версии приложения из системы HockeyApp по его публичному идентификатору:

```
stingray_cli --distribution_system hockeyapp --hockey_token 18bc81146d374ba4b1182ed65e0b3aaa --public_id "1234567890abcdef1234567890abcdef" --stingray_url "https://saas.mobile.appsec.world" --profile_id 2 --testcase_id 3 --company_id 1 --architecture_id 1 --token "eyJ0eXA4OiJKA1QiLbJhcGciO5JIU4I1NiJ1.eyJzdaJqZWNcX2lkIj53LCJle5AiOjf1OTM5OTU3MjB1.hfI6c4VN_U2mo5VfRoENPvJCvpxhLzjHqI0gxqgr2Bs"
```

В результате в системе HockeyApp будет найдено приложение с уникальным публичным идентификатором `1234567890abcdef1234567890abcdef` и последней доступной версией. Файл приложения будет скачен и для него будет проведен автоматизированный анализ с профилем с `id` 2 и будет запущен тест-кейс с `id` 3.

### AppCenter по id релиза
Для запуска анализа приложения по известному имени, владельцу и ID релиза необходимо выполнить следующую команду:

```
stingray_cli --distribution_system appcenter --appcenter_token 18bc81146d374ba4b1182ed65e0b3aaa --appcenter_owner_name test_org_or_user --appcenter_app_name Stingray_demo_app --appcenter_release_id 710 --stingray_url "https://saas.mobile.appsec.world" --profile_id 2 --testcase_id 3 --company_id 1 --architecture_id 1 --token "eyJ0eXA4OiJKA1QiLbJhcGciO5JIU4I1NiJ1.eyJzdaJqZWNcX2lkIj53LCJle5AiOjf1OTM5OTU3MjB1.hfI6c4VN_U2mo5VfRoENPvJCvpxhLzjHqI0gxqgr2Bs"
```

В результате у владельца (пользователя или организации `test_org_or_user`) будет найдено приложение `Stingray_demo_app` с ID релиза `710`. Данная версия релиза будет загружена и передана на анализ безопасности в Stingray

Для загрузки релиза с последней версией необходимо параметр `appcenter_release_id latest`. Тогда команда будет выглядеть следующим образом:

```
stingray_cli --distribution_system appcenter --appcenter_token 18bc81146d374ba4b1182ed65e0b3aaa --appcenter_owner_name "test_org_or_user" --appcenter_app_name "Stingray_demo_app" --appcenter_release_id latest --stingray_url "https://saas.mobile.appsec.world" --profile_id 2 --testcase_id 3 --company_id 1 --architecture_id 1 --token "eyJ0eXA4OiJKA1QiLbJhcGciO5JIU4I1NiJ1.eyJzdaJqZWNcX2lkIj53LCJle5AiOjf1OTM5OTU3MjB1.hfI6c4VN_U2mo5VfRoENPvJCvpxhLzjHqI0gxqgr2Bs"
```

и загружен последний доступный релиз для данного приложения.

#### AppCenter по версии приложения
Для запуска анализа приложения по известному имени, владельцу и версии приложения (`version_code` в `Android Manifest`) необходимо выполнить следующую команду:

```
stingray_cli --distribution_system appcenter --appcenter_token 18bc81146d374ba4b1182ed65e0b3aaa --appcenter_owner_name "test_org_or_user" --appcenter_app_name "Stingray_demo_app" --appcenter_app_version 31337 --stingray_url "https://saas.mobile.appsec.world" --profile_id 2 --testcase_id 3 --company_id 1 --architecture_id 1 --token "eyJ0eXA4OiJKA1QiLbJhcGciO5JIU4I1NiJ1.eyJzdaJqZWNcX2lkIj53LCJle5AiOjf1OTM5OTU3MjB1.hfI6c4VN_U2mo5VfRoENPvJCvpxhLzjHqI0gxqgr2Bs"
```

В результате у владельца (пользователя или организации `test_org_or_user`) будет найдено приложение `Stingray_demo_app` и найден релиз, в котором была указана версия приложения `31337`. Данная версия релиза будет загружена и передана на анализ безопасности в Stingray.
