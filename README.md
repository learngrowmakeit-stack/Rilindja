# Rilindja – Sistemi digjital i shkollës

Aplikacion i integruar në gjuhën shqipe, me Django 5.2, autentikim me sesione, databazë relacionale dhe skedarë privatë. Ndërfaqja përdor të njëjtën databazë për të gjitha modulet. Nuk ka llogari ose fjalëkalime të paracaktuara.

## Nisja në cloud

Python 3.12. Checkout-i i task-ut është tashmë i izoluar; përdoreni drejtpërdrejt, pa krijuar Git worktree.

```bash
bash /workspace/Rilindja/scripts/install.sh
cd /workspace/Rilindja
export RILINDJA_DEBUG=1
/workspace/.venvs/rilindja/bin/python manage.py bootstrap_admin --email emaili-juaj-zyrtar
/workspace/.venvs/rilindja/bin/python manage.py runserver 127.0.0.1:8000 --noreload
```

Komanda e konfigurimit kërkon fjalëkalimin në terminal pa e shfaqur. Lejohet vetëm para krijimit të administratorit të parë. Krijimi i administratorëve shtesë bëhet nga administratori ekzistues përmes miratimit të llogarive. Mos vendosni fjalëkalime në argumente, skripte, Git ose chat.

Përpara shkollës reale, administratori krijon vitin, periudhat, klasat, lëndët, llojet/peshat e vlerësimit dhe caktimet. Punonjësit kërkojnë llogari; administratori i miraton dhe cakton rolin. Regjistrimi publik nuk lejon vetëcaktim roli.

Në zhvillim, databaza, çelësi lokal dhe skedarët ruhen në dosjen e injoruar `var/`. `RILINDJA_STATE_DIR` mund të caktojë destinacion tjetër privat. Email-et e rivendosjes ruhen në `var/mail/` gjatë zhvillimit; nuk dërgohen në internet.

## Funksionet e integruara

- Tetë role, miratim/bllokim/çaktivizim llogarish, kontrolle në server dhe revokim i sesioneve të llogarive të bllokuara.
- Nxënës, profile, regjistrime në klasa, transferime që ruajnë historikun dhe arkivim sipas viteve.
- Caktime sipas klasës/lëndës; mësimdhënësi ndryshon vetëm notat në caktimet e veta. Kujdestari lexon të dhënat akademike të klasës së vet.
- Nota me pesha të ruajtura në momentin e regjistrimit, kontroll klase/viti/periudhe/date dhe historik me përdoruesin, kohën, vlerat e mëparshme dhe të reja. Konfliktet e versioneve të notës refuzohen.
- Raport pedagogjik për disa klasa, numër nxënësish të përfshirë/të paplotë, mesatare të lëndëve, kategori suksesi, rezultate individuale dhe krahasim me periudhën e mëparshme.
- Vijueshmëri ditore, arsyetim, kërkim/filtra/eksporte dhe njoftime pas çdo pesë mungesash të paarsyetuara të regjistruara në formular.
- Dosje pedagogjike, versione skedarësh, dorëzim, shqyrtim, komente dhe njoftime për statusin. Tabela të përbashkëta me leje të veçanta për shikim/shkarkim/ndryshim/fshirje, sipas rolit ose përdoruesit.
- Dokumentet psikologjike kërkojnë autorizim individual; administratori ose drejtori nuk merr automatikisht qasje. Rastet profesionale janë të ndara dhe të kufizuara te psikologu përgjegjës/personat e autorizuar individualisht.
- Parapamje XLSX/CSV me kërkim/renditje/filtra, përditësim tabelar në shfletues dhe ruajtje si version i ri XLSX. Origjinali ruhet. Përditësimi në shfletues mbështet 500 rreshta × 30 kolona dhe i ruan formulat si tekst.
- Importim me parapamje e validim për nxënës, nota dhe vijueshmëri; ruajtje atomike, pa importim të pjesshëm.
- Protokoll hyrës/dalës/kërkesa, kalendar me pjesëmarrës, orar me kontroll të mbivendosjes së klasës/mësimdhënësit/kabinetit dhe njoftime për ndryshime.
- Eksporte CSV, XLSX dhe PDF me emër shkolle, titull, datë dhe përgjegjës. Logoja e konfiguruar përfshihet në PDF. Modulet mbështesin kufizime shtesë sipas rolit nga administratori, brenda përgjegjësive bazë të atij roli.
- Regjistër auditimi dhe komanda për kopje rezervë/rikuperim.

