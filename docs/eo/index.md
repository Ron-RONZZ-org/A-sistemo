# A-sistemo Dokumentado

 Bonvenon al A-sistemo — sistemadministrada komandoj por A-kadro.

## Rapida Komenco

### Instalo

 ```bash
 pip install A-sistemo
 ```

 Aŭ el fontkodo:

 ```bash
 git clone https://github.com/Ron-RONZZ-org/A-sistemo.git
 cd A-sistemo
 poetry install
 ```

### Bazaj Uzoj

 ```bash
 A sistemo --help           # Montri helpon
 A sistemo help            # Montri helpon
 A sistemo ls             # Listigi subkomandojn
 ```

---

## Komandoj

A-sistemo provizas sistemadministrada komandojn:

| Komando | Priskribo |
|--------|-------------|
| `info` | Sistemaj informoj |
| `wifi` | Wi-Fi mastrumado |
| `bluhdento` | Bluetooth mastrumado |
| `usb` | USB aparatoj |
| `disko` | Diskaj aparatoj |
| `particio` | Particia mastrumado |
| `rubo` | Rubujo mastrumado |
| `sxelo-aliaso` | Bash aliazaj mastrumado |

### Sistemaj Informoj

 ```bash
 A sistemo info      # Montri sistemajn informojn
 ```

### Wi-Fi

 ```bash
 A sistemo wifi ls           # Listigi Wi-Fi retojn
 A sistemo wifi konekti SSID  # Konekti al reto
 ```

### Bluetooth

 ```bash
 A sistemo bluhdento ls        # Listigi Bluetooth aparatojn
 ```

### USB

 ```bash
 A sistemo usb ls           # Listigi USB aparatojn
 ```

### Diskoj

 ```bash
 A sistemo disko ls        # Listigi diskajn aparatojn
 ```

### Particioj

 ```bash
 A sistemo particio ls      # Listigi particiojn
 ```

### Rubujo

 ```bash
 A sistemo rubo ls          # Listigi rubujon
 A sistemo ruboelton       # Vacui rubujon
 ```

### Bash Aliazoj

 ```bash
 A sistemo sxelo-aliaso ls        # Listigi aliazon
 ```

---

## Arkitekturo

A-sistemo havas duoblajn tavolojn:

 ```
 CLI Layer (Typer)
 Service Layer
 ```

---

## Dependecoj

A-sistemo dependas de A-core.

---

## Licenco

GPL-3.0-only