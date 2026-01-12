AI-POWERED NETWORK FIREWALL - PROJECTDOCUMENT

Teamleden: Grigor Mkrttsjan & Nick Duschek

================================================================================
DEEL 1: PROJECTVOORSTEL
================================================================================

1. Management Samenvatting
Dit project ontwikkelt een AI-Firewall: een slimme netwerkbeveiliging die traditionele detectie combineert met Machine Learning. Het systeem stopt zowel bekende aanvallen als nieuwe, onbekende bedreigingen. Het is specifiek ontworpen om (draadloze) netwerken te beveiligen en dient als een betaalbare Plug & Play oplossing voor MKB en thuisgebruikers.

2. Probleemstelling
Draadloze netwerken zijn inherent kwetsbaar omdat het signaal buiten de fysieke muren treedt. Dit maakt Wi-Fi netwerken vatbaar voor specifieke aanvallen:

- Rogue Access Points: Kwaadaardige access points die zich voordoen als legitieme netwerken
- Deauthentication Attacks: Aanvallers sturen disconnect-paketten om clients af te koppelen
- Evil Twin Attacks: Nabootsen van bestaande SSIDs om credentials te stelen
- KRACK (Key Reinstallation Attacks): Exploits tegen WPA2 encryptie
- Wardriving: Scannen naar kwetsbare draadloze netwerken

Huidige firewalls missen nieuwe aanvallen op Wi-Fi en IoT-apparaten omdat ze alleen op vaste regels werken. Daarnaast zijn geavanceerde wireless security systemen vaak te duur en te complex voor MKB.

3. De Oplossing
We bouwen een hybride systeem met twee beschermingslagen dat al het verkeer van en naar het draadloze toegangspunt (Wireless Access Point) filtert:

- Laag 1: Suricata (IDS). Dit vangt direct alle bekende aanvallen en malware af op basis van wereldwijde databases, inclusief specifieke wireless signatures.
- Laag 2: Machine Learning Engine. Dit analyseert gedrag en herkent nieuwe aanvallen (zoals DDoS, Botnets, wireless deauth floods en specifieke 802.11 exploits) die nog niet in databases staan.

Het systeem wordt fysiek geplaatst tussen de Wireless Access Point en de internet router, waardoor ALLE draadloze clients automatisch beschermd worden zonder software-installatie.

4. Technische Architectuur
Het systeem is modulair opgebouwd met Docker containers:

- Network Bridge (Layer 2): Het systeem fungeert als een transparante Ethernet bridge tussen het Wireless Access Point en de router. Dit werkt op OSI Layer 2, waardoor IP-adressen en MAC-adressen van wireless clients ongewijzigd blijven.
- Wireless Compatibility: Werkt met elk 802.11 access point (a/b/g/n/ac/ax) ongeacht fabrikant. Geen speciale access point vereist.
- Technologie: We gebruiken Python voor de AI, Redis voor snelheid en een web-dashboard voor inzicht.
- Hardware: Het draait efficiënt op een Raspberry Pi 4 (met USB Gigabit Ethernet adapter voor tweede poort) of in een Virtuele Machine.

Netwerk Topologie:
[Internet] -> [Router] -> [AI-Firewall RPi] -> [Wireless Access Point] -> [Wi-Fi Clients]

5. Unieke Kenmerken
- Wireless Security: Beveiligt alle apparaten op het Wi-Fi netwerk (smartphones, laptops, IoT devices, smart home apparaten) zonder software op de clients te installeren.
- Protocol Agnostisch: Werkt met WPA2, WPA3, en zelfs open netwerken. De beveiliging zit in de verkeer-analyse, niet in de encryptie.
- IoT Bescherming: Detecteert gecompromitteerde IoT apparaten (cameras, thermostaten, smart speakers) die vaak geen eigen firewall hebben.
- Eenvoud: Ontworpen om zonder configuratie te werken (Plug & Play).
- Inzicht: Een dashboard toont live wat er in het draadloze netwerk gebeurt.
- Privacy: Alle analyse gebeurt lokaal op het apparaat, er gaat geen data naar de cloud.

6. Taakverdeling
- Grigor: Machine Learning (onderzoek, algoritme selectie, model training)
- Nick: Software Development (Suricata integratie, Dashboard, Linux/Raspberry Pi deployment)

7. Conclusie
De AI-Firewall maakt professionele beveiliging toegankelijk. Door slimme software te combineren met goedkope hardware, bieden we een krachtig antwoord op moderne cyberdreigingen.

================================================================================
DEEL 2: LOGBOEK
================================================================================

WEEK 1 (23 november - 30 november 2025)

Grigor - Machine Learning Research & Development:

1. Onderzoek ML Algoritmes voor Network Intrusion Detection
   Uitgebreid literatuuronderzoek gedaan naar machine learning methodes die geschikt zijn voor het detecteren van kwaadaardig netwerkverkeer. Hierbij is gekeken naar zowel supervised als unsupervised learning technieken.