## Metoda e suksesit

Mesatarja e lëndës për nxënësin = `Σ(nota × pesha e ruajtur) / Σ(pesha)`, vetëm për lëndën dhe periudhën e përzgjedhur. Mesatarja e përgjithshme e nxënësit = mesatarja e lëndëve me peshë të barabartë. Nxënësi është i plotë kur ka të paktën një vlerësim për çdo lëndë të caktuar në klasë. Ky përkufizim duhet të miratohet nga shkolla; nuk supozon se një vlerësim është notë përfundimtare zyrtare.

Mesatarja e klasës përfshin vetëm nxënësit e plotë. Mungesa e notës nuk është zero dhe nuk plotësohet artificialisht. Mesatarja e secilës lëndë tregon veçmas numrin e nxënësve me vlerësim. Kategoritë bazohen në mesataren e parrumbullakosur; rrumbullakosja shërben vetëm për shfaqje. Pragu kalues është i konfigurueshëm për çdo vit. Ndryshimi i peshës së një lloji nuk ndryshon retroaktivisht notat ekzistuese. Vitet e arkivuara janë vetëm për lexim në aplikacion.

Kur filtrohet një lëndë, plotësia dhe mesatarja i referohen vetëm asaj lënde. Raportet e mësimdhënësve kufizohen te lëndët e caktuara ose klasa ku janë kujdestarë.

## Importimi

Skedarët duhet të kenë titujt e mëposhtëm, në rendin e dhënë. Datat: `YYYY-MM-DD`; klasat: numra 1–9. Kufiri: 500 regjistrime për import. XLSX nuk duhet të përmbajë makro; CSV duhet të jetë UTF-8. Parapamja lexon fletën e parë.

Nxënës:
```text
numri_regjistrit,emri,mbiemri,klasa,paralelja,data_regjistrimit
```

Nota:
```text
numri_regjistrit,klasa,paralelja,lenda,periudha,lloji,data,nota
```

Vijueshmëri:
```text
numri_regjistrit,klasa,paralelja,data,statusi,arsyetimi
```
Statuset e importit: `present`, `absent`, `late`, `excused`. Lëndët, periudhat dhe llojet duhet të përputhen me emrat në databazë. Kufijtë, dyfishimet dhe caktimet kontrollohen para konfirmimit. Importimi i notave krijon gjithashtu historikun e vlerësimeve.

## Testimi

```bash
cd /workspace/Rilindja
RILINDJA_DEBUG=1 /workspace/.venvs/rilindja/bin/python manage.py test school
RILINDJA_DEBUG=1 /workspace/.venvs/rilindja/bin/python manage.py check
```

Testet përdorin databazë të veçantë dhe të dhëna me shenjën TEST. Për regjistra demonstrimi opsionalë pa përdorues ose nota të sajuara:

```bash
RILINDJA_DEBUG=1 /workspace/.venvs/rilindja/bin/python manage.py seed_demo
```

`seed_demo` është i përsëritshëm dhe përdor vetëm vitin `DEMO 2026/2027`. Mos e përdorni në databazën reale të shkollës.

Testi i shfletuesit: `scripts/smoke_browser.py` me Playwright dhe Chromium. Ai krijon e fshin një databazë të përkohshme dhe kontrollon hyrjen, panelin, kërkimin/profilin, ruajtjen dhe daljen në ekran 1440 px dhe 390 px.

## Kopjet rezervë dhe rikuperimi

Nga terminali i besuar, me konfigurimin e databazës aktive:

```bash
RILINDJA_DEBUG=1 /workspace/.venvs/rilindja/bin/python manage.py backup_school --output /destinacion-privat/backup.tar.gz
RILINDJA_DEBUG=1 /workspace/.venvs/rilindja/bin/python manage.py restore_school --backup /destinacion-privat/backup.tar.gz --destination /destinacion-i-ri
```

