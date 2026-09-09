# Windows'ta çalıştırma

PowerShell 5.1 (Windows'la gelen sürüm) üç yerde bash'ten ayrılıyor ve
üçü de bu projenin komutlarını kırıyor.

| Bash | PowerShell 5.1 |
|---|---|
| `a && b` | `a; b` ya da ayrı satırlar |
| satır sonu `\` | satır sonu ` (ters tırnak) ya da tek satır |
| `export X=1` | `$env:X = "1"` |

`&&` PowerShell 7'de çalışıyor, 5.1'de çalışmıyor. Hangi sürümde
olduğunu `$PSVersionTable.PSVersion` söyler.

## Kurulum

conda kuruluysa ayrı bir ortam en temizi. base'i kirletmez ve
`rasterio` gibi paketleri conda-forge'dan alır, ki Windows'ta pip'ten
kurmaktan daha güvenilir.

```powershell
cd C:\Users\yavuz\git\yerkon
git pull

conda create -n yerkon python=3.11 -y
conda activate yerkon
conda install -c conda-forge rasterio requests numpy -y
pip install -e ".[dev]"
```

conda kullanmak istemiyorsan venv de olur, ama `rasterio` Windows'ta
pip'ten kurulurken derleyici isteyebilir:

```powershell
cd C:\Users\yavuz\git\yerkon
git pull

python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev,sites]"
```

`Activate.ps1` "running scripts is disabled" derse, bir kereliğine:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

## Çalıştığını doğrulama

```powershell
pytest -q
```

## Saha verisi indirme

Tek satır. PowerShell'de satır bölmek istersen sonuna ters tırnak koy,
ters bölü değil.

```powershell
yerkon fetch --south 39.85 --west 32.70 --north 39.98 --east 33.05 --into sites/ankara-o20 --spacing 30
```

Bölmek istersen:

```powershell
yerkon fetch --south 39.85 --west 32.70 `
             --north 39.98 --east 33.05 `
             --into sites/ankara-o20 --spacing 30
```

`yerkon` komutu bulunamıyorsa ortam etkin değildir ya da
`pip install -e` çalışmamıştır. Ortamı etkinleştirmeden de çalışır:

```powershell
python -m yerkon.cli fetch --south 39.85 --west 32.70 --north 39.98 --east 33.05 --into sites/ankara-o20
```

Elle bir şey indirmen gerekmiyor. Komut yüksekliği Copernicus 30 m
karolarından kendi çekiyor: anahtar istemiyor, hız sınırı yok, bir
derecelik kare tek dosyada geliyor. Karolar `sites\_tiles` altında
saklanıyor, aynı karedeki ikinci saha bedava.

Zaten indirilmiş bir rasterin varsa onu öne koyabilirsin. Ağ hiç
gerekmez:

```powershell
yerkon fetch --south 39.85 --west 32.70 --north 39.98 --east 33.05 --into sites/ankara-o20 --geotiff C:\Users\yavuz\Downloads\N39E032.tif
```

Karo önbelleğini başka yere koymak istersen `--tile-cache`, Copernicus'u
tamamen atlamak istersen `--no-copernicus` var. `--no-copernicus`
sorgu servisine düşürür; o servis günde bin çağrıyla sınırlı, 30 m
aralıkla Ankara boyunda bir kutu 4791 çağrı eder ve komut bunu baştan
reddeder.

## MATLAB

`matlab/` altındaki betikler MATLAB'ın kendi komut penceresinde çalışır,
PowerShell'de değil. PowerShell'den çalıştırmak istersen:

```powershell
matlab -batch "cd('C:\Users\yavuz\git\yerkon\matlab'); yerkon_ranging_sim"
```
