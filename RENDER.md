# Nisja në Render

Ky konfigurim nuk krijon shërbime ose pagesa automatikisht. Kodi duhet të jetë në GitHub përpara deploy-it. Përdorni vetëm të dhëna testimi derisa të përfundojnë konfigurimi i email-it, verifikimet e sigurisë dhe miratimi i shkollës.

## Web Service

| Fusha | Vlera |
|---|---|
| Name | `rilindja` ose emër i lirë i ngjashëm |
| Language | Python 3 |
| Branch | Dega ku është ruajtur kodi, pas miratimit të ndryshimeve |
| Region | E njëjta rajon me PostgreSQL; preferoni rajon evropian |
| Root Directory | Bosh |
| Build Command | `bash scripts/render_build.sh` |
| Start Command | `bash scripts/render_start.sh` |

Zgjidhni plan që mbështet disk të qëndrueshëm. Në formularin aktual Starter shfaqet $7/muaj; PostgreSQL dhe disku faturohen veçmas. Kontrolloni çmimet në llogarinë tuaj para krijimit.

## PostgreSQL

Krijoni PostgreSQL nga menuja New, në të njëjtin rajon me Web Service. Vendosni emra jo sekretë si `rilindja-db` dhe `rilindja`. Render gjeneron kredencialet. Merrni **Internal Database URL** dhe vendoseni vetëm te variabla sekrete `RILINDJA_DATABASE_URL` e Web Service. Mos e dërgoni në chat, screenshot ose GitHub. Aplikacioni kërkon TLS për lidhjen PostgreSQL. Zgjidhni një plan me ruajtje dhe backup të përshtatshëm; mos përdorni databazë testimi me afat për të dhëna reale.

## Disku privat

Te konfigurimi i Web Service, shtoni disk të qëndrueshëm me:

- Mount path: `/var/data`
- Madhësia: sipas nevojës dhe çmimit të shfaqur nga Render.

Variabla `RILINDJA_STATE_DIR=/var/data/rilindja` vendos dokumentet private dhe email-et lokale në këtë disk. Mos krijoni Static Site për diskun dhe mos ekspozoni `/var/data` publikisht. Mos përdorni disk të përkohshëm për dokumentet.

## Environment Variables të Web Service

| Emri | Vlera |
|---|---|
| `PYTHON_VERSION` | `3.12.14` |
| `RILINDJA_DEBUG` | `0` |
| `RILINDJA_SECRET_KEY` | Klikoni Generate; mbajeni sekret dhe të pandryshuar gjatë redeploy-it |
| `RILINDJA_DATABASE_URL` | Internal Database URL nga PostgreSQL; sekret |
| `RILINDJA_STATE_DIR` | `/var/data/rilindja` |
| `WEB_CONCURRENCY` | `2` |

Render siguron `RENDER=true`, `RENDER_EXTERNAL_HOSTNAME` dhe `PORT`. Hostname-i konkret pranohet automatikisht, pa wildcard. Headers HTTPS besohen vetëm në Render; aplikacioni dhe cookies punojnë në HTTPS. WhiteNoise shërben vetëm skedarët statikë të mbledhur, pa publikuar dokumentet private.

Mos vendosni `RILINDJA_DEBUG=1` për të kaluar gabimet e konfigurimit. Start-i ndalon nëse mungojnë PostgreSQL ose disku. Build-i nuk kryen migrime në DB dhe nuk pret që disku të jetë i montuar; migrimet kryhen gjatë start-it, kur disku është i disponueshëm.

## Pas deploy-it

1. Kontrolloni logs për migrimet dhe nisjen e Gunicorn.
2. Hapni adresën HTTPS që Render jep dhe faqen `/hyrje/`; kontrolloni stilin e faqes dhe formularin.
3. Në **Shell** privat të shërbimit Render ekzekutoni `python manage.py bootstrap_admin --email EMAILI_JUAJ_ZYRTAR`. Komanda kërkon fjalëkalim pa echo dhe nuk pranon administrator të dytë nga bootstrap-i. Mos e vendosni fjalëkalimin në komanda ose environment variables.
4. Hyni dhe krijoni një vit/shkollë/llogari të shënuar TEST; testoni miratimin, notat dhe një dokument privat. Bëni redeploy dhe verifikoni ruajtjen e dokumentit dhe regjistrave.
5. Konfiguroni SMTP real për rivendosjen e fjalëkalimit sipas README.md. Pa këtë, email-et mbeten skedarë privatë dhe nuk dërgohen.

Hostimi real në Render, lidhja me PostgreSQL dhe ruajtja pas redeploy-it duhen verifikuar në shërbimin tuaj. Testimi lokal i konfigurimit nuk i zëvendëson këto prova. Politikat RLS, skanimi malware dhe verifikimet ligjore mbeten jashtë këtij konfigurimi.
