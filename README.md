# Pardus ETAP 23 Spoof & MEB Integration Utility (`etap-spoof`)

[![Organization](https://img.shields.io/badge/Org-uhcal--oss-blue.svg)](https://github.com/uhcal-oss)
[![License](https://img.shields.io/badge/License-GPLv3-green.svg)](LICENSE)
[![Target](https://img.shields.io/badge/Target-Pardus%20ETAP%2023-red.svg)](https://etap.org.tr)
[![Platform](https://img.shields.io/badge/Tested%20On-Fedora%2044%20x86__64-orange.svg)](https://fedoraproject.org)

Modern Linux dağıtımları (Fedora, Arch vb.) kurulu MEB Etkileşimli Tahtalarını (Faz 1, Faz 2) merkezi MEB sistemleri ve **Lider Ahenk** ile sorunsuz uyumlu hale getirmek için geliştirilmiş resmi kimlik taklit ve doğrulama aracı.

---

## 📌 Özellikler (Features)

- **Otantik Pardus ETAP 23 Kimliği**:
  - `/etc/os-release` (`Pardus ETAP GNU/Linux 23 (yirmiuc)`)
  - `/etc/issue` & `/etc/issue.net` (`Pardus GNU/Linux 23`)
  - `/etc/lsb-release` (`DISTRIB_ID=Pardus`, `DISTRIB_RELEASE=23.4`, `DISTRIB_CODENAME=yirmiuc`)
  - `/etc/debian_version` (`12.4`) & `/etc/pardus-release` (`Pardus 23.4 (yirmiuc)`)
- **Evrensel LSB Release Shim (`lsb_release`)**:
  - Python `distro`, `ahenk` ve sistem tarama araçlarının LSB sorgularında (`lsb_release -a`) tam uyumlu Pardus yanıtı vermesini sağlar.
- **Güvenli Paket Yöneticisi Koruması (DNF Protection)**:
  - `/etc/dnf/vars/releasever` dosyasını `44` olarak sabitleyerek Fedora'nın DNF/DNF5 paket yöneticisinin `/etc/os-release` kaynaklı bozulmasını tamamen önler.
- **Canlı MEB EBA ETAP Entegrasyonu**:
  - Cihazın birincil ağ arayüzü MAC adresi üzerinden MEB EBA merkezi veritabanı (`api-etap.eba.gov.tr:1000`) ile anlık kayıt durumunu sorgular (Okul adı, kurum kodu, oda/ünite, tahta ID vb.).
- **Tek Tuşla Geri Alma (Revert)**:
  - Orijinal dağıtım dosyalarına veya Fedora sistem ayarlarına tek komutla temiz geri dönüş.

---

## 🚀 Kurulum (Installation)

```bash
git clone https://github.com/uhcal-oss/pardus-etap-spoof.git
cd pardus-etap-spoof
sudo ./install.sh
```

---

## 🛠️ Kullanım (Usage)

### 1. Pardus ETAP 23 Kimliğini Etkinleştirme
```bash
sudo etap-spoof enable
```
*Sistemi anında Pardus ETAP 23 olarak tanımlar, DNF korumasını aktif eder ve orijinal dosyaları `/var/lib/pardus-etap-spoof/backups/` altına yedekler.*

### 2. Durum ve MEB Kaydını Görüntüleme
```bash
etap-spoof status
```
Örnek Çıktı:
```
=== Pardus ETAP Spoofing Status ===
Status: ACTIVE (Pardus ETAP 23)

--- Python Distro Telemetry ---
  distro.id():           pardus
  distro.name():         Pardus ETAP GNU/Linux
  distro.version():      23.4
  distro.codename():     etap-yirmiuc
  distro.lsb_release:    {'distributor_id': 'Pardus', 'description': 'Pardus ETAP 23.4 (yirmiuc)', 'release': '23.4', 'codename': 'yirmiuc'}

--- Smart Board Hardware Info ---
  Vendor:                VESTEL
  Product Name:          14MB24A
  Board Name:            14MB24A
  Primary MAC:           00:09:df:82:fe:f5

--- MEB EBA ETAP Central Verification ---
  Registration Status:   REGISTERED WITH MEB
  School Name:           Urla Hakan Çeken Anadolu Lisesi (Code: 964416)
  Location:              İZMİR / URLA
  Unit / Room:           YazilimOdasi
  Phase:                 Vestel Faz1
  Board ID:              419234
```

### 3. MEB EBA API Doğrudan JSON Sorgusu
```bash
etap-spoof meb-check
```

### 4. Orijinal Dağıtıma Geri Dönme
```bash
sudo etap-spoof disable
```
*Tüm ETAP kimlik dosyalarını temizler ve Fedora orijinal sembolik linklerini geri yükler.*

---

## 🔍 Lider Ahenk ve MEB ETAP Mimarisi

1. **Donanım Doğrulaması**:
   - Vestel Faz 1 tahtaları DMI seviyesinde `VESTEL 14MB24A` anakartı taşır.
   - Dokunmatik ekran `IRTOUCHSYSTEMS 6615:0c20` USB kimliğiyle çalışır ve MEB'in resmi `devices.json` izinli donanım listesindedir.
2. **Merkezi MEB EBA Kaydı**:
   - `http://api-etap.eba.gov.tr:1000/api/board/check?mac=<MAC>` uç noktasıyla cihazın okuluna ait tahta envanter kaydı kontrol edilir.
3. **Lider Ahenk İstemcisi (`ahenk`)**:
   - Lider Ahenk istemcisi Python ile geliştirilmiş bir arka plan servisidir (`ahenkd.py`).
   - Sistem açıldığında Python `distro` ve `lsb_release` üzerinden işletim sistemi telemetrisini okuyarak Lider sunucusuna XMPP (5222 portu) protokolüyle iletir.
   - `etap-spoof`, `ahenk` ve Lider'in beklediği tüm parametreleri (`os.distributionName: Pardus ETAP GNU/Linux`, `os.distributionVersion: 23.4`, `os.version: Pardus ETAP 23.4 (yirmiuc)-23.4`) eksiksiz sağlar.

---

## 📄 Lisans

Bu proje GNU General Public License v3.0 (GPLv3) ile lisanslanmıştır.  
Urla Hakan Çeken Anadolu Lisesi Açık Kaynak Topluluğu ([@uhcal-oss](https://github.com/uhcal-oss)) tarafından geliştirilmiştir.