2. Algoritme Selectie
   Na vergelijking van verschillende opties zijn twee complementaire algoritmes gekozen:

   a) XGBoost (Extreme Gradient Boosting)
      - Type: Supervised learning, gradient boosting ensemble
      - Waarom gekozen: Zeer hoge accuracy (>99%) op benchmark datasets voor network intrusion detection. Kan omgaan met ongebalanceerde datasets (veel normaal verkeer, weinig aanvallen). Snelle inference tijd, geschikt voor real-time classificatie.
      - Toepassing: Classificeert netwerkstromen als "Benign" of "Malicious" op basis van 79 features (packet sizes, flow duration, protocol flags, etc.).

   b) Isolation Forest
      - Type: Unsupervised learning, anomaly detection
      - Waarom gekozen: Detecteert afwijkingen zonder gelabelde data nodig te hebben. Ideaal voor zero-day attacks die niet in training data voorkomen. Lage computational overhead.
      - Toepassing: Berekent een "anomaly score" voor elke netwerkstroom. Hoge scores duiden op verdacht gedrag.

3. Training Dataset Identificatie
   De CIC-IDS2017 dataset van het Canadian Institute for Cybersecurity is geselecteerd als primaire trainingsbron. Deze dataset bevat:
   - 2.8 miljoen gelabelde netwerkstromen
   - 79 geëxtraheerde features per stroom
   - Diverse aanvalstypen: DDoS, PortScan, Brute Force SSH/FTP, Web Attacks, Infiltration, Botnet
   - Realistische verhouding benign/malicious verkeer
   
   Relevantie voor Wireless Networks:
   De dataset bevat verkeer dat representatief is voor typische wireless omgevingen, inclusief:
   - IoT device communicatie patronen
   - Mobile app traffic (HTTP/HTTPS)
   - Streaming verkeer (video/audio)
   - Botnet command & control traffic (vaak via gecompromitteerde IoT devices)

4. Python Scripts Ontwikkeling
   Gestart met het ontwikkelen van de training pipeline:
   - data_loading.py: Script voor het inladen en preprocessen van de CIC-IDS2017 CSV bestanden
   - train_model.py: Training script met hyperparameter configuratie voor XGBoost en Isolation Forest
   - inference.py: Real-time prediction module die beide modellen combineert tot een ensemble score

Nick - Software Development & Infrastructure:

1. Docker Architectuur
   Complete containerized stack opgezet met Docker Compose:
   - Suricata container: IDS met real-time packet inspection
   - AI-Engine container: Python applicatie met ML modellen
   - API container: FastAPI server voor REST endpoints en WebSocket streaming
   - Dashboard container: Nginx met statische HTML/JS frontend
   - Redis container: In-memory cache en message broker

2. Suricata IDS Integratie
   Suricata geconfigureerd als eerste detectielaag:
   - Emerging Threats ruleset geïmplementeerd (40.000+ signatures)
   - EVE JSON logging ingeschakeld voor machine-readable alerts
   - Network bridge mode voor transparante filtering van wireless traffic
   - Specifieke rules voor IoT malware (Mirai, Hajime, BrickerBot)
   - Detectie van wireless-specifieke aanvallen op applicatieniveau

3. Web Dashboard Development
   Real-time monitoring interface gebouwd:
   - Live traffic flow visualisatie met Chart.js
   - Blocked IPs overzicht met timestamp en reden
   - Attack type distributie (pie chart)
   - WebSocket connectie voor instant updates

4. Linux Deployment Automation
   Installatiescript (install.sh) ontwikkeld voor headless deployment:
   - Automatische Docker installatie
   - Netplan bridge configuratie voor Raspberry Pi / Ubuntu
   - Systemd service voor auto-start bij boot
   - DNS fix voor Docker build issues in VM omgevingen

5. Raspberry Pi 4 Optimalisatie
   Specifieke configuratie voor resource-constrained omgeving:
   - Memory limits per container
   - Redis zonder persistence (SD-card wear prevention)
   - Lightweight Nginx Alpine image
   - 2 Uvicorn workers ipv standaard 4

6. Wireless Network Integration
   Configuratie voor plaatsing in draadloos netwerk:
   - USB 3.0 Gigabit Ethernet adapter als tweede netwerkpoort
   - Linux bridge (br0) voor Layer 2 transparante filtering
   - Promiscuous mode voor volledige packet capture
   - Geen DHCP server conflict met bestaande router
   - Latency optimalisatie: <5ms toegevoegde vertraging per packet

================================================================================
DEEL 3: PLANNING
================================================================================

GLOBALE PROJECTPLANNING

Week 1 (Voltooid): Onderzoek & Basis Setup
Week 2: ML Model Training & Dashboard Uitbreiding
Week 3: Integratie & Testing
Week 4: Optimalisatie & Documentatie
Week 5: Eindpresentatie & Oplevering

PLANNING KOMENDE WEEK (Week 2: 1-7 december 2025)

Grigor:
- ML modellen trainen op de CIC-IDS2017 dataset.
- Hyperparameter tuning voor optimale detectie accuracy.
- Eerste tests met real-time classificatie van netwerkstromen.