Ndalni shërbimin gjatë kopjimit të dokumenteve për të shmangur ndryshime ose fshirje konkurruese. Kopja përfshin databazën dhe skedarët, me leje 0600, pa çelësin e sesioneve ose kredenciale të mjedisit. Ruajeni në destinacion të enkriptuar jashtë makinës së aplikacionit. SQLite kopjohet me API-në konsistente të backup-it. Rikuperimi kontrollon checksum-in dhe integritetin dhe refuzon mbishkrimin e destinacionit. Kontrolloni regjistrat/skedarët e rikuperuar, ndalni shërbimin, pastaj vendosni `RILINDJA_STATE_DIR` në destinacionin e ri. PostgreSQL përdor `pg_dump`; për rikuperim përdorni `pg_restore` në një databazë të re. Planifikimi dhe ruajtja jashtë makinës janë përgjegjësi operative.

## Konfigurimi para përdorimit real

Ky version është bazë zhvillimi e testueshme; mos e konsideroni të certifikuar për prodhim ose për kërkesat ligjore të të dhënave të fëmijëve.

- Vendosni `RILINDJA_DEBUG=0`, një `RILINDJA_SECRET_KEY` privat dhe `RILINDJA_ALLOWED_HOSTS` me domain-in real. Përdorni HTTPS. Cookies të sigurta, HSTS dhe ridrejtimi HTTPS janë aktivë në prodhim.
- Për PostgreSQL: `RILINDJA_DB_NAME`, `RILINDJA_DB_HOST`, `RILINDJA_DB_PORT`, `RILINDJA_DB_USER`, `RILINDJA_DB_PASSWORD`. Përdorni përdorues DB me privilegje minimale dhe rrjet privat. SQLite është vetëm konfigurimi lokal i verifikuar. PostgreSQL dhe politika RLS sipas përdoruesit nuk janë verifikuar/implementuar; kontrollet e qasjes aktualisht zbatohen në server, krahas lidhjeve dhe kufizimeve të integritetit në DB.
- Për email real: `RILINDJA_EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend`, `RILINDJA_EMAIL_HOST`, `RILINDJA_EMAIL_PORT`, `RILINDJA_EMAIL_USER`, `RILINDJA_EMAIL_PASSWORD`, `RILINDJA_FROM_EMAIL`. Vendosni kredencialet vetëm përmes injektimit të sigurt të mjedisit. Mos i ruani në repo. Transporti SMTP nuk është testuar në këtë mjedis.
- Për WSGI: `gunicorn config.wsgi:application --bind 127.0.0.1:8000 --workers 2`, pas një reverse proxy HTTPS. Konfiguroni përcjelljen e protokollit sipas infrastrukturës së besuar; mos besoni headers të ardhur nga klientët pa proxy të kontrolluar.
- Ekzekutoni `manage.py collectstatic --noinput`; publikoni vetëm `staticfiles/`, kurrë `var/`, databazën ose dokumentet private. `MEDIA_ROOT` nuk ka rrugë publike; shkarkimet kalojnë autorizimin.
- Ngarkimet kufizohen në 20 MB, verifikojnë formatin bazë dhe refuzojnë makrot/arkivat e fryra. Para prodhimit shtoni skanim malware dhe kontroll më të plotë për dokumente PDF/Office. Kontrolli bazë nuk është certifikim i përmbajtjes.
- Afati i ruajtjes është metadata e konfigurueshme; nuk ka fshirje automatike sipas afatit. Miratoni politikën ligjore, procedurat e fshirjes, aksesin psikologjik dhe enkriptimin e backup-eve.
- Raportet mbështesin periudha/tremujorë, muaj, gjysmëvjetorë, vit dhe intervale datash. Konsolidimi përdor të njëjtën metodë të vlerësimeve të ponderuara; miratoni veçmas rregullat e notës përfundimtare zyrtare. Modelet zyrtare të dokumenteve duhet të përcaktohen nga shkolla. Dokumentet kanë afat dorëzimi; ekzekutoni `manage.py notify_deadlines` çdo ditë për njoftime individuale të afateve, pa dublime brenda ditës. Nuk ka modele ligjore të sajuara ose rezultate artificiale.
- Kontrollet e konfliktit të orarit/regjistrimit zbatohen në transaksione/formularë; për shkallëzim me shumë procese shtoni kufizime transaksionale PostgreSQL dhe testim ngarkese. Nuk pretendohet audit i pavarur sigurie ose testim i plotë i çdo shfletuesi.

Publikimi i mjedisit bëhet nga përdoruesi në cilësimet e cloud-it pas rishikimit të konfigurimit. Publikimi i aplikacionit në internet është hap i veçantë pas kontrolleve të mësipërme.