Nick:
- Redis Pub/Sub implementeren voor real-time data streaming naar dashboard.
- Dashboard uitbreiden met grafieken voor attack types en blocked IPs.
- Testen van de volledige stack op een Raspberry Pi 4.

================================================================================

WEEK 2 (1 december - 7 december 2025)

Grigor - Machine Learning Training & Evaluatie:

1. Model Training Uitgevoerd
   Beide ML modellen succesvol getraind op de CIC-IDS2017 dataset:
   
   a) XGBoost Classifier
      - Training tijd: ~15 minuten op volledige dataset
      - Hyperparameters: max_depth=10, n_estimators=100, learning_rate=0.1
      - Train/Test split: 80/20
   
   b) Isolation Forest
      - Training tijd: ~5 minuten
      - Hyperparameters: n_estimators=100, contamination=0.1
      - Geen labels nodig (unsupervised)

2. Model Evaluatie & Resultaten
   De getrainde modellen zijn geëvalueerd op de test dataset. Hieronder de resultaten:
   
   [AFBEELDING: confusion_matrices.png]
   Confusion Matrix analyse:
   - XGBoost: Zeer hoge true positive rate voor malicious traffic
   - Isolation Forest: Goede anomaly detectie met acceptabele false positive rate
   
   [AFBEELDING: roc_curves.png]
   ROC Curves:
   - XGBoost AUC: 0.99+ (uitstekend)
   - Ensemble score combineert beide modellen voor robuustere detectie
   
   [AFBEELDING: precision_recall_curves.png]
   Precision-Recall Curves:
   - Hoge precision belangrijk om false positives te minimaliseren
   - Recall >95% voor de meeste attack types

3. Feature Analysis
   Onderzoek naar welke netwerkfeatures het meest bijdragen aan detectie:
   
   [AFBEELDING: feature_importance.png]
   Top 5 belangrijkste features:
   1. Flow Duration - Langere flows vaak verdacht
   2. Packet Length Mean - Afwijkende packet sizes
   3. Flow Bytes/s - Bandwidth anomalieën (DDoS indicator)
   4. Fwd Packets/s - Forward packet rate
   5. Destination Port - Bepaalde poorten correleren met aanvallen
   
   [AFBEELDING: feature_correlations.png]
   Feature correlaties tonen clusters van gerelateerde metrics

4. Anomaly Score Distributie
   
   [AFBEELDING: anomaly_score_distribution.png]
   - Benign traffic: Lage anomaly scores (0.0 - 0.3)
   - Malicious traffic: Hoge anomaly scores (0.7 - 1.0)
   - Duidelijke scheiding maakt threshold-based blocking mogelijk
   
   [AFBEELDING: score_distribution.png]
   Ensemble score distributie over alle test samples

5. Attack Type Classificatie
   Model getest op specifieke aanvalstypen uit de dataset:
   - DDoS: 99.8% detectie rate
   - PortScan: 99.5% detectie rate
   - Brute Force: 98.2% detectie rate
   - Web Attacks: 97.1% detectie rate
   - Botnet: 99.9% detectie rate
   - Infiltration: 94.3% detectie rate

Nick - Software Development & Testing:

1. Dashboard Afgerond
   Het real-time monitoring dashboard is volledig afgewerkt:
   - Live traffic flow visualisatie met Chart.js
   - Blocked IPs overzicht met timestamp en reden
   - Attack type distributie (pie chart)
   - WebSocket connectie voor instant updates
   - Dark mode theme
   - Export functie voor logs (CSV)

2. Software Stack Compleet
   Alle benodigde software componenten zijn afgewerkt en klaar voor integratie:
   - Docker Compose configuratie voor alle containers
   - FastAPI backend met REST endpoints
   - Redis Pub/Sub voor real-time communicatie
   - Suricata IDS configuratie met custom rules
   - Nginx reverse proxy setup
   - Systemd service voor auto-start

3. Installatie Automatisering
   Het install.sh script is volledig functioneel:
   - One-click deployment op Ubuntu/Debian systemen
   - Automatische network bridge configuratie
   - Docker en dependencies installatie
   - Service registratie voor boot persistence

4. Volgende Stap: Integratie
   De software kant is klaar. De volgende stap is het integreren van Grigor's getrainde ML modellen in de software stack. Hiervoor moet:
   - De inference.py module gekoppeld worden aan de API server
   - De model files (.pkl/.joblib) in de juiste container gemount worden
   - De ensemble scoring getest worden met live traffic
   - Fine-tuning van thresholds op basis van real-world performance

================================================================================

PLANNING KOMENDE WEEK (Week 3: 8-14 december 2025)

Grigor:
- Model files exporteren in productie-ready formaat
- Inference snelheid optimaliseren voor real-time gebruik
- Threshold tuning voor optimale precision/recall balans

Nick:
- ML modellen integreren in de Docker containers
- End-to-end testing van de volledige pipeline
- Performance testing op Raspberry Pi 4 hardware

Gezamenlijk:
- Live testing met gesimuleerde aanvallen
- Fine-tuning van de software-model integratie
- Documentatie bijwerken

================================================================================
